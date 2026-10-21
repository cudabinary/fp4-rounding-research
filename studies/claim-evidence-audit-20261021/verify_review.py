"""Verify review references and byte identities only; never run research code."""
from pathlib import Path
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]


def verify():
    index=json.loads((HERE/'evidence_index.json').read_text(encoding='utf-8'))
    entries=index['artifacts']
    by_id={x['id']:x for x in entries}
    assert len(by_id)==len(entries)
    for item in entries:
        path=(REPO/item['path']).resolve()
        assert path.is_relative_to(REPO)
        data=path.read_bytes()
        assert len(data)==item['bytes']
        assert hashlib.sha256(data).hexdigest()==item['sha256']
    text=(HERE/'claim_to_evidence.txt').read_text(encoding='utf-8')
    used=set(re.findall(r'\bE_[A-Z0-9_]+\b',text))
    assert used<=set(by_id),sorted(used-set(by_id))
    claims=re.findall(r'^C(\d{2})\.',text,re.MULTILINE)
    assert claims==[f'{x:02d}' for x in range(1,11)]
    matrix=json.loads((HERE/'theorem_source_matrix.json').read_text(encoding='utf-8'))
    sources={x['id']:x for x in matrix['sources']}
    assert sources['S_RUMP_PENDING']['source_file_sha256'] is None
    assert sources['S_RUMP_PENDING']['exact_premises'] is None
    assert sources['S_RUMP_PENDING']['exact_conclusion'] is None
    assert sources['S_RUMP_PENDING']['direct_substitution_applicability']=='UNKNOWN'
    archived=json.loads((REPO/by_id['E_SOURCE_RECORDS']['path']).read_text())
    old_sources={x['logical_file']:x for x in archived['sources']}
    for value in (sources['S_ROUX']['pdf'],sources['S_ROUX']['text'],sources['S_SAIKI']['html']):
        old=old_sources[value['logical_file']]
        assert value['sha256']==old['sha256'] and value['bytes']==old['bytes']
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['new_arithmetic_evaluations']==protocol['new_enumerations']==0
    assert protocol['old_checkers_or_scans_to_execute']==[]
    manifest=HERE/'payload_manifest.json'
    if manifest.exists():
        for item in json.loads(manifest.read_text())['files']:
            path=(HERE/item['path']).resolve()
            assert path.is_relative_to(HERE)
            data=path.read_bytes()
            assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
    return dict(status='PASS_REVIEW_IDENTITIES_AND_REFERENCE_COVERAGE',
                evidence_files=len(entries),claims=len(claims),theorem_source_records=len(sources),
                new_arithmetic_evaluations=0,new_enumerations=0,research_modules_imported=0,
                limitation='Identity/reference checks are not a new verification of the mathematical proofs or publication novelty')


if __name__=='__main__':print(json.dumps(verify(),indent=2))
