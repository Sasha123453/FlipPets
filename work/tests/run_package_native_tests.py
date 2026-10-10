"""Reject incomplete, duplicated or foreign native cases at the publication gate."""
from pathlib import Path
import copy
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'work'))
import package_release as package

current = json.loads((ROOT / 'work/qa-final/native-cards/native-cards-qa.json').read_text(encoding='utf-8'))
rows = []
package.native_qa_cases(current, 31)
rows.append(dict(test='real_current_report', ok=True))
for name, change, count in [
    ('duplicate_case', lambda d: d['results'].__setitem__(0, d['results'][1]), 31),
    ('foreign_case', lambda d: d['results'][0].update(test='unrelated_passing_case'), 31),
    ('missing_case', lambda d: d['results'].pop(), 31),
    ('wrong_expected_count', lambda d: None, 30),
]:
    data = copy.deepcopy(current)
    change(data)
    try:
        package.native_qa_cases(data, count)
        passed = False
    except ValueError:
        passed = True
    rows.append(dict(test=name, ok=passed))
assert all(row['ok'] for row in rows), rows
result = dict(environment='Host-only publication gate checks using current report plus deliberately invalid copies',
              source_sha256={str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (ROOT / 'work/package_release.py', ROOT / 'work/tests/native_apps_contract.py')},
              tested=len(rows), failed=0, results=rows)
(ROOT / 'work/qa-final/native-package-guards.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print('5 native publication gate checks passed')
