#!/usr/bin/env python3
"""Evidence-referenced finite arithmetic and schedule audit; Python 3.10+."""
import argparse
import ast
import csv
import itertools
import json
import math
import operator
import re
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, localcontext
from pathlib import Path

VERSION = '1.0.0'
NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
FUNCTIONS = {'ceil', 'floor', 'abs', 'min', 'max'}
RELATIONS = {'<=': operator.le, '<': operator.lt, '>=': operator.ge,
             '>': operator.gt, '==': operator.eq, '!=': operator.ne}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    require(not isinstance(value, bool) and isinstance(value, (int, float, Decimal, str)),
            'Expected a finite numeric quantity')
    value = Decimal(str(value))
    require(value.is_finite() and abs(value) <= Decimal('1e100'), 'Nonfinite or excessive quantity')
    return value


def integer(value, label, minimum=1):
    value = number(value)
    require(value == value.to_integral_value() and value >= minimum, f'{label}: invalid integer')
    return int(value)


def load(path):
    def reject(value):
        raise ValueError('Invalid JSON numeric constant: ' + value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_float=Decimal,
                      parse_constant=reject)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               default=lambda x: str(x) if isinstance(x, Decimal) else _unsupported(x),
                               allow_nan=False) + '\n', encoding='utf-8')


def _unsupported(value):
    raise TypeError(type(value).__name__)


def identifier(value):
    require(isinstance(value, str) and NAME.fullmatch(value) and value not in FUNCTIONS,
            f'Invalid or reserved variable name: {value}')
    return value


def expression(text, context):
    require(isinstance(text, str) and 0 < len(text) <= 4096, 'Invalid expression length')
    tree = ast.parse(text, mode='eval')
    require(sum(1 for _ in ast.walk(tree)) <= 256, 'Expression too complex')

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return number(ast.get_source_segment(text, node))
        if isinstance(node, ast.Name):
            require(node.id in context, f'Unknown variable: {node.id}')
            return context[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            ops = {ast.Add: operator.add, ast.Sub: operator.sub,
                   ast.Mult: operator.mul, ast.Div: operator.truediv}
            require(type(node.op) in ops, 'Unsupported arithmetic operator')
            return number(ops[type(node.op)](visit(node.left), visit(node.right)))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            require(node.func.id in FUNCTIONS and not node.keywords, 'Unsupported function')
            args = [visit(x) for x in node.args]
            if node.func.id in ('min', 'max'):
                require(len(args) >= 1, 'min/max require arguments')
                return (min if node.func.id == 'min' else max)(args)
            require(len(args) == 1, 'Unary function requires exactly one argument')
            if node.func.id == 'abs':
                return abs(args[0])
            return args[0].to_integral_value(rounding=ROUND_CEILING if node.func.id == 'ceil' else ROUND_FLOOR)
        raise ValueError('Unsupported expression syntax')

    return number(visit(tree.body))


def evidence(item, known):
    refs = item.get('evidence')
    require(isinstance(refs, list) and refs and all(isinstance(x, str) and x in known for x in refs),
            'Missing or unresolved evidence IDs')


def solve(model, out):
    require(isinstance(model.get('case_id'), str) and model['case_id'], 'case_id required')
    sources = model.get('sources', [])
    require(isinstance(sources, list) and sources, 'sources required')
    known = set()
    for source in sources:
        require(isinstance(source.get('id'), str) and source['id'] and source['id'] not in known,
                'Duplicate or missing source ID')
        require(isinstance(source.get('locator'), str) and source['locator'], 'Source locator required')
        known.add(source['id'])
    constants = {identifier(k): number(v) for k, v in model.get('constants', {}).items()}
    derived = model.get('derived', [])
    constraints = model.get('constraints', [])
    objectives = model.get('objectives', [])
    candidates = model.get('candidates', [])
    require(constraints and objectives and candidates, 'constraints, objectives and candidates required')
    require(len({x['id'] for x in constraints}) == len(constraints), 'Duplicate constraint ID')
    for item in derived + constraints + objectives + candidates:
        evidence(item, known)
    for c in constraints:
        require(isinstance(c['id'], str) and c['id'] and c['op'] in RELATIONS, 'Invalid constraint')
    for o in objectives:
        require(o['direction'] in ('min', 'max'), 'Invalid objective direction')
    seen, domain_names, total = set(), None, 0
    prepared = []
    for c in candidates:
        require(isinstance(c['id'], str) and c['id'] and c['id'] not in seen, 'Duplicate or missing candidate ID')
        require(isinstance(c.get('version'), str) and c['version'], 'Candidate version required')
        seen.add(c['id'])
        domains = c['domains']
        require(isinstance(domains, dict) and domains, 'Nonempty domains required')
        names = sorted(identifier(k) for k in domains)
        require(not (set(names) & constants.keys()), 'Domain shadows constant')
        if domain_names is None:
            domain_names = names
        require(names == domain_names, 'Candidate domain names differ')
        values = []
        for name in names:
            require(isinstance(domains[name], list) and domains[name], 'Empty or invalid domain')
            vals = [number(v) for v in domains[name]]
            require(len(set(vals)) == len(vals), 'Duplicate domain value')
            values.append(vals)
        total += math.prod(len(x) for x in values)
        prepared.append((c, names, values))
    limit = integer(model.get('max_points', 100000), 'max_points')
    require(limit <= 1000000 and total <= limit, f'Search limit exceeded: {total} points; no feasibility conclusion')
    derived_names = [identifier(x['name']) for x in derived]
    require(len(set(derived_names)) == len(derived_names), 'Duplicate derived name')
    require(not (set(derived_names) & (set(domain_names) | constants.keys())), 'Derived name shadows input')
    reserved = {'candidate_id', 'version', 'feasible', 'failed_constraints'} | {f'objective_{i+1}' for i in range(len(objectives))}
    require(not (reserved & (set(domain_names) | set(derived_names))), 'Variable shadows output column')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {'case_id': model['case_id'], 'verifier_version': VERSION,
              'scope': 'Declared numeric model only; source semantics and unit consistency require review',
              'status': 'completed', 'complete_enumeration': True, 'evaluated': total,
              'objectives': objectives, 'candidates': [], 'best': None, 'global_ties': 0}
    global_key = None
    fields = ['candidate_id', 'version'] + domain_names + derived_names + [f'objective_{i+1}' for i in range(len(objectives))] + ['feasible', 'failed_constraints']
    with (out / 'evaluations.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for candidate, names, values in prepared:
            failures = Counter()
            item = {'id': candidate['id'], 'version': candidate['version'], 'evaluated': 0,
                    'feasible_count': 0, 'best': None, 'ties': 0}
            best_key = None
            for point in itertools.product(*values):
                params = dict(zip(names, point))
                ctx = dict(constants, **params)
                for d in derived:
                    ctx[d['name']] = expression(d['expr'], ctx)
                checks = [{'id': c['id'], 'lhs': expression(c['lhs'], ctx),
                           'rhs': expression(c['rhs'], ctx), 'op': c['op']} for c in constraints]
                for check in checks:
                    check['passed'] = RELATIONS[check['op']](check['lhs'], check['rhs'])
                    check['signed_margin'] = (check['rhs'] - check['lhs'] if check['op'] in ('<=', '<')
                                              else check['lhs'] - check['rhs'] if check['op'] in ('>=', '>')
                                              else -abs(check['lhs'] - check['rhs']) if check['op'] == '=='
                                              else abs(check['lhs'] - check['rhs']))
                failed = [x['id'] for x in checks if not x['passed']]
                failures.update(failed)
                objective_values = [expression(o['expr'], ctx) for o in objectives]
                row = {'candidate_id': candidate['id'], 'version': candidate['version'],
                       **{k: ctx[k] for k in domain_names + derived_names},
                       **{f'objective_{i+1}': v for i, v in enumerate(objective_values)},
                       'feasible': not failed, 'failed_constraints': '|'.join(failed)}
                writer.writerow(row)
                item['evaluated'] += 1
                if failed:
                    continue
                item['feasible_count'] += 1
                key = tuple(v if o['direction'] == 'min' else -v for v, o in zip(objective_values, objectives))
                result = {'candidate_id': candidate['id'], 'version': candidate['version'],
                          'parameters': params, 'derived': {k: ctx[k] for k in derived_names},
                          'objectives': objective_values, 'constraint_checks': checks}
                if best_key is None or key < best_key:
                    best_key, item['best'], item['ties'] = key, result, 1
                elif key == best_key:
                    item['ties'] += 1
                if global_key is None or key < global_key:
                    global_key, report['best'], report['global_ties'] = key, result, 1
                elif key == global_key:
                    report['global_ties'] += 1
            item['violation_counts'] = dict(failures)
            item['status'] = 'feasible' if item['feasible_count'] else 'infeasible_in_declared_domain'
            report['candidates'].append(item)
    report['feasible_count'] = sum(x['feasible_count'] for x in report['candidates'])
    if report['best'] is None:
        report['status'] = 'infeasible_in_declared_domain'
    write(out / 'report.json', report)
    return report


def audit_schedule(model):
    require(isinstance(model.get('case_id'), str) and model['case_id'], 'case_id required')
    require(isinstance(model.get('time_unit'), str) and model['time_unit'], 'time_unit required')
    resources = model['resources']
    require(isinstance(resources, dict), 'resources must be a mapping')
    for rid, r in resources.items():
        require(isinstance(rid, str) and rid, 'Invalid resource ID')
        r['capacity'] = integer(r['capacity'], 'capacity')
        require(isinstance(r['windows'], list), 'windows must be a list')
        windows = []
        for w in r['windows']:
            require(len(w) == 2, 'Invalid booking window')
            a, b = map(number, w)
            require(0 <= a < b, 'Invalid booking interval')
            windows.append((a, b))
        r['windows'] = windows
    steps, ids = model['steps'], {}
    require(isinstance(steps, list) and steps, 'Nonempty steps required')
    for s in steps:
        require(isinstance(s['id'], str) and s['id'] and s['id'] not in ids, 'Duplicate/invalid step ID')
        s['start'], s['end'] = number(s['start']), number(s['end'])
        require(0 <= s['start'] < s['end'], 'Invalid step interval')
        require(isinstance(s.get('after', []), list), 'after must be a list')
        require(isinstance(s.get('demands', {}), dict), 'demands must be a mapping')
        for rid, demand in s.get('demands', {}).items():
            require(rid in resources, 'Unknown resource: ' + rid)
            s['demands'][rid] = integer(demand, 'demand')
        ids[s['id']] = s
    violations = []
    for s in steps:
        for dep in s.get('after', []):
            require(dep in ids and dep != s['id'], 'Unknown/self dependency')
            if ids[dep]['end'] > s['start']:
                violations.append({'type': 'dependency', 'step': s['id'], 'predecessor': dep})
        for rid in s.get('demands', {}):
            if not any(a <= s['start'] and s['end'] <= b for a, b in resources[rid]['windows']):
                violations.append({'type': 'booking', 'step': s['id'], 'resource': rid})
    for rid, r in resources.items():
        users = [s for s in steps if rid in s.get('demands', {})]
        events = sorted({t for s in users for t in (s['start'], s['end'])})
        for a, b in zip(events, events[1:]):
            active = [s for s in users if s['start'] <= a < s['end']]
            demand = sum(s['demands'][rid] for s in active)
            if demand > r['capacity']:
                violations.append({'type': 'capacity', 'resource': rid, 'start': a, 'end': b,
                                   'demand': demand, 'capacity': r['capacity'],
                                   'steps': [s['id'] for s in active]})
    makespan = max(s['end'] for s in steps)
    if 'deadline' in model:
        deadline = number(model['deadline'])
        require(deadline >= 0, 'Invalid deadline')
        if makespan > deadline:
            violations.append({'type': 'deadline', 'makespan': makespan, 'deadline': deadline})
    return {'case_id': model['case_id'], 'verifier_version': VERSION,
            'status': 'valid' if not violations else 'invalid', 'time_unit': model['time_unit'],
            'makespan': makespan, 'violations': violations,
            'scope': 'Audit of supplied schedule; no global schedule feasibility claim'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['solve', 'schedule'])
    parser.add_argument('input')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        with localcontext() as ctx:
            ctx.prec = 50
            model = load(args.input)
            if args.mode == 'solve':
                report = solve(model, args.out)
            else:
                report = audit_schedule(model)
                write(args.out, report)
        print(json.dumps({'case_id': report['case_id'], 'status': report['status'],
                          'out': str(args.out)}, ensure_ascii=False))
        return 0 if report['status'] in ('completed', 'valid') else 2
    except (ValueError, TypeError, KeyError, InvalidOperation, ArithmeticError, SyntaxError, OSError) as exc:
        path = Path(args.out) / 'report.json' if args.mode == 'solve' else Path(args.out)
        write(path, {'status': 'failed', 'complete_enumeration': False,
                     'error': str(exc), 'no_feasibility_conclusion': True})
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
