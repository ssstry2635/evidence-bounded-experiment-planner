# Delivery and final review

Example Agent request: “Read this repository's SKILL.md, compare the candidate plans in data/case.json against the supplied evidence and resource constraints, and save the revised plan and result.json in output/.” These paths are defaults; use the caller's explicit paths and output schema when supplied.

A reviewable result can contain `case_id`, `status`, `hypothesis`, `variables`, `controls`, `candidate_comparison`, `selected_plan`, `steps`, `parameters`, `resources`, `sample_accounting`, `cost_breakdown`, `schedule`, `decision_rules`, `risks`, `confirmations`, `sources`, `uncertainty`, `validation` and `change_log`. This suggested structure supplements the requested output schema. A required unknown value still needs a reason and an honest partial status.

Review the science: hypothesis-endpoint-control alignment, independent replication, calibration, equipment compatibility, evidence and measurable failure triggers. Review the arithmetic from primitives: units, integer counts, material balance, existing stock versus purchases, pack ceilings, full cost, concurrency, booking windows and deadline. Review the output: all requested fields/types/IDs, candidate versions, referenced files and final change records.

Validate against a supplied JSON Schema when one exists. Ensure attached CSV, scripts and reports agree with result.json. If two checks disagree, fix the problem or retain a partial result. Missing source material, a genuinely undecidable comparison and a tool crash should be distinguishable. Continue unaffected parts when a missing resource does not affect them.

Retain actual source hashes, tool versions and inputs. Report a scenario budget as a scenario estimate rather than a bill. Report proposed experiments as proposals rather than measurements. Deterministic arithmetic does not establish a future scientific response or authorize laboratory work.
