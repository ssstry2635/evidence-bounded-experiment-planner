---
name: evidence-bounded-experiment-planner
description: Generate, compare and revise experimental plans using actual scientific evidence, finite parameter domains and explicit resource constraints. Includes deterministic budget, procurement and schedule checks for auditable planning.
---

# EvidenceBound Planner

Version 1.1.0. Build a research plan whose scientific assumptions, resource needs and revisions can be inspected. Use the bundled Python tools to recalculate candidate plans, find feasible revisions, and audit resource schedules.

## Establish the task

Read the caller's research brief, supplied sources, candidate plans and resource information. When present, use `/input/case.json`, `task.md` and `environment/resources.yaml` to find the inputs, tools and output contract. Inventory the actual files and keep their IDs and versions. Use original sources to resolve misleading labels. Extract the research question, requested deliverables and hard thresholds before reviewing the candidates.

Use the caller's paths. In the mounted case environment use `/app/work` and `/app/output`; otherwise default to `work/` and `output/`. Save a valid partial `result.json` early with `case_id`, all supported fields and concrete missing prerequisites. Preserve the caller's field names, types and nesting. Put audit details in a separate file if the contract forbids extra fields. Leave time to validate the final output and its referenced files.

## Ground parameters in evidence

Read the relevant paper methods, supplements, instrument manuals, inventory and booking information. Inspect rendered source pages when text extraction loses tables, equations, units or image context. Record actual source paths, versions, page/section locators, short supporting quotations and extraction uncertainty.

Use [references/evidence-and-design.md](references/evidence-and-design.md) to create an evidence ledger. Distinguish reported facts, project-specific resource assumptions, calculations, proposed settings and items needing expert confirmation. A simulated price or booking remains a scenario input. A published experimental setting does not by itself establish a safe operating limit for another instrument.

## Design, compare and revise

Connect the hypothesis, operational variables, primary endpoint, relevant controls, equipment/materials, parameter ranges, time/cost estimates and failure responses. Identify independent replication separately from repeated readings. Define quality gates, missingness rules and decision criteria before results are observed.

Inspect every supplied candidate and preserve its ID and version. Compute the as-written values from primitives and report each applicable hard constraint with value, limit, unit, signed margin, decision and source. Keep original settings apart from allowed revision domains. Identify whether the contract prioritizes minimal change, cost, time or another objective. Hard feasibility comes first. If no feasible point exists, retain which constraints each candidate fails and give a concrete failed point with the exact limits. An unavailable prerequisite remains unresolved, even when the arithmetic can be checked.

Revise the selected source plan with a change log: original/revised version, field, before/after values, reason, evidence, downstream effects and remaining uncertainty. Retain unaffected choices where possible. Do not remove scientifically necessary controls to make a budget appear feasible. Do not optimize an invented scientific response or report proposed experiments as completed measurements.

## Run the deterministic checks

Read [references/verification.md](references/verification.md). Run from the installed Skill directory and use absolute paths for the working files when needed. The example commands use repository-relative paths.

```bash
python scripts/verify_plan.py solve examples/model.json --out output/search
python scripts/verify_plan.py compare examples/model.json --out output/comparison
python scripts/verify_plan.py schedule examples/schedule.json --out output/schedule-audit.json
```

For a generate-and-revise request, normalize all supplied candidates into one model with `baseline` values and explicit finite `domains`. Run `compare` to obtain each original calculation, the nearest feasible revision by field count, and a change log. For another required optimization priority use `solve` on the allowed domains and select by the caller's rule. Retain the source-to-model mapping, normalized inputs and reports. Use consistent units, distinguish stock from purchased packs, count controls and setup/cleanup, and verify the exact selected revision with a separate schedule audit.

The search returns a conditional lexicographic optimum within the declared finite domain. The schedule command audits a supplied schedule; it does not search every possible schedule. Unsupported expressions, invalid inputs and exhausted limits are failures/unknowns, not proofs of scientific infeasibility. Recompute the chosen point independently from the original quantities. Use and retain a different verifier when the actual mathematical structure requires it.

## Deliver a reviewable plan

Assemble the requested plan using the [handoff worksheet](references/plan-worksheet.md). Include evidence locators, measurement and control acceptance criteria, parameter ranges with units, a step-to-resource schedule, budget lines, and risk triggers with a stop or recovery action. Bind each confirmation to the affected step and name the evidence needed to clear it. Recompute the selected plan from source primitives, validate its schedule independently, and link every material revision to what triggered it.

Use [references/output-and-review.md](references/output-and-review.md) for the final scientific, arithmetic and output-schema review. Verify units, integer purchases, independent sample counts, equipment capacity, booking coverage, dependencies and deadline. Report missing material, inability to determine and execution failure separately. An essential unresolved instrument setting or safety/ethics prerequisite prevents treating the affected operation as ready to execute.

Generate a figure only when actual data and the requested task justify it. Distinguish a planning visualization from a reproduced measurement. If original data or figures are missing, describe the limitation instead of drawing a matching-looking surrogate. Check real renderings of any editable document or diagram that is part of the delivery. Mechanical verification supports review; it does not certify scientific validity or laboratory authorization.
