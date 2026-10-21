Completed CPU precision-boundary study

This directory imports the completed October 21 arithmetic study into the
dedicated repository. It does not rerun the study or modify the initial
historical snapshot. The comparison baseline is commit
3cff792a70b419eaf1c2a9dc029c057ebad00978.

New arithmetic evidence

The input remains finite BF16, with 0<=x<=amax and F32 RN-even(amax/6) scale,
gradual underflow, the unchanged E2M1 grid, and zero fallback 2^-42.
The working significand precision p is virtual RNE-p with binary64 exponent
range. The probability-lattice precision is b. No new physical RNG policy is
implemented for b>32.

At b32, the first safe p in the preregistered p>=b+3 region is 45 for normal
scales and 49 when subnormal scales are included. The independent direct
validator found five normal representative failures at p44 and one subnormal
failure at p48. It found none at the corresponding p45 and p49 boundaries.

At p53, b37 passes and b38 fails on nine subnormal-scale pairs; the checked
normal-scale representative classes at b38 pass. The small b38 witness has
BF16 amax=0x0010, x=0x0004 and derived F32 scale=0x0002aaab. Its ideal and
RN53 thresholds are 274876334082 and 274876334083, respectively.

The primary gap scan covers 8,242,261 parameter/representative cases across
eleven b settings. A separate Fraction nearest-neighbor reference checks
24,159 cases. Direct integer RNE followed by full grid interpolation checks
3,105,916 boundary evaluations without the gap inequality. The written
exponent-reduction and small-ratio-tail arguments are in derivation_and_scope.txt;
they have not been checked by a proof assistant. These are related deterministic
arithmetic evaluations, not independent workloads or GPU executions.

Relation to the historical snapshot

The initial snapshot already contains the b32,p53 no-carry result and the
532,701,120-pair historical certificate. The new results characterize different
precision boundaries and legal internal counterexamples. They do not rerun
that historical sweep. Historical CUDA timing, D1's gain over B, and its loss
to the strong A-double-prime baseline on ordinary inputs remain inherited
results; this import adds no new speed, model-quality, or hardware claim.

theorem_mapping.txt records direct substitution into Roux Theorem 29 and
Saiki v1. The inspected direct rules do not by themselves establish the current
RNE-to-threshold-floor identity. This is not a proof of independence from their
full theories. Rump's exact lemma was not freshly recovered after source access
failures. General-theory independence and publication novelty remain OPEN.

Identity, restoration and raw evidence

The two Python files, original preregistration and selected completed outputs
are copied byte for byte; import_provenance.json records their original hashes.
p53_counterexamples.json is a JSON-array derivative of the preserved raw JSONL;
its source hash and all 37 records are retained. The original Korean report,
machine-path-bearing receipts, raw logs, paper inputs and downloaded reading
copies remain unchanged in the sealed original completion archive.

Original completion ZIP SHA256:
d139b93db4cb1649846ecd5bc7a64b767f4a79572a8b50362cda5966a1ee216b
Size: 2234525 bytes. ZIP CRC check passed. Its B2 file ID is not yet assigned
by this import; do not treat the local archive reference as a remote backup.

The original round correctly recorded four reports unavailable at input seal.
This import freshly verifies three selected historical reports against their
archive source identities and the later protected restoration. These are the
analytic lemma, domain exactness results, and prior-art delta. This later check
does not rewrite the original run's missing-input record or turn a post-run
hash into an at-run attestation. The fourth, exact final-limits report remains
unverified. A nearby contribution-decision report is not used as its substitute.

Verification and next action

Run tools/verify_manifest.py from the repository root for the immutable initial
curated files, and this directory's verify_import.py for the imported payload.
Neither command reruns numerical experiments. Reproduce an experiment only in
a fresh copy, keeping the sealed original and raw logs unchanged.

The next scientific action is an analytic account of the normal/subnormal
precision boundary and the b37/b38 transition, connected explicitly to existing
theorem premises. No optimized candidate or GPU experiment starts during this
repository transition. New B2 transfers remain held until the task-only transfer
increments are merged exactly once with current MAIN counters and account cost
can be bounded. No tags, releases, publication or automation are introduced.
