"""Write release metadata: hashes, provenance summary and verification evidence for the addon suite."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess

def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('suite', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    args = parser.parse_args()
    suite, source, scratch = args.suite, args.source, args.scratch
    repo = 'G:/download/cobblemon-main (1)/cobblemon-main'
    base = 'b79dbcca802e10fb7eda89c568a874f7891a2d28'
    workspace_head = subprocess.check_output(['git', '-C', repo, 'rev-parse', 'HEAD'], text=True).strip()
    import zipfile
    client_jar = next((suite / 'client').glob('Cobblemon-fabric-*.jar'))
    with zipfile.ZipFile(client_jar) as archive:
        gitinfo = archive.read('cobblemon-git.properties').decode('utf-8')
    commit = next(line.split('=', 1)[1].strip() for line in gitinfo.splitlines() if line.startswith('commit='))
    assert subprocess.run(['git', '-C', repo, 'merge-base', '--is-ancestor', base, commit]).returncode == 0
    verification = suite / 'verification'
    verification.mkdir(exist_ok=True)
    for name, target in [
        ('addons-release-pairs-run.log', 'addons-release-pairs-run.log'),
        ('pair-addons-release-shell-verification.json', 'pair-addons-release-shell-verification.json'),
        ('pair-addons-release-full-verification.json', 'pair-addons-release-full-verification.json'),
        ('pair-addons-release-shell-client.log', 'pair-addons-release-shell-client.log'),
        ('pair-addons-release-shell-server.log', 'pair-addons-release-shell-server.log'),
        ('pair-addons-release-full-client.log', 'pair-addons-release-full-client.log'),
        ('pair-addons-release-full-server.log', 'pair-addons-release-full-server.log'),
        ('registry-addons-runtime-riding-run.log', 'addon-runtime-probe.log'),
        ('registry-addons-runtime-riding.json', 'runtime-registry-snapshot.json'),
        ('cobblemon-riding-build.log', 'cobblemon-build.log'),
        ('cobblenav-build.log', 'cobblenav-build.log'),
        ('mega-riding-build.log', 'mega-showdown-build.log'),
        ('spawn-notification-compile.log', 'spawn-notification-build.log'),
    ]:
        path = scratch / name
        if path.is_file():
            shutil.copy2(path, verification / target)
    for name in ['cobblemon-git.properties']:
        pass
    pairs = {}
    for variant in ['shell', 'full']:
        record = verification / f'pair-addons-release-{variant}-verification.json'
        assert record.is_file(), record
        pairs[variant] = json.loads(record.read_text(encoding='utf-8'))
        assert pairs[variant]['passed'] is True
    runtime = (verification / 'addon-runtime-probe.log').read_text(encoding='utf-8', errors='replace')
    assert 'TRAIN_ADDON_RUNTIME_PASS ridingSpecies=47 nativeSyncRoundtrips=47 navItems=29 notificationCases=3' in runtime
    assert 'TRAIN_LEGACY_CONFIG_PASS repeats=2 speed=1.25 offsetXYZ=0.3,1.4,0.2' in runtime
    assert 'LEGACY_CONFIG_UNCHANGED_PASS' in runtime
    addons = {}
    for name in ['mega-showdown', 'cobblenav', 'spawn-notification']:
        addons[name] = json.loads((suite / 'addon-manifests' / f'{name}.json').read_text(encoding='utf-8'))
    summary = {
        'cobblemon': {'upstreamBaseCommit': base, 'buildCommit': commit, 'workspaceHead': workspace_head,
                      'version': '1.8.4+1.21.1',
                      'ridingFixes': {'legacySpeciesTargets': 47, 'mergedNativeData': True}},
        'addons': {name: {'version': data['version'], 'preservedClasses': data['preservedClasses'],
                          'shellRegistries': data['shellRegistries'],
                          'retainedRuntimeResources': data.get('retainedRuntimeResources', [])}
                   for name, data in addons.items()},
        'pairs': {variant: {'registries': record['clientRegistries'], 'clientResult': record['clientResult'],
                            'serverHeap': record['serverHeapLimit'], 'elapsedSeconds': record['elapsedSeconds']}
                  for variant, record in pairs.items()},
        'runtimeProbe': {
            'ridingSpeciesChecked': 47,
            'nativeSyncRoundtrips': 47,
            'cobblenavItems': 29,
            'notificationCases': ['ordinary-silent', 'shiny', 'legendary'],
            'legacyConfig': 'imported twice, no multiplier compounding, original file unchanged, invalid entries skipped',
        },
        'notVerified': [
            'Actual riding input/physics, seat visuals and dual-rider camera in a real GUI session',
            'Mega evolution battle flow, all Mega/Gmax items and animations beyond registry/model loading',
            'Cobblenav screens and fishing navigation interaction beyond server load and item registration',
            'Spawn notification delivery to real players, cross-dimension routing and audible sound',
            'Long-running train modpack combination, old Pokemon saves on the shell, or addon APIs on the shell',
        ],
    }
    (verification / 'addons-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = []
    for path in sorted(p for p in suite.rglob('*') if p.is_file()):
        relative = path.relative_to(suite).as_posix()
        if relative.startswith('verification/') or relative == 'SHA256SUMS.txt':
            continue
        lines.append(f'{digest(path)}  {relative}')
    (suite / 'SHA256SUMS.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'files': len(lines), 'buildCommit': commit, 'workspaceHead': workspace_head, 'addons': list(addons)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
