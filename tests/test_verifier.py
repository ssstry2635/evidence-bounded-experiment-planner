"""Regression checks for finite parameter search and resource scheduling."""
import copy
import importlib.util
import itertools
import json
import math
import random
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT
SCRIPT = SKILL_ROOT / 'scripts/verify_plan.py'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('verifier', SCRIPT)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class ArithmeticTests(unittest.TestCase):
    def setUp(self):
        self.model = v.load(SKILL_ROOT / 'examples/model.json')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)

    def test_compare_recalculates_baselines_and_prefers_one_field_change(self):
        report = v.solve(self.model, self.out, compare=True)
        a, b, c = report['candidates']
        self.assertEqual(a['infeasibility_witness']['constraint_checks'][0]['signed_margin'], -1)
        self.assertFalse(b['as_written']['feasible'])
        self.assertEqual(b['as_written']['derived']['duration'], 9)
        self.assertEqual(b['best']['parameters'], {'n': 3, 'dwell': 3})
        self.assertEqual(b['changes'], [
            {'parameter': 'n', 'before': 5, 'after': 3, 'domain_evidence': ['example']}
        ])
        self.assertEqual(b['best']['derived']['cost'], 120)
        self.assertEqual(b['best']['constraint_checks'][2]['unit'], 'hours')
        self.assertEqual(c['as_written']['derived']['duration'], 16)
        self.assertEqual(c['status'], 'infeasible_in_declared_domain')

    def test_compare_revises_out_of_domain_baseline_with_undefined_arithmetic(self):
        self.model['candidates'] = [self.model['candidates'][1]]
        self.model['candidates'][0]['baseline']['n'] = 0
        self.model['derived'].append({'name': 'ratio', 'expr': '1/n', 'evidence': ['example']})
        report = v.solve(self.model, self.out, compare=True)
        candidate = report['candidates'][0]
        self.assertEqual(candidate['as_written']['outside_allowed_domains'], ['n'])
        self.assertEqual(candidate['as_written']['evaluation_error'], 'DivisionByZero')
        self.assertFalse(candidate['as_written']['feasible'])
        self.assertEqual(candidate['best']['parameters']['n'], 3)
        self.assertIsNone(next(c for c in candidate['derived_changes'] if c['quantity'] == 'ratio')['before'])

    def test_example_counts_optimum_and_independent_accounting(self):
        r = v.solve(self.model, self.out)
        self.assertEqual(r['evaluated'], 8)
        self.assertEqual(r['feasible_count'], 5)
        self.assertEqual(r['best']['candidate_id'], 'B')
        self.assertEqual(r['best']['parameters'], {'dwell': Decimal(2), 'n': Decimal(3)})
        self.assertEqual(r['best']['derived']['cost'], Decimal(120))
        # Independent sample/stock/purchase identity for the selected point.
        n = int(r['best']['parameters']['n'])
        consumed = 4 * n
        bought = math.ceil(max(0, consumed - 5) / 10) * 10
        self.assertEqual(bought * 12, 120)
        self.assertGreaterEqual(bought + 5, consumed)
        self.assertEqual(r['candidates'][0]['violation_counts'], {'independent_replication': 1})
        self.assertEqual(r['candidates'][2]['violation_counts'], {'time': 1})

    def test_stock_and_pack_boundary(self):
        candidate = copy.deepcopy(self.model['candidates'][1])
        for stock, expected in [(12, 0), (11, 120), (2, 120), (1, 240)]:
            self.model['constants']['stock'] = stock
            self.model['candidates'] = [copy.deepcopy(candidate)]
            self.model['candidates'][0]['domains'] = {'n': [3], 'dwell': [2]}
            self.assertEqual(v.solve(self.model, self.out)['best']['derived']['cost'], expected)

    def test_random_finite_search_against_independent_integer_oracle(self):
        rng = random.Random(3917)
        for _ in range(35):
            stock, budget = rng.randrange(0, 18), rng.randrange(0, 500)
            m = copy.deepcopy(self.model)
            m['constants'].update(stock=stock, budget=budget)
            m['candidates'] = [m['candidates'][1]]
            m['candidates'][0]['domains'] = {'n': list(range(1, 10)), 'dwell': [1, 2, 3, 4]}
            valid = []
            for n, dwell in itertools.product(range(1, 10), [1, 2, 3, 4]):
                samples = 4 * n
                deficit = max(samples-stock, 0)
                packs = (deficit + 9) // 10
                cost = packs * 120
                duration = ((samples+7)//8) * dwell
                if n >= 3 and cost <= budget and duration <= 8:
                    valid.append((cost, duration))
            r = v.solve(m, self.out)
            self.assertEqual(r['evaluated'], 36)
            self.assertEqual(r['feasible_count'], len(valid))
            self.assertEqual(r['best'] is None, not valid)
            if valid:
                self.assertEqual(tuple(map(int, r['best']['objectives'])), min(valid))
                self.assertEqual(r['global_ties'], valid.count(min(valid)))

    def test_decimal_and_signed_expressions(self):
        self.assertEqual(v.expression('0.1 + 0.2', {}), Decimal('0.3'))
        self.assertEqual(v.expression('ceil(1.0000000000000001)', {}), 2)
        self.assertEqual(v.expression('floor(-1.1)', {}), -2)
        self.assertEqual(v.expression('1e-3 * 1000', {}), 1)

    def test_unsupported_code_is_rejected(self):
        for expr in ['__import__("os")', 'x.real', '(1).__class__', '[1][0]', '2**999', 'True', 'nan']:
            with self.subTest(expr=expr), self.assertRaises((ValueError, SyntaxError)):
                v.expression(expr, {})

    def test_unknown_source_empty_duplicate_domain_and_budget_guard(self):
        for mutate in [
            lambda m: m['constraints'][0].update(evidence=['missing']),
            lambda m: m['candidates'][0]['domains'].update(n=[]),
            lambda m: m['candidates'][0]['domains'].update(n=[2, 2]),
            lambda m: m.update(max_points=1),
            lambda m: m['candidates'][0]['domains'].update(n=[True]),
            lambda m: m['candidates'][0]['domains'].update(n=['NaN']),
        ]:
            m = copy.deepcopy(self.model)
            mutate(m)
            with self.assertRaises(ValueError):
                v.solve(m, self.out)

    def test_failure_overwrites_stale_report_and_cli_exit(self):
        v.solve(self.model, self.out)
        self.model['derived'][0]['expr'] = '1 / 0'
        p = self.out/'bad.json'
        v.write(p, self.model)
        process = subprocess.run([sys.executable, str(SCRIPT), 'solve', str(p), '--out', str(self.out)], capture_output=True)
        self.assertEqual(process.returncode, 1)
        r = json.loads((self.out/'report.json').read_text())
        self.assertEqual(r['status'], 'failed')
        self.assertFalse(r['complete_enumeration'])

    def test_all_infeasible_is_scoped(self):
        self.model['constants']['budget'] = 0
        r = v.solve(self.model, self.out)
        self.assertEqual(r['status'], 'infeasible_in_declared_domain')
        self.assertIsNone(r['best'])

    def test_maximize_and_ties(self):
        self.model['objectives'] = [{'expr': 'n', 'direction': 'max', 'evidence': ['example']}]
        r = v.solve(self.model, self.out)
        self.assertEqual(r['best']['parameters']['n'], 5)
        self.assertEqual(r['global_ties'], 1)  # n=5,dwell=3 exceeds time


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.model = {'case_id': 'hypothetical-schedule', 'time_unit': 'hour', 'deadline': 8,
                      'resources': {'oven': {'capacity': 1, 'windows': [[0, 8]]}},
                      'steps': [{'id': 'a', 'start': 0, 'end': 4, 'after': [], 'demands': {'oven': 1}},
                                {'id': 'b', 'start': 4, 'end': 8, 'after': ['a'], 'demands': {'oven': 1}}]}

    def test_touching_boundaries_are_valid(self):
        r = v.audit_schedule(self.model)
        self.assertEqual(r['status'], 'valid')
        self.assertEqual(r['makespan'], 8)

    def test_capacity_conflict_and_dependency(self):
        self.model['steps'][1]['start'] = 3
        r = v.audit_schedule(self.model)
        self.assertEqual({x['type'] for x in r['violations']}, {'capacity', 'dependency'})

    def test_booking_gap_and_deadline(self):
        self.model['resources']['oven']['windows'] = [[0, 3], [5, 8]]
        self.model['deadline'] = 7
        r = v.audit_schedule(self.model)
        self.assertEqual([x['type'] for x in r['violations']].count('booking'), 2)
        self.assertIn('deadline', [x['type'] for x in r['violations']])

    def test_parallel_capacity_two(self):
        self.model['resources']['oven']['capacity'] = 2
        self.model['steps'][1].update(start=0, end=4, after=[])
        self.assertEqual(v.audit_schedule(self.model)['status'], 'valid')

    def test_unknown_or_invalid_inputs(self):
        for mutate in [lambda m: m['steps'][0]['demands'].update(missing=1),
                       lambda m: m['steps'][0].update(after=['missing']),
                       lambda m: m['steps'][0].update(start=-1),
                       lambda m: m['resources']['oven'].update(capacity=1.5)]:
            m = copy.deepcopy(self.model)
            mutate(m)
            with self.assertRaises(ValueError):
                v.audit_schedule(m)

    def test_unavailable_equipment(self):
        self.model['resources']['oven']['windows'] = []
        self.assertEqual(len(v.audit_schedule(self.model)['violations']), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
