"""FILE MODEL ONLY: interruption/compare-before-restore design, not an OEM installer.

The native writer, notifications, wallpaper service and access checks are unresolved.
This module intentionally has no ADB, shell, Android paths, or production adapter.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path


def digest(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.pending')
    with temp.open('w', encoding='utf-8', newline='\n') as output:
        json.dump(value, output, sort_keys=True)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    os.replace(temp, path)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def plan(before, owned_id, resource, after_current, after_wallpaper):
    if not owned_id.startswith('flippets-charlie-') or owned_id in before['resources']:
        raise ValueError('A new owned resource is required')
    states = [deepcopy(before)]
    # Values are opaque exact bytes/metadata supplied by the test fixture.
    for operation in ('copy', 'current', 'history', 'wallpaper'):
        state = deepcopy(states[-1])
        if operation == 'copy':
            state['resources'][owned_id] = deepcopy(resource)
        elif operation == 'current':
            state['current'] = deepcopy(after_current)
        elif operation == 'history':
            state['history'] = [deepcopy(after_current)] + state['history'][:9]
        else:
            state['wallpaper'] = deepcopy(after_wallpaper)
        states.append(state)
    hashes = [digest(state) for state in states]
    if len(set(hashes)) != len(hashes):
        raise ValueError('Every model phase must have distinguishable exact state')
    return dict(schemaVersion=1, scope='offline-file-model-only', ownedId=owned_id,
                states=states, stateHashes=hashes, pending=None, direction='apply',
                complete=False, nativeApplyAllowed=False)


def validate(receipt):
    if receipt.get('schemaVersion') != 1 or receipt.get('scope') != 'offline-file-model-only':
        raise ValueError('Unknown model receipt')
    if receipt.get('nativeApplyAllowed') is not False:
        raise ValueError('No native writer is implemented')
    if receipt['stateHashes'] != [digest(s) for s in receipt['states']]:
        raise ValueError('Receipt snapshots are corrupt')


def advance(state_path, receipt_path, direction, interrupt=None):
    """One model phase. `interrupt` can emulate death before/after state replace."""
    receipt = read(receipt_path)
    validate(receipt)
    current = read(state_path)
    current_hash = digest(current)
    if current_hash not in receipt['stateHashes']:
        raise ValueError('Unknown/later manual state: preserve it, do not restore or delete')
    index = receipt['stateHashes'].index(current_hash)
    if direction not in ('apply', 'restore'):
        raise ValueError('Unknown direction')
    target_index = index + (1 if direction == 'apply' else -1)
    if not 0 <= target_index < len(receipt['states']):
        receipt.update(pending=None, direction=direction, complete=True)
        atomic_json(receipt_path, receipt)
        return False
    target = receipt['states'][target_index]
    # Removing even our own resource is forbidden while any restored selection/history references it.
    if receipt['ownedId'] in current['resources'] and receipt['ownedId'] not in target['resources']:
        references = [target['current']] + target['history'] + [target['wallpaper']]
        if any(receipt['ownedId'] in json.dumps(value, sort_keys=True) for value in references):
            raise ValueError('Owned resource remains referenced')
    receipt.update(pending=dict(before=current_hash, after=digest(target)), direction=direction, complete=False)
    atomic_json(receipt_path, receipt)
    if interrupt == 'before-state':
        return True
    # A real adapter needs external serialization/versioning here. This file model does not prove it.
    if digest(read(state_path)) != current_hash:
        raise ValueError('Concurrent state change: stop')
    atomic_json(state_path, target)
    if interrupt == 'after-state':
        return True
    receipt['pending'] = None
    atomic_json(receipt_path, receipt)
    return True
