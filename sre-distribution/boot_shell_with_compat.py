"""Boot the real 其余列车服务器更新mod jar set against the registry-only shell."""
from pathlib import Path
import os, shutil, subprocess, sys
sys.path.insert(0, os.environ['PI_SCRATCH_DIR'])
from distribution_env import ROOT, prepare_server, server_args, argfile

FOLDER = Path('C:/Users/canyuesama/Desktop/待更新/其余列车服务器更新mod')
CORE = 'Cobblemon-fabric-1.8.4+1.21.1.jar'
label = sys.argv[1] if len(sys.argv) > 1 else 'shell-boot'

game = prepare_server(label, FOLDER / CORE, ROOT / 'distribution-probe.jar')
for jar in sorted(FOLDER.glob('*.jar')):
    if jar.name != CORE:
        shutil.copy2(jar, game / 'mods' / jar.name)
output = ROOT / f'{label}.json'
log = ROOT / f'{label}.log'
with log.open('wb') as stream:
    result = subprocess.run(['java', argfile(label + '.args', server_args(game, [
        '-Dtrain.registry.output=' + output.as_posix(), '-Dtrain.probe.stop=true']))],
        cwd=game, stdout=stream, stderr=subprocess.STDOUT, timeout=420)
text = log.read_text(encoding='utf-8', errors='replace')
print('\n'.join(text.splitlines()[-45:]))
fatal = [line for line in text.splitlines() if 'target missing' in line or 'MixinApplyError' in line]
assert not fatal, fatal[:5]
assert result.returncode == 0 and 'TRAIN_REGISTRY_DUMP_PASS' in text, (result.returncode, log)
print('SHELL_BOOT_PASS', output)
