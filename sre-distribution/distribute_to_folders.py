"""Distribute the verified addon suite into the three existing 待更新 folders.

Additive only: never overwrites a different file, and every copy is hash-verified.
"""
from pathlib import Path
import hashlib, json, shutil

DESKTOP = Path('C:/Users/canyuesama/Desktop/待更新')
SUITE = Path('H:/pi/data/scratch/52a41f9c-b48c-4c2b-a60d-dd0f4fafe637/cobblemon-addon-suite')
CORE = 'Cobblemon-fabric-1.8.4+1.21.1.jar'
MAP = {
    'client': '客户端更新mod',
    'server-shell': '其余列车服务器更新mod',
    'server-full': '哈比生存服务器更新mod',
}

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    record = {}
    for variant, folder in MAP.items():
        source = SUITE / variant
        target = DESKTOP / folder
        assert target.is_dir(), target
        jars = sorted(source.glob('*.jar'))
        assert any(j.name == CORE for j in jars), (variant, 'core jar missing')
        entries = []
        for jar in jars:
            destination = target / jar.name
            if destination.exists():
                assert digest(destination) == digest(jar), f'refusing to overwrite {destination}'
                entries.append({'name': jar.name, 'sha256': digest(jar), 'action': 'unchanged'})
                continue
            shutil.copy2(jar, destination)
            assert digest(destination) == digest(jar), destination
            entries.append({'name': jar.name, 'sha256': digest(jar), 'bytes': destination.stat().st_size, 'action': 'added'})
        record[folder] = {'variant': variant, 'coreJar': CORE, 'files': entries}
        print(folder, variant, len(entries), 'jars')
    (DESKTOP / 'Cobblemon-1.8.4' / 'distribution-locations.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: len(v['files']) for k, v in record.items()}, ensure_ascii=False))

if __name__ == '__main__':
    main()
