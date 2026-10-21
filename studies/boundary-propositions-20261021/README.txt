Boundary propositions and independent minimal witnesses

This is a new CPU-only step after commit
719fe72340dfc3e07e62f7af2d3d0d87ae0538e2. The previous completed scans and the
original Korean report, source copies and ZIP remain unchanged.

Read propositions_and_proof.txt for the exact predicates, parameter intervals,
necessary/sufficient distinction and the dependency of each proof unit.
statement_certificate.json links the inherited positive finite cells to their
hashes. Those large scans were not rerun. All-input symbolic sufficiency,
proof-assistant verification, complete derivability from Rump/Flocq, publication
novelty and practical runtime value remain OPEN.

The new bit-serial integer reference evaluates 78552 raw-code prefix pairs,
84 witness/precision cases and three zero cases. All 340 generated scales
agree with an independent midpoint method; 195 rounding checks agree with a
separate exact midpoint reference. Prefix endpoints were selected from known
witnesses; this validates minimality rather than claiming prospective discovery.

Lexicographic order is (nonnegative BF16 amax magnitude code,x magnitude code).
The first normal-scale b32,p44 failure is amax 0x01ec, x 0x00c7; its threshold
changes 2274877096 -> 2274877097. The first full-domain b32,p48 failure is
0x00f2,0x00dd, changing 3176857458 -> 3176857459. The first full-domain
b38,p53 failure is 0x0010,0x0004, changing 274876334082 -> 274876334083.
These minimality claims are justified by complete preceding raw-code prefixes,
not by a random search or an assertion that every notion of smallness agrees.

Verification without a new numerical scan:
python studies/precision-boundaries-20261021/verify_import.py
python studies/boundary-propositions-20261021/verify_statements.py

To reproduce the new targeted run, use a fresh copy of this delivery or the
study directories, then run:
python studies/boundary-propositions-20261021/targeted_reference.py

The Python code requires only the standard library. The original large scans
can also be reproduced from their included code/protocol in a fresh copy, but
they are not prerequisites for the small witness reproduction and were not
repeated in this step. The analysis wall times are not quantizer performance.

The English delivery contains the completed study code, English explanations,
small structured results, exact selected calculation logs, reproduction steps,
and per-file hashes. The larger 24159-row round-1 diagnostic trace remains
unchanged in its original sealed archive and is identified by SHA256 rather
than bundled as a large raw log. No keys, personal machine paths, unrelated
research, model data, GPU arrays or Korean originals are included.

The current Library catalogue query succeeded but exposed zero Library tools
and no continuation cursor. No ZIP upload was called and no Library ID exists.
This is a capability block, not a claim that the earlier approval rejection
was retried successfully. The earlier rejection concerned missing exact
payload/destination authorization; later user evidence authorized only this
paper's reviewed payload and specified private destinations. No alternate
account, storage service or Page is used as a workaround.

The fourth exact historical final-limits report remains unidentified and is
not replaced by an adjacent decision report. The three earlier restored
historical reports retain their separately verified hashes. Official alternate
Rump sources returned timeout and HTTP 403; no permission or TLS bypass was
attempted. B2 transfer/checkpoint creation remains held for the once-only
ledger merge and bounded account-cost conditions. No GPU, compiler, install,
new optimized candidate, tag, release, submission or automation was executed.
