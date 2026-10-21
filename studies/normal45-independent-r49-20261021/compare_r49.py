"""Compare frozen independent direct-j output with the prior residue certificate."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent/'r49-audit-20261021'
INDEPENDENT = ROOT/'independent'


def read_csv(path):
    with path.open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))


def compare():
    frozen = json.loads((INDEPENDENT/'freeze_manifest.json').read_text())
    assert frozen['enumeration_runs'] == 1
    assert frozen['comparison_against_old_results_performed'] is False
    for item in frozen['files']:
        path = INDEPENDENT/item['logical_filename']
        if item['retention'] == 'ARCHIVE_ONLY' and not path.exists():
            continue
        data = path.read_bytes()
        assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
    old_rows = read_csv(OLD/'coefficient_ledger.csv')
    new_rows = read_csv(INDEPENDENT/'all_coefficient_t_branches.csv')
    key = lambda r: tuple(int(r[x]) for x in ('q','A','t'))
    old = {key(r): r for r in old_rows}
    new = {key(r): r for r in new_rows}
    issues = []
    if len(old) != len(old_rows) or len(new) != len(new_rows):
        issues.append({'kind':'DUPLICATE_BRANCH'})
    if set(old) != set(new):
        issues.append({'kind':'BRANCH_SET_MISMATCH',
                       'old_only':sorted(set(old)-set(new)),
                       'new_only':sorted(set(new)-set(old))})
    compared, disposition = [], Counter()
    for k in sorted(set(old)&set(new)):
        a,b = old[k],new[k]
        same_fields = all(int(a[x]) == int(b[x]) for x in ('D','epsilon','m','j_cap'))
        old_j = [int(a['j_residue'])] if a['status']=='COARSE_CONGRUENCE_SURVIVOR' else []
        new_j = [int(x) for x in b['survivor_j'].split(';') if x]
        same_survivors = old_j == new_j
        if not same_fields or not same_survivors:
            issues.append({'kind':'BRANCH_VALUE_MISMATCH','branch':k,'old':a,'new':b})
        disposition[a['status']] += 1
        compared.append(dict(q=k[0],A=k[1],t=k[2],parameters_match=same_fields,
                             survivors_match=same_survivors,old_status=a['status'],
                             independent_status=b['status'],independent_checks=b['checks']))
    old_result = json.loads((OLD/'kernel_results.json').read_text())
    fresh = json.loads((INDEPENDENT/'independent_results.json').read_text())
    fields = ('q','A','D','epsilon','t','j','m')
    old_candidates = sorted(tuple(r[x] for x in fields) for r in old_result['coarse_survivors'])
    new_candidates = sorted(tuple(r[x] for x in fields) for r in fresh['coarse_survivors'])
    if old_candidates != new_candidates:
        issues.append({'kind':'SURVIVOR_SET_MISMATCH'})
    old_recon = {(r['v'],r['S']):(r['L'],r['u'],r['numerator'],r['X'])
                 for r in old_result['reconstructions']}
    new_recon = {(r['v'],r['S']):(r['L'],r['u'],r['numerator'],
                 r['X_floor'] if r['X_remainder']==0 else None)
                 for r in fresh['reconstructions']}
    if old_recon != new_recon:
        issues.append({'kind':'RECONSTRUCTION_MISMATCH'})
    if fresh['failures'] or fresh['exact_scale_anomalies']:
        issues.append({'kind':'INDEPENDENT_REPORTED_FAILURE','failures':fresh['failures'],
                       'exact_scale_anomalies':fresh['exact_scale_anomalies']})
    with (ROOT/'r49_branch_comparison.csv').open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=list(compared[0]))
        writer.writeheader();writer.writerows(compared)
    summary = dict(status='PASS_COMPLETE_BRANCH_AND_RECONSTRUCTION_AGREEMENT' if not issues else 'MISMATCH',
                   old_branches=len(old_rows),independent_branches=len(new_rows),
                   compared_branches=len(compared),old_dispositions=dict(disposition),
                   independent_counts=fresh['counts'],coarse_survivors=new_candidates,
                   reconstruction_branches_compared=len(new_recon),
                   mismatches=issues,
                   independent_implementation_prior_exposure_disclosed=True,
                   blind_replication=False,enumeration_runs_in_independent_implementation=1,
                   extra_enumeration_performed_by_comparison=False,
                   epsilon_zero_note='99 relaxed diagnostic congruence hits are excluded by exact-scale divisibility; they are not physical candidates or disagreements',
                   old_ledger_sha256=hashlib.sha256((OLD/'coefficient_ledger.csv').read_bytes()).hexdigest(),
                   independent_freeze_manifest_sha256=hashlib.sha256((INDEPENDENT/'freeze_manifest.json').read_bytes()).hexdigest(),
                   comparison_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (ROOT/'r49_comparison_results.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    if issues:
        raise SystemExit('Preserved mismatch; stop the affected conclusion')


if __name__ == '__main__':
    compare()
