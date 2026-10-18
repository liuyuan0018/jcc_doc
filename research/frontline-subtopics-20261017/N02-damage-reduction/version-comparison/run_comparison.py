"""Select a reduction parameter version and run the existing native simulator."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(selection_path, profiles_path):
    selection = read(selection_path)
    profiles = read(profiles_path)
    requested = selection['damageReductionVersion']
    version = profiles['latest'] if requested == 'latest' else requested
    if version not in profiles['versions']:
        raise ValueError(f'Unknown damageReductionVersion: {requested}')
    parameters = profiles['versions'][version]
    for rate in [*parameters['juggernautMemberReduction'].values(), parameters['ordinarySpiritVisageReduction']]:
        if type(rate) not in (int, float) or not 0 <= rate < 1:
            raise ValueError('Reduction rates must be numeric fractions in [0,1)')
    base_path = (selection_path.parent / selection['battleInput']).resolve()
    base = read(base_path)
    battle = copy.deepcopy(base)
    changes = []

    def replace(definition, rate, kind):
        # Keep the existing engine representation; this adapter does not fix its semantics.
        channel = definition['properties']['damageReduction']
        if len(channel) != 1 or next(iter(channel)) not in ('add', 'set'):
            raise ValueError('Unsupported reduction representation: ' + str(channel))
        mode = next(iter(channel))
        previous = channel[mode]
        channel[mode] = rate
        changes.append(dict(kind=kind, id=definition['id'], channel=mode, before=previous, after=rate))

    buffs = {x['id']: x for x in battle['catalog']['buffs']}
    for tier, rate in parameters['juggernautMemberReduction'].items():
        key = profiles['memberBuffIdPrefix'] + tier
        if key in buffs:
            replace(buffs[key], rate, 'buff')
    six = profiles['memberBuffIdPrefix'] + '6'
    if six not in buffs:
        raise ValueError('This N02 comparison requires the expanded six-Juggernaut member buff')
    equipment = {x['id']: x for x in battle['catalog']['equipment']}
    item = profiles['ordinaryItemId']
    if item not in equipment:
        raise ValueError('This N02 comparison requires expanded ordinary Spirit Visage equipment')
    replace(equipment[item], parameters['ordinarySpiritVisageReduction'], 'equipment')
    battle['id'] = 'n02-reduction-' + version
    battle['isFixture'] = True
    provenance = dict(requestedVersion=requested, resolvedVersion=version, scope=profiles['scope'],
                      parameters=parameters, profileSha256=sha(profiles_path),
                      baseBattle=str(base_path), baseBattleSha256=sha(base_path), changes=changes,
                      semantics='existing engine unchanged; known reduction and Vi timing issues retained')
    return battle, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='JSON with damageReductionVersion and battleInput')
    parser.add_argument('--profiles', type=Path, default=ROOT/'reduction-versions.json')
    parser.add_argument('--binary', type=Path, required=True, help='Existing jcc-server executable')
    parser.add_argument('--output', type=Path, required=True, help='A new output directory')
    args = parser.parse_args()
    battle, provenance = resolve(args.input.resolve(), args.profiles.resolve())
    binary = args.binary.resolve()
    if not binary.is_file():
        raise FileNotFoundError(binary)
    args.output.mkdir(parents=True, exist_ok=False)
    input_path = args.output/'battle.json'
    replay_path = args.output/'replay.json'
    save(input_path, battle)
    provenance.update(createdAt=datetime.now(timezone.utc).isoformat(), binary=str(binary),
                      binarySha256=sha(binary), inputSha256=sha(input_path))
    completed = subprocess.run([str(binary), str(input_path), str(replay_path)], capture_output=True, text=True)
    provenance.update(exitCode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
    if completed.returncode == 0:
        replay = read(replay_path)
        provenance.update(replaySha256=sha(replay_path), runtimeSourceHash=replay['sourceHash'],
                          compiledBalanceVersion=replay['balanceVersion'], compiledBalanceHash=replay['balanceHash'],
                          result=replay['result'], use='diagnostic only; not yet a gameplay conclusion')
    save(args.output/'run-manifest.json', provenance)
    print(json.dumps(dict(requested=provenance['requestedVersion'], resolved=provenance['resolvedVersion'],
                          exitCode=completed.returncode, output=str(args.output)), ensure_ascii=False))
    raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
