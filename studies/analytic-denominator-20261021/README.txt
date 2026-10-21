Analytic denominator proof step

Base commit: f7ba45359f485eaffd23794604fb9d636546bc56.
Read analytic_proof.txt for the complete domain and proof chain.

New proof work:
- Unnormalized subnormal scale units give 3D=A*2^q+epsilon for q15/16/17.
- A common positive-integer t identity exposes the remaining residue gap.
- A complete elementary proof draft establishes the conservative b32,p53
  subnormal sufficient condition through ten explicit integer brackets and
  five nonsquares, without the historical raw-pair enumeration.
- The known p44/p48 witnesses analytically require uniform precision of at
  least 45/49 in the stated p35..64 interval.

The exact p45 normal and p49 full-domain sufficient clauses still need the
old finite certificates. Their sharper analytic exclusions R45 and R49 are
OPEN. The larger-j residual sets cannot be replaced by the small-j p53 proof.
Neither passing examples nor the constant-check script close those obligations.
Code-order witness minimality is inherited and separate from uniform precision
optimality. The earlier p45/p49 and p37/p38 numerical certificates are unchanged.

source_comparison.txt records actual acquired Roux/Saiki premises and the
unavailable Rump lemma. No global theory-independence or novelty claim follows.
The exact missing historical final-limits report remains unidentified; no
neighboring report is substituted.

Verification:
python studies/analytic-denominator-20261021/verify_analytic_steps.py

This checks 13 scale examples, 10 published proof-bracket constants, 5
nonsquares, small modular case classifications and 6 fixed witness evaluations.
It does not sweep raw pairs or rerun the 78552-pair or large historical scans.
The examples are sanity checks, not the universal proof's coverage argument.
The proof is not formalized in Lean/Coq and is not a CUDA implementation proof.

All new filenames, text and code are English. Original evidence is preserved.
No GPU, compiler, install, optimized kernel, other-paper work, tag, release,
submission, paid extension, duplicate Library upload or B2 transfer occurs.
The two earlier ZIPs are left to the designated upload session, without
messages or duplicate transfer from this chat. B2 remains held for the shared
ledger and cost conditions. The next mathematical step is the R49 residue
exclusion at the enlarged j bounds, rather than another raw-input scan.
