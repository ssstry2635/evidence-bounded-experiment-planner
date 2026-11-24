# Review worksheet for an executable plan

Use this worksheet to find omissions before handing off a plan. Map these fields onto the requested output contract. Add supporting files when the contract has a stricter schema. Treat any field you cannot verify as unresolved and identify the action needed to resolve it.

| Record | Fields to retain | Review question |
|---|---|---|
| Hypothesis and variables | Experimental unit, treatment and comparator, operational definitions, endpoint method and unit, time point, expected direction, decision threshold, confounders | Could the proposed observation reject the hypothesis? |
| Control | Control ID, role, condition, question or confounder it tests, expected readout and acceptance interval, response if it fails | Does the control establish interpretability for this endpoint? Consider background, negative or positive reference, and calibration only where relevant. |
| Parameter and equipment | Step ID, setting, unit, discrete values or range, instrument/model or minimum capability, consumable grade/specification, source locator, uncertainty, substitution rule | Does the setting lie in the intersection of protocol evidence, equipment capabilities and project constraints? |
| Schedule and cost | Step, predecessor, active and instrument time, batch capacity, booking window, quantity, purchasable pack size, stock, price basis, subtotal and total | Can the selected version fit the resources, including controls, failed-run reserve when allowed, and setup or cleanup? |
| Risk and exception | Affected step, observed trigger, detection method, stop/hold rule, recovery, retry limit, resource impact, owner | Can an operator decide what to do as soon as the trigger is observed? |
| Evidence and confirmations | Evidence ID, path/version, page/table/row, observed value or supplied assumption, safety/ethics/equipment/expert confirmation, affected step and clearance condition | Can someone independently verify the input or see exactly what still needs approval? |

Review the as-written plans and revisions in this order.

1. Reconcile IDs and versions. Make one normalized model for comparable candidates, documenting any source-specific assumptions and keeping their original settings intact.
2. Read the as-written comparison and resolve any unit conversions or uncertain rule interpretations. Preserve infeasible candidates and record each failure with observed value, limit and evidence.
3. Apply the requested selection order and retain the chosen original version. Record each changed field, reason, supporting evidence, derived cost or time changes, and rechecked constraints. Auditing a candidate is valid even if it remains infeasible.
4. Audit the final schedule using the revised batch counts and durations. Compute the budget again from quantities, pack rounding and prices. Check the control acceptance criteria and any conditional resource or safety prerequisite.
5. Return the requested result, source mapping, normalized inputs, verification artifacts and change log. Separate a missing document or booking, a scientifically undecidable conclusion, and a failed calculation. If the complete decision remains blocked, provide the verified portions and name the blocking input.
