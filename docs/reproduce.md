# Verification and recovery

Run from the repository root:

```text
python tools/verify_manifest.py
```

This checks sizes and SHA256 values for the initial curated snapshot. It does not validate scientific claims, compile historical programs, rerun experiments, or treat old receipts as newly executed tests.

The English-metadata PDF is a labelled derivative of the preserved manuscript, with identical scientific page content; see manuscript/README.md. The original DOCX contains Korean XML metadata or font naming and remains archive-only with its exact hash. The historical independent_reference.py contains machine paths and Korean material and is also archive-only. The CPU threshold host requires its sibling exact header, legacy reference header, and decoder; those exact bytes are present. domain_audit.cpp additionally requires the archived SCALE_BITS.bin in a fresh run directory. Restore that exact file using its raw catalogue entry before building or running; do not synthesize a replacement and call it historical evidence. NumPy is required by the selected Python numerical modules. CUDA source is preserved for comparison; no new GPU run or speed claim is made.

For a fresh recovery, obtain the immutable checkpoint and expected SHA256 from the coordinating verification report or a subsequent audited receipt. Use the existing restricted archive authentication outside Git. Download the checkpoint by its B2 file ID, verify its hash, then download its referenced Git bundle and verify that hash. Verify the bundle in a new empty repository, fetch its main branch, and compare the recovered HEAD and tracked file hashes. Do not restore over an original or active research directory.

For raw evidence, download and verify the referenced catalogue. Locate the desired source ID, download each exact B2 object version, verify the whole pack SHA256, concatenate the indicated extents in file-offset order, and compare the complete logical file SHA256 and size. Existing archive restore tools implement this process. Object names alone do not pin a version; use the recorded file ID.

The initial setup verifies remote manifests, both Git bundle recoveries, all tracked checkout files, and at least one historical representative file per paper reconstructed from a freshly downloaded existing global pack. It is not a complete raw-dataset restore or a different-physical-computer test.
