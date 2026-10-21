"""Verify completed import identities and internal receipts without rerunning it."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent

def main():
    manifest = json.loads((ROOT / 'payload_manifest.json').read_text())
    for entry in manifest['files']:
        path = (ROOT / entry['path']).resolve()
        if not path.is_relative_to(ROOT):
            raise SystemExit('Unsafe import manifest path')
        data = path.read_bytes()
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise SystemExit('Import identity mismatch: ' + entry['path'])
    provenance = json.loads((ROOT / 'import_provenance.json').read_text())
    for entry in provenance['copied_files']:
        data = (ROOT / entry['path']).read_bytes()
        assert len(data) == entry['bytes']
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
    results = json.loads((ROOT / 'results.json').read_text())
    direct = json.loads((ROOT / 'direct_validation.json').read_text())
    failures = json.loads((ROOT / 'p53_counterexamples.json').read_text())
    assert sum(s['pairs'] for s in results['summaries']) == 8242261
    assert results['independent_checks'] == 24159
    assert direct['total_RNE_evaluations'] == 3105916
    assert failures['record_count'] == len(failures['records']) == 37
    assert sum(c['b'] == 38 for c in failures['records']) == 9
    assert all(c['kind'] == 'subnormal' for c in failures['records'])
    b32 = next(s for s in results['summaries'] if s['b'] == 32)
    assert b32['kinds']['normal']['first_safe_p_in_tested_region'] == 45
    assert b32['kinds']['subnormal']['first_safe_p_in_tested_region'] == 49
    assert provenance['actual_experiment_source_git_commit'] is None
    assert provenance['scientific_experiment_rerun'] is False
    assert provenance['original_archive']['b2_file_id'] is None
    print('PASS: imported file identities and completed arithmetic receipts; no experiment rerun.')

if __name__ == '__main__':
    main()
