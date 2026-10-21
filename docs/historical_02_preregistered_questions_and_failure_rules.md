# Frozen questions and failure rules

REPRO/PREREGISTERED_PROTOCOL.json was written before threshold experiments. SHA256:
d577e1107441ac6e8278143ec3226d29d27425224d8f900cfbdf3020f28c69ee.

## D1 — no compatibility increment on the actual producer domain

Claim: for every finite BF16 x with group amax>=abs(x), and s=RN32(amax/6) or all-zero fallback, deleting B's final RN64 compatibility increment preserves canonical threshold/base against source A″.

One valid disagreement falsifies the claim. Source B, source A″ and an independently implemented integer-U128 ratio→RNE64 oracle must agree; a baseline/oracle disagreement aborts the main test rather than permitting tuning. Candidate count1; no CUDA candidate is generated.

## D2 — additional necessity/removal rule

Question: does the legal domain yield an actual computational removal or useful necessity rule beyond the already-known generic B guard? A domain-specific removal can be retained if D1 passes, but “domain specialization is useful” or a larger test count is not a novel rule by itself. If D1 had failed, first witnesses and per-amax records would be preserved; no rescue candidate would be selected automatically.

## Exact execution plan and complete reporting

Magnitude order: all-zero, increasing amax1..32639, then x0..amax. Exhaustive coverage with sign symmetry; no case sampling or exponent normalization assumption. All BF16 subnormal magnitudes and derived subnormal scales are included directly.

Fixed smoke rows: amax1,127,128,447,448,16256,32639; eight signed corners; one old arbitrary-F32 rounding witness. Smoke50,054 legal pairs passes. The old witness deliberately remains outside the restricted producer domain and fails the no-correction candidate while matching A/B/oracle.

Main test compares A″, unchanged B, D1 and the U128 RNE oracle on532,701,120 pairs. Store disagreement/carry/guard totals, all32,639 per-amax rows and first32 candidate counterexamples if any. No counterexample suppression or success-only variant selection.

Budget: existing local tools,1800seconds, maximum2workers/4GB target. Actual worker1; no allocation proportional to the Cartesian product (a few fixed arrays/streaming CSV). No failed experiment or retry occurred. No new GPU/kernel/module load, remote, CUDA compile, paid resource or model run.

## Observation vs proof

This is complete finite verification of the concrete scalar CPU semantics and explicitly specified domain, not a solver proof of arbitrary source/CUDA compilation. Algebra explains why D1 is ideal-rational floor; empirical exhaustiveness establishes its equality to the legacy RN64 evaluator on this finite domain. A universal analytic no-crossing theorem or maximal-domain characterization is not claimed.

## Application phase

Only after the completed scalar result, APPLICATION_MODEL_PROTOCOL.json freezes one proposed point-to-point use and all bandwidth/extra-cost scenarios. This is accounting over inherited latency and assumed bandwidth, not another scalar-candidate search or new runtime measurement. The family of raw timing inputs remains unchanged.
