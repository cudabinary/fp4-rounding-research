Normal p45 reduction and one independent R49 enumeration
2026-10-21

Start with normal45_proof.txt and proof_status.json. The normal p45 statement
is proved with an algebraic reduction plus a complete small finite certificate.
A purely symbolic replacement of that coefficient enumeration remains OPEN.
The p44 counterexample establishes necessity within p35..64. Native p45 GPU
arithmetic, a new SR algorithm, novelty and speed are not claimed.

Using Python3.9+ standard library (recorded3.12.14), from repository root:
  python studies/normal45-independent-r49-20261021/normal45_certificate_verifier.py
  python studies/normal45-independent-r49-20261021/compare_r49.py

The normal verifier checks complete branch and residue coverage without
modular inversion. fixed_arithmetic_checks.py deliberately recomputes seven
scale examples, a p44 negative control and p45 pass for one known witness,
and the two eta exclusions. normal45_reduction.py and
normal45_certificate_builder.py regenerate only the bounded normal
coefficient conditions; they do not run raw BF16 pairs or old orchestrators.

The independent R49 first run is frozen, not blindly repeated. It used its
own direct-j code and protocol, without old kernel/table imports or copying.
Its protocol discloses prior exposure to the earlier conclusion; this is
implementation independence, not a blind experiment or human replication.
Every one of its 4656 branches and six reconstructions agrees with the prior
sealed certificate. r49_comparison_results.json and r49_branch_comparison.csv
record the comparison after freeze. No expected result was asserted in the
independent enumerator. The normal algebra review is separate from that
freeze and does not claim independent enumeration of the normal236 cases.

The independent raw every-j CSV is 5219160 bytes and remains outside Git.
archive_only_manifest.json and independent/freeze_manifest.json identify it
by logical path and SHA256. The fresh local delivery ZIP includes that raw
CSV at its original logical path. The small per-branch CSV remains in Git.
Running independent/direct_j_conditions.py intentionally regenerates raw
outputs in its directory; it is a reproduction command, not a required
read-only verification step. Only one independent run occurred this round.

The ZIP includes required prior comparison files and proof dependencies at
their repository-relative paths. It is not a complete repository-history
archive. The local Git bundle and fresh recovery clone preserve history.
The new commit retains 07ac3e0 and all older files byte-for-byte. No Library
upload, B2 transfer, GPU, compiler/install, paid-resource or other-paper work
is included. ZIP receipts and Git remote verification are separate facts.
