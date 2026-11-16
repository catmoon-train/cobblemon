"""Isolate the mixin-preparation crash: same shell stack, old vs fixed sre-pokemon-compat.

The jar copy is patched only in the test sandbox (drop the external SRE hard dependency and
entrypoints) so the mixin-plugin path can run without the whole train modpack.
"""
from pathlib import Path
import json, os, shutil, subprocess, sys, zipfile
sys.path.insert(0, os.environ['PI_SCRATCH_DIR'])
from distribution_env import ROOT, prepare_server, server_args, argfile

DESKTOP = Path('C:/Users/canyuesama/Desktop/待更新')
SHELL_FOLDER = DESKTOP / '其余列车服务器更新mod'
BACKUP = Path('G:/download/cobblemon-main (1)/cobblemon-main/sre-distribution/local-backups/sre-pokemon-compat-before-shell-fix/其余列车服务器更新mod-sre-pokemon-compat-1.0.0.jar')
FIXED = Path('G:/exmo/StarRailExpress2/StarRailExpress/sre-pokemon-compat/build/libs/sre-pokemon-compat-1.0.0.jar')
CORE = 'Cobblemon-fabric-1.8.4+1.21.1.jar'

SHELL_MODS = ['mega_showdown-fabric-1.3.3+1.8.4+1.21.1-release.jar',
              'cobblenav-fabric-2.4.2.jar',
              'cobblemon_spawn_notification-fabric-1.5-fabric-1.2.1.jar']


def sandbox_jar(source, target):
    """Drop SRE hard dependency + entrypoints so only mixin plugins are exercised."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == 'fabric.mod.json':
                meta = json.loads(data)
                meta['depends'].pop('starrailexpress', None)
                meta['entrypoints'] = {}
                data = json.dumps(meta, indent=2).encode()
            dst.writestr(info.filename, data)
    return target


def run(label, compat_jar):
    game = prepare_server(label, SHELL_FOLDER / CORE, ROOT / 'distribution-probe.jar')
    for name in SHELL_MODS:
        shutil.copy2(SHELL_FOLDER / name, game / 'mods' / name)
    shutil.copy2(compat_jar, game / 'mods' / 'sre-pokemon-compat-1.0.0.jar')
    log = ROOT / f'{label}.log'
    with log.open('wb') as stream:
        result = subprocess.run(['java', argfile(label + '.args', server_args(game, [
            '-Dtrain.registry.output=' + (ROOT / f'{label}.json').as_posix(),
            '-Dtrain.probe.stop=true']))], cwd=game, stdout=stream, stderr=subprocess.STDOUT, timeout=420)
    text = log.read_text(encoding='utf-8', errors='replace')
    crash = 'compatibility target missing' in text
    started = 'TRAIN_REGISTRY_DUMP_PASS' in text
    print(f'{label}: exit={result.returncode} mixinCrash={crash} started={started}')
    return crash, started


def main():
    old = sandbox_jar(BACKUP, ROOT / 'compat-sandbox' / 'old' / 'sre-pokemon-compat-1.0.0.jar')
    new = sandbox_jar(FIXED, ROOT / 'compat-sandbox' / 'fixed' / 'sre-pokemon-compat-1.0.0.jar')
    old_crash, _ = run('compat-old', old)
    new_crash, new_started = run('compat-fixed', new)
    assert old_crash, 'old jar should reproduce the reported crash'
    assert not new_crash and new_started, 'fixed jar must boot the shell server'
    print('REGRESSION_PROVEN old crashed, fixed boots')


if __name__ == '__main__':
    main()
