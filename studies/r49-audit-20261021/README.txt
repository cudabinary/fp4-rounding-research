R49 reduced-certificate result and independent S53 audit
2026-10-21

Start with r49_proof.txt and proof_status.json. The result is subnormal-scale
p49 no-carry on the fixed BF16/derived-F32/b32 scalar contract. It uses an
analytic reduction plus a complete small coefficient/t certificate. It is
not a pure symbolic theorem, a sample pass, or proof-assistant verification.

Reproduce the certificate check using Python 3.9 or newer with the standard
library (the recorded run used Python 3.12.14):

  python studies/r49-audit-20261021/certificate_verifier.py

This checks supplied residue identities and complete branch coverage, without
calling modular inversion or any historical raw-pair evaluator. To regenerate
the small certificate deliberately, run residue_kernel.py; it writes the ledger
and kernel_results.json. The complete ledger has 4656 coefficient/t branches,
one relaxed congruence survivor, and no legal BF16 reconstruction.

The separate independent/ review audits the preceding S53 proof from definitions
using independently constructed limited checks. Its sample pairs are diagnostic;
the universal S53 conclusion comes from the mathematical case review. A separate
R49 review describes its scope and checking method. Neither is human replication
or a proof-assistant development. Follow each review's explicit scope limits.

The prior source commit is 2e7c2dae61ac9da85e889168694a459bfed13cd1. All previous
studies and original artifacts remain byte-identical. payload_manifest.json
identifies this study's files; verification.json records validation. Parent
relative source references identify the prior proof and finite normal result.

Full-domain p49 sufficiency still uses the normal-scale finite certificate;
compact symbolic normal p45 and universal b37 proofs remain open. Novelty,
Rump Lemma 4.6 derivability, formal verification, and practical runtime value
are not settled. No GPU, compiler/install, kernel optimization, old large scan,
raw prefix rerun, other-paper work, or B2 transfer was performed in this round.

The delivery ZIP is a fresh local artifact. A successful local ZIP check or Git
push is not a Library upload. Its external receipt records bytes, SHA256, CRC,
and content verification; no Library identifier is fabricated.
