"""Verify proposal identities and references, without any scientific computation."""
from pathlib import Path
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]


def verify():
    links=json.loads((HERE/'evidence_links.json').read_text())
    records=links['artifacts']
    by_id={x['id']:x for x in records}
    assert len(by_id)==len(records)
    for item in records:
        path=(REPO/item['path']).resolve()
        assert path.is_relative_to(REPO)
        data=path.read_bytes()
        assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
    for module in links['modules']:
        assert set(module['evidence_ids'])<=set(by_id)
    main=(HERE/'proposed_sections.txt').read_text()
    blocks=re.findall(r'^\[(P[1-7])\]',main,re.MULTILINE)
    assert blocks==[f'P{x}' for x in range(1,8)]
    guide=(HERE/'revision_guide.txt').read_text()
    for block in blocks:assert block in guide
    assert all(x in guide for x in ('R1','R2','R3','R4','R5','R6','R7','R8'))
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['status']=='PROPOSAL_ONLY_NOT_APPLIED_TO_MANUSCRIPT'
    assert protocol['scientific_programs_to_execute']==[]
    manifest=HERE/'payload_manifest.json'
    if manifest.exists():
        for item in json.loads(manifest.read_text())['files']:
            path=(HERE/item['path']).resolve()
            assert path.is_relative_to(HERE)
            data=path.read_bytes()
            assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
    return dict(status='PASS_PROPOSAL_IDENTITIES_AND_REFERENCES',replacement_blocks=len(blocks),
                referenced_evidence_files=len(records),scientific_modules_imported=0,
                scientific_or_integer_checks_executed=0,enumeration_runs=0,
                limitation='Document consistency only; no mathematical proof, numerical result, native execution or layout revalidation')


if __name__=='__main__':print(json.dumps(verify(),indent=2))
