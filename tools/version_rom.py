"""Preserve distinct ROM builds and their validation evidence without overwriting ROMs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from update_readme import refresh_readme_release

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'gaw-megadrive.bin')
    parser.add_argument('--notes', default='Compilation ; validation en attente.')
    parser.add_argument('--report', type=Path, action='append', default=[])
    args = parser.parse_args()
    data = args.source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    reports = []
    for path in args.report:
        raw = path.read_bytes()
        assert json.loads(raw)['md_sha256'] == digest, f'Report belongs to another ROM: {path}'
        reports.append((path.name, raw))
    archive = ROOT / 'versions'
    archive.mkdir(exist_ok=True)
    index = archive / 'index.json'
    entries = json.loads(index.read_text(encoding='utf-8')) if index.exists() else []
    entry = next((e for e in entries if e['sha256'] == digest), None)
    if entry is None:
        version = max((e['version'] for e in entries), default=0) + 1
        folder = archive / f'v{version:04d}-{digest[:8]}'
        folder.mkdir()
        target = folder / f'gaw-megadrive-v{version:04d}.bin'
        with target.open('xb') as stream:
            stream.write(data)
        entry = dict(version=version, sha256=digest, bytes=len(data),
                     archived_utc=datetime.now(timezone.utc).isoformat(),
                     rom=str(target.relative_to(archive)).replace('\\', '/'),
                     notes=args.notes, validation='build_only', reports=[])
        entries.append(entry)
    target = archive / entry['rom']
    assert target.read_bytes() == data, 'Archived ROM must never be overwritten'
    for name, raw in reports:
        dest = target.parent / name
        if dest.exists():
            assert dest.read_bytes() == raw, f'Existing evidence differs: {dest}'
        else:
            with dest.open('xb') as stream:
                stream.write(raw)
        item = dict(file=name, sha256=hashlib.sha256(raw).hexdigest())
        if item not in entry['reports']:
            entry['reports'].append(item)
    if reports:
        entry['validation'] = 'targeted_checks_passed'
        entry['notes'] = args.notes
    temp = archive / 'index.json.tmp'
    temp.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temp.replace(index)
    lines = ['# Versions des ROMs', '',
             'Chaque binaire est conserve sans ecrasement. Les controles cibles ne prouvent pas un portage complet.', '',
             '| Version | ROM | Validation | Changements | SHA-256 |',
             '| --- | --- | --- | --- | --- |']
    for e in reversed(entries):
        notes = e['notes'].replace('|', '/').replace('\n', ' ')
        lines.append(f"| v{e['version']:04d} | [Telecharger]({e['rom']}) | {e['validation']} | {notes} | `{e['sha256']}` |")
    (archive / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    refresh_readme_release(ROOT, entry)
    print(f"ROM v{entry['version']:04d}: {target} ({entry['validation']})")


if __name__ == '__main__':
    main()
