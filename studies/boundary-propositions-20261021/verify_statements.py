"""Check the statement/certificate links without rerunning the large scans."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / 'precision-boundaries-20261021'

def main():
    old = json.loads((PRIOR/'direct_validation.json').read_text())
    new = json.loads((ROOT/'targeted_results.json').read_text())
    units = json.loads((ROOT/'statement_certificate.json').read_text())
    assert new['protocol_sha256'] == hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest()
    assert new['source_sha256'] == hashlib.sha256((ROOT/'targeted_reference.py').read_bytes()).hexdigest()
    for spec in units['inherited_positive_cells']:
        row = next(r for r in old['rows'] if all(r[k] == spec[k] for k in ('b','p','kind')))
        assert row['pairs'] == spec['pairs'] and row['mismatches'] == 0
    expected = [(48755,5,492,199),(29645,1,242,221),(152,3,16,4)]
    for prefix, (count,failures,a,x) in zip(new['prefixes'],expected):
        assert prefix['evaluations'] == count and prefix['mismatches'] == failures
        witness = prefix['first_failure']
        assert (witness['amax_bf16'],witness['x_bf16']) == (a,x)
        assert witness['rounded_base'] == witness['ideal_base']
        assert witness['rounded_T'] == witness['ideal_T'] + 1
        u = witness['ideal_T']
        assert 0 <= u < 1 << witness['b']
        assert (u < witness['ideal_T']) != (u < witness['rounded_T'])
    for index, cut in ((0,45),(1,49)):
        w = new['prefixes'][index]['first_failure']
        rows = [r for r in new['precision_checks'] if (r['amax_bf16'],r['x_bf16']) == (w['amax_bf16'],w['x_bf16'])]
        assert len(rows) == 30 and all(r['mismatch'] == (r['p'] < cut) for r in rows)
    assert new['total_prefix_evaluations'] == 78552
    assert new['independent_midpoint_checks'] == 195
    assert new['scale_checks'] == 340
    assert len(new['precision_checks']) == 84 and len(new['zero_checks']) == 3
    assert new['assertion_status'] == 'PASS'
    assert all(not z['mismatch'] for z in new['zero_checks'])
    for entry in units['inherited_file_identities']:
        data = (PRIOR/entry['path']).read_bytes()
        assert len(data) == entry['bytes'] and hashlib.sha256(data).hexdigest() == entry['sha256']
    print('PASS: statement units, inherited identities, minimal witnesses and precision checks; no large scan rerun.')

if __name__ == '__main__':
    main()
