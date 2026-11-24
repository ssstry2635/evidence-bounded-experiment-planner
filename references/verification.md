# Arithmetic, search and schedule interface

The Agent extracts the scientific model from actual evidence. The helper checks the declared arithmetic, not semantic completeness or units. All numbers are converted from JSON decimal literals or decimal strings into Decimal. The CLI uses 50 significant digits; nonterminating division is rounded at that precision, not exact rational arithmetic. Output numeric quantities are decimal strings to retain calculated precision; adapt to original contract numeric types after checking precision. Set every expression in a single consistent unit system and document conversions. Python 3.10+, standard library, no network or third-party packages.

## `solve model.json --out DIRECTORY`

Input keys: `case_id`, `sources` (nonempty mappings `{id, locator}`), `constants` (name to number), `derived` (ordered `{name, expr, evidence:[source IDs]}`), `constraints` (nonempty `{id,lhs,op,rhs,evidence}`), `objectives` (ordered `{expr,direction: min|max,evidence}`), `candidates` (nonempty `{id,version,domains:{name:[numeric values]},evidence}`), optional `max_points` (default 100000, hard limit 1000000). Domains and constants must be numeric, finite and nonempty; encode categorical options as documented numeric codes only when appropriate. Do not use NaN, Infinity, booleans or implicit wildcard ranges. IDs must be unique. Each candidate's domains must expose the same variable names. Candidate domains may be singletons for as-written audits, or the actual allowed revision set for search. Run these two modes separately to avoid conflating an original candidate with an optimized revision.

Expressions allow names, decimal constants, `+ - * /`, unary signs, and `ceil`, `floor`, `abs`, `min`, `max`. No eval, attributes, imports, indexing or exponentiation. Define derived names before using them. Each expression is limited to 256 AST nodes; nonfinite arithmetic and magnitudes over 1e100 fail. Relations are `<=`, `<`, `>=`, `>`, `==`, `!=`; there is no hidden tolerance or fuzzy equality. Express any scientifically justified tolerance explicitly. A source reference is checked for existence in the model, not for truth in the original document. Evidence mapping still needs human/Agent inspection.

Every grid point is evaluated against every hard constraint. `evaluations.csv` retains parameters, derived quantities, objective values, feasibility and failed constraint IDs. `report.json` reports enumerated/feasible counts, each candidate's lexicographic optimum, objective directions, number of ties, violation counts and search completeness. Lexicographic priority is used only because the declared objectives specify that priority; for weighted or Pareto selection implement and retain the actual project-defined rule separately. Equality to the best objective is a tie; retain the count and the deterministic first point without implying scientific uniqueness. Global best is conditional on these domains and this declared model. If all points fail, that proves infeasibility only within the enumerated domain and complete declared constraints. Non-monotonic behavior is handled by enumeration, not an assumed gradient.

Before using a result, recompute a chosen point directly from primitives. Check a bound, unit conversion, an integer ceiling discontinuity, zero-purchase stock case, control counts, time/resource overlap and a deliberately infeasible input. Do not add regression comparisons against invented scientific truths. For a large search or uncertain constants, explicitly declare the remaining uncertainty instead of reporting an exact global optimum.

## `compare model.json --out DIRECTORY`

Use the same model as `solve` and add a `baseline` mapping to every candidate. Its keys must match that candidate's domain variables. Supply the original values even if they lie outside allowed domains. Optional constraint `unit` labels appear alongside the actual operands, relation, signed margin and evidence IDs in the report. A zero margin can fail a strict inequality or a not-equal constraint, so use the returned `passed` flag.

The report adds `as_written`, `changes`, `derived_changes` and, for infeasible candidates, `infeasibility_witness`. Revisions minimize the number of changed parameters per candidate before applying the declared objectives. The top-level best compares the resulting per-candidate revisions by those objectives. Ties use the first enumerated point and retain counts. Use `solve` if the project requires optimizing objectives ahead of change count, or retain all feasible points from the CSV if another selection rule is required.

An infeasibility witness is a concrete tested point with the fewest failed constraints, breaking ties by changed field count then enumeration order. It illustrates the conflicts. The enumerated counts establish feasibility only over the supplied domains and constraints. Undefined baseline arithmetic is recorded and can coexist with valid revised points. Undefined arithmetic inside the allowed search space aborts the run, since complete verification then requires a corrected domain or model.

## `schedule schedule.json --out FILE`

Input keys: `case_id`, `time_unit` (nonempty), `resources` mapping resource ID to `{capacity, windows:[[start,end],...]}`, `steps` list of `{id,start,end,after:[],demands:{resource_id:quantity}}`, optional `deadline`. All times use the named unit relative to a specified origin in the case report; all intervals are half-open `[start,end)`. Capacities and demands are positive integers. A step's duration must be positive. Each use must fit inside a single resource availability window. Split multi-stage operations when capacities change. Use separate steps for setup and cleanup if these occupy a resource. An empty `windows` list represents unavailable equipment. Represent maintenance by splitting availability windows, rather than accepting an overlap with a blackout.

The audit checks unique IDs, actual references, nonnegative starts, positive durations, dependency completion, resource existence, integer capacities, booking coverage, capacity via every event interval and optional deadline. It reports actual makespan, violations and deterministic validity. An invalid/unknown dependency or resource is an invalid model, not a silently dropped condition. It audits the submitted schedule; it does NOT search all schedules or prove that no feasible schedule exists. A failing schedule can often be repaired. To claim schedule infeasibility, supply an independent lower bound/conflict witness or a complete exact search. Calendar/time-zone conversion and variable duration formulas belong in the normalized source mapping, not in this helper.

## Input example

`examples/model.json` is a tiny, explicitly hypothetical interface example with three candidate versions. Its numbers illustrate the interface and are not laboratory specifications or research observations. Run:

```bash
python scripts/verify_plan.py solve examples/model.json --out work/interface-example
```

The generated report demonstrates engineering arithmetic. It does not establish scientific quality, experimental performance or a real research conclusion.
