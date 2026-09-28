#!/usr/bin/env python3
"""Stage verified dual-rank images and text on the external publish volume."""

from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
import os
import shutil


ROOT = Path(__file__).resolve().parents[2]
PUBLISH = ROOT / 'publish'
DOC = PUBLISH / 'doc'
EXTERNAL = Path('/Volumes/Apple')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--replace-date', action='store_true',
                        help='Replace only the same-date files staged by an earlier run')
    args = parser.parse_args()
    package = args.package.resolve()
    manifest = json.loads((package / 'manifest.json').read_text())
    checks = json.loads((package / 'checks.json').read_text())
    if manifest.get('test_fixture') or not checks.get('ok') or checks.get('visual_status') != 'checks_passed_needs_visual_check':
        raise SystemExit('Package must pass non-fixture verification before staging')
    if not EXTERNAL.is_mount() or not PUBLISH.is_symlink() or not PUBLISH.resolve().is_relative_to(EXTERNAL):
        raise SystemExit('External publish volume is not mounted at the expected path')
    if not os.access(PUBLISH, os.W_OK):
        raise SystemExit('External publish directory is not writable')

    _, month, day_number = (int(part) for part in manifest['date'].split('-'))
    day = f'{month}.{day_number}'
    outputs = []
    stage = []
    for note in manifest['notes']:
        key = note['key']
        label = {'regular': '阵容榜', 'cold': '冷门榜'}[key]
        upload = DOC / f'{label}{day}'
        files = []
        for image in note['images']:
            source = Path(image['file'])
            if digest(source) != image['png_sha256']:
                raise SystemExit('Image changed after verification: ' + str(source))
            name = source.name
            files.append((source, upload / name))
        body = Path(note['body_file'])
        if digest(body) != note['body_sha256']:
            raise SystemExit('Body changed after verification: ' + str(body))
        files.extend([(body, DOC / f'{label}{day}-正文.txt')])
        title_file = package / f'{key}-title.txt'
        if title_file.read_text().strip() != note['title']:
            raise SystemExit('Title changed after verification: ' + str(title_file))
        files.extend([(title_file, DOC / f'{label}{day}-标题.txt')])

        for source, target in files:
            if target.exists() and digest(target) != digest(source) and not args.replace_date:
                raise SystemExit('Same-date file exists; review before --replace-date: ' + str(target))
        stage.append((upload, files))
        outputs.append({'key': key, 'images': len(note['images']), 'upload_folder': str(upload),
                        'text_prefix': str(DOC / f'{label}{day}')})

    for upload, files in stage:
        upload.mkdir(parents=True, exist_ok=True)
        expected = {target.name for _, target in files if target.parent == upload}
        stale = [old for old in upload.iterdir() if old.name not in expected]
        if stale and not args.replace_date:
            raise SystemExit('Unexpected files in upload folder: ' + str(upload))
        if any(not old.is_file() for old in stale):
            raise SystemExit('Unexpected directory in upload folder: ' + str(upload))
        for source, target in files:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.new')
            shutil.copyfile(source, temporary)
            os.replace(temporary, target)
            if digest(target) != digest(source):
                raise SystemExit('Staged copy failed verification: ' + str(target))
        for old in stale:
            old.unlink()
    print(json.dumps({'date': manifest['date'], 'package': str(package), 'outputs': outputs}, ensure_ascii=False))


if __name__ == '__main__':
    main()
