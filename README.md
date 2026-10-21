# FP4 stochastic rounding research

Private, independent research workspace for the preserved paper and future work. The initial import uses only earlier sealed artifacts, with SHA256 links to the existing global backup. Ongoing October 21 research is excluded.

The preserved study reports 532,701,120 CPU input pairs under a restricted BF16/amax-derived scale contract. D1 is not a universal replacement on arbitrary F32 inputs. Historical GPU comparisons and failure boundaries remain scoped to the archived protocol; this setup adds no new performance or novelty claim.

## Contents

- `manuscript/`: English manuscript copies and available historical typesetting sources.
- `code/`: selected historical source files, retained byte for byte.
- `results/`: small historical tables, protocols, and receipts.
- `evidence/source_manifest.json`: original identity and exact B2 pack extents for each admitted file, plus archive-only original references.
- `evidence/file_manifest.json`: hashes of the initial curated checkout, excluding that manifest itself.
- `docs/reproduce.md`: verification and recovery boundaries.
- `docs/backup.md`: shared-budget backup operation and commit linkage.
- `docs/tag_policy.md`: future tag policy and examples only.

Start with `python tools/verify_manifest.py`. This verifies file identity without launching experiments. The checkout is a selected seed, not a complete fresh-machine GPU installation. Full source archives, inputs, raw outputs, failed runs, Korean originals, and their historical receipts remain available through the raw archive catalogue.

Private B2 bucket: `cudabinary-research-archive-20261021`. Paper prefix: `research-archive/papers/fp4-rounding/`. Prefixes provide organization within one existing permission scope. The external checkpoint records the exact Git commit, bundle object/version, source-manifest hash, raw-catalogue version, and SHA256 values. Read `evidence/backup_receipt.json` after the initial backup has been verified.
