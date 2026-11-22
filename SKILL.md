---
name: evidence-bounded-experiment-planner
description: Generate, compare and revise experimental plans using actual scientific evidence, finite parameter domains and explicit resource constraints. Includes deterministic budget, procurement and schedule checks for auditable planning.
---

# EvidenceBound Planner

Version 1.0.0. Build a research plan whose scientific assumptions, resource needs and revisions can be inspected. The Agent performs the scientific reasoning; the bundled Python tools check the declared arithmetic and resource schedule.

## Establish the task

Read the caller's research brief, supplied sources, candidate plans and resource information. Identify the research question, requested output schema, parameter domains, hard thresholds, sample unit, budget, equipment capabilities and availability windows. Inventory the actual files before inferring their contents from labels. Keep input identifiers and version history.

Use the caller's input, working and output directories. For an unconfigured local workflow, use `data/`, `work/` and `output/`. Save a valid partial `result.json` early, including `case_id`, known required fields, honest status and missing prerequisites. Preserve the caller's output schema; use a supplementary file if it forbids additional fields. Choose a time and tool-call budget appropriate to the task, reserving time for final verification.

## Ground parameters in evidence

Read the relevant paper methods, supplements, instrument manuals, inventory and booking information. Inspect rendered source pages when text extraction loses tables, equations, units or image context. Record actual source paths, versions, page/section locators, short supporting quotations and extraction uncertainty.

Use [references/evidence-and-design.md](references/evidence-and-design.md) to create an evidence ledger. Distinguish reported facts, project-specific resource assumptions, calculations, proposed settings and items needing expert confirmation. A simulated price or booking remains a scenario input. A published experimental setting does not by itself establish a safe operating limit for another instrument.

## Design, compare and revise

Connect the hypothesis, operational variables, primary endpoint, relevant controls, equipment/materials, parameter ranges, time/cost estimates and failure responses. Identify independent replication separately from repeated readings. Define quality gates, missingness rules and decision criteria before results are observed.

Inspect every candidate and preserve its ID/version. Recalculate sample counts, material demand, purchase packs, cost and timing from primitives. Compare hard feasibility before soft preferences. A weighted preference cannot compensate for violating a hard constraint. Explain Pareto tradeoffs where priorities are underdetermined. If all declared candidates are infeasible, provide an explicit conflict witness instead of quietly lowering the research requirement.

Revise the selected source plan with a change log: original/revised version, field, before/after values, reason, evidence, downstream effects and remaining uncertainty. Retain unaffected choices where possible. Do not remove scientifically necessary controls to make a budget appear feasible. Do not optimize an invented scientific response or report proposed experiments as completed measurements.

## Run the deterministic checks

Read [references/verification.md](references/verification.md). From the repository root:

```bash
python scripts/verify_plan.py solve examples/model.json --out output/search
python scripts/verify_plan.py schedule examples/schedule.json --out output/schedule-audit.json
```

For real work, normalize the caller's actual quantities into this interface and retain the source-to-model mapping. Use a consistent unit system, ordered derived expressions, explicit evidence references and actual finite domains. The CLI uses 50 significant decimal digits; nonterminating division is rounded at that precision.

The search returns a conditional lexicographic optimum within the declared finite domain. The schedule command audits a supplied schedule; it does not search every possible schedule. Unsupported expressions, invalid inputs and exhausted limits are failures/unknowns, not proofs of scientific infeasibility. Recompute the chosen point independently from the original quantities. Use and retain a different verifier when the actual mathematical structure requires it.

## Deliver a reviewable plan

Deliver the requested plan, evidence ledger, parameter table, controls, resource accounting, explicit schedule, decision rules, risk responses, confirmations and change record. Save machine-readable results and the normalized arithmetic inputs/scripts needed to reproduce the checks.

Use [references/output-and-review.md](references/output-and-review.md) for the final scientific, arithmetic and output-schema review. Verify units, integer purchases, independent sample counts, equipment capacity, booking coverage, dependencies and deadline. Report missing material, inability to determine and execution failure separately. An essential unresolved instrument setting or safety/ethics prerequisite prevents treating the affected operation as ready to execute.

Generate a figure only when actual data and the requested task justify it. Distinguish a planning visualization from a reproduced measurement. If original data or figures are missing, describe the limitation instead of drawing a matching-looking surrogate. Check real renderings of any editable document or diagram that is part of the delivery. Mechanical verification supports review; it does not certify scientific validity or laboratory authorization.
