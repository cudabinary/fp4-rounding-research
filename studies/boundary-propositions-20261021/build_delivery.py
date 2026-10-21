"""Build a reviewed English delivery in a fresh local directory."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import argparse
import datetime
import hashlib
import json
import re

STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[1]
PRIOR = REPO/'studies/precision-boundaries-20261021'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check_text(data, label):
    encoding = 'utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
    text = data.decode(encoding)
    assert not re.search(r'[\uac00-\ud7a3]',text), ('Non-English source',label)
    path_pattern = r'\b[A-Za-z]:[\\/]|/Users/[A-Za-z0-9_.-]+/|/home/[A-Za-z0-9_.-]+/|file://(?:/[A-Za-z]|[A-Za-z]:)'
    assert not re.search(path_pattern,text), ('Personal path',label)
    assert not re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|sk-proj-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)',text), ('Credential pattern',label)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-source',type=Path,required=True)
    ap.add_argument('--destination',type=Path,required=True)
    args = ap.parse_args()
    out = args.destination.resolve()
    assert not out.exists(), 'Delivery destination must be new'
    out.mkdir(parents=True)
    package = out/'fp4_boundary_evidence_20261021_v2'
    package.mkdir()
    records = []

    def add(relative,data,role,source_hash=None):
        check_text(data,relative)
        assert len(data) < 2000000, ('Payload limit',relative)
        p = package/relative
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data)
        records.append(dict(path=relative,bytes=len(data),sha256=sha(data),role=role,
                            source_sha256=source_hash or sha(data)))

    prior_manifest = json.loads((PRIOR/'payload_manifest.json').read_text())
    for entry in prior_manifest['files']:
        data = (PRIOR/entry['path']).read_bytes()
        assert len(data)==entry['bytes'] and sha(data)==entry['sha256']
        add('studies/precision-boundaries-20261021/'+entry['path'],data,'BYTE_IDENTICAL_COMPLETED_ROUND_1')
    data = (PRIOR/'payload_manifest.json').read_bytes()
    add('studies/precision-boundaries-20261021/payload_manifest.json',data,'ROUND_1_IDENTITY_MANIFEST')
    science = json.loads((STUDY/'scientific_manifest.json').read_text())
    for entry in science['files']:
        data = (STUDY/entry['path']).read_bytes()
        assert len(data)==entry['bytes'] and sha(data)==entry['sha256']
        add('studies/boundary-propositions-20261021/'+entry['path'],data,'BYTE_IDENTICAL_COMPLETED_ROUND_2')
    add('studies/boundary-propositions-20261021/scientific_manifest.json',
        (STUDY/'scientific_manifest.json').read_bytes(),'ROUND_2_IDENTITY_MANIFEST')

    original_manifest = json.loads((args.raw_source/'FILE_MANIFEST.json').read_text())
    by_name = {e['file'].replace('\\','/'):e for e in original_manifest}
    for name in ('scan.log','direct_validation.log','p53_counterexamples.jsonl'):
        data = (args.raw_source/name).read_bytes()
        expected = by_name[name]
        assert len(data)==expected['bytes'] and sha(data)==expected['sha256']
        add('selected_raw/round1_'+name,data,'BYTE_IDENTICAL_SELECTED_RAW_CALCULATION')
    trace = by_name['independent_checks.jsonl']
    trace_ref = dict(role='UNCHANGED_RAW_TRACE_NOT_BUNDLED',bytes=trace['bytes'],sha256=trace['sha256'],
                     source_archive_sha256='d139b93db4cb1649846ecd5bc7a64b767f4a79572a8b50362cda5966a1ee216b',
                     archive_remote_file_id=None,
                     reason='Larger raw trace retained in sealed original; approved delivery is code, English documents and small results')
    add('selected_raw/round1_full_trace_reference.json',
        json.dumps(trace_ref,indent=2).encode(),'EXPLICIT_RAW_TRACE_OMISSION_REFERENCE')
    summary = (
        'FP4 precision-boundary evidence delivery version 2\n\n'
        'This is a selected English research delivery, not a full repository or raw-dataset backup.\n'
        'Read studies/boundary-propositions-20261021/propositions_and_proof.txt first.\n'
        'The prior 45/49 and 37/38 boundaries are certificate-assisted; new work verifies exact\n'
        'statement scopes and lexicographically minimal witnesses with 78552 prefix evaluations.\n'
        'Pure symbolic sufficiency, proof-assistant checking and publication novelty remain OPEN.\n\n'
        'From this directory, verify without rerunning numerical scans:\n'
        'python studies/precision-boundaries-20261021/verify_import.py\n'
        'python studies/boundary-propositions-20261021/verify_statements.py\n\n'
        'Reproduce only in a fresh copy:\n'
        'python studies/boundary-propositions-20261021/targeted_reference.py\n\n'
        'Both verification scripts and the targeted reference require Python standard library only.\n'
        'The initial historical repository manifest verifier mentioned in the round-1 README\n'
        'requires the full repository and is intentionally not part of this selected package.\n'
        'No GPU, compiler, model, install, large historical sweep or optimized candidate is run.\n'
        'ZIP metadata dates are normalized for reproducible packaging, not claimed run timestamps.\n'
        'file_manifest.json records every packaged file except itself. Source bytes and omissions\n'
        'are labelled explicitly. Korean originals and the original sealed ZIP remain unchanged.\n'
        'No Library ID is asserted by a local package. B2 remote checkpoint status is pending.\n'
    )
    add('README.txt',summary.encode(),'NEW_ENGLISH_DELIVERY_GUIDE')
    manifest = dict(schema='reviewed-delivery-content-v1',base_commit='719fe72340dfc3e07e62f7af2d3d0d87ae0538e2',
                    selection='FP4 code, English documents, small results, selected exact calculation bytes and hashes',
                    files=sorted(records,key=lambda r:r['path']),excludes=['file_manifest.json'])
    mdata = json.dumps(manifest,indent=2).encode()
    (package/'file_manifest.json').write_bytes(mdata)
    archive = out/'fp4_boundary_evidence_20261021_v2.zip'
    with ZipFile(archive,'x',compression=ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(package.rglob('*')):
            if p.is_file():
                info = ZipInfo(p.relative_to(package).as_posix(),date_time=(2026,10,21,0,0,0))
                info.compress_type=ZIP_DEFLATED
                info.external_attr=0o100600 << 16
                z.writestr(info,p.read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=6)
    with ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {e['path'] for e in records} | {'file_manifest.json'}
        for entry in records:
            data=z.read(entry['path'])
            assert len(data)==entry['bytes'] and sha(data)==entry['sha256']
    receipt = dict(schema='reviewed-local-delivery-v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   archive_name=archive.name,bytes=archive.stat().st_size,sha256=sha(archive.read_bytes()),
                   zip_crc='PASS',file_count=len(records)+1,uncompressed_bytes=sum(e['bytes'] for e in records)+len(mdata),
                   content_manifest_sha256=sha(mdata),content_inventory=manifest['files'],
                   english_personal_path_credential_pattern_scan='PASS',
                   library_status='NOT_UPLOADED_NO_LIBRARY_TOOL_EXPOSED',library_id=None,
                   b2_status='HELD_PENDING_LEDGER_AND_COST',original_files_modified=False)
    (out/'delivery_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ('archive_name','bytes','sha256','zip_crc','file_count','uncompressed_bytes')}))

if __name__=='__main__':
    main()
