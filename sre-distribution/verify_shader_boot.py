"""Boot the client with mods only (no resource packs) to prove shader assets live in the JAR.

The earlier verification enabled the external packs, which hid the defect: a client that does
not enable them could not find Mega's core shaders and died during shader reload.
"""
from pathlib import Path
import os, shutil, subprocess, sys
sys.path.insert(0, os.environ['PI_SCRATCH_DIR'])
from distribution_env import ROOT, CACHE, MINECRAFT, CLASSPATH, WORKSPACE, API, argfile

SUITE = Path('H:/pi/data/scratch/52a41f9c-b48c-4c2b-a60d-dd0f4fafe637/cobblemon-addon-suite-v4')
CORE = 'Cobblemon-fabric-1.8.4+1.21.1.jar'
OLD_MEGA = Path('H:/pi/data/scratch/52a41f9c-b48c-4c2b-a60d-dd0f4fafe637/addon-variants/mega-showdown/client/mega_showdown-fabric-1.3.3+1.8.4+1.21.1-release.jar')
NEW_MEGA = SUITE / 'client' / 'mega_showdown-fabric-1.3.3+1.8.4+1.21.1-release.jar'


def run(label, mega):
    game = ROOT / label
    assert not game.exists(), game
    (game / 'mods').mkdir(parents=True)
    for jar in sorted((SUITE / 'client').glob('*.jar')):
        if jar.name.startswith('mega_showdown'):
            continue
        shutil.copy2(jar, game / 'mods' / jar.name)
    shutil.copy2(mega, game / 'mods' / mega.name)
    shutil.copy2(API, game / 'mods' / API.name)
    natives = (WORKSPACE / '.gradle/loom-cache/natives').as_posix()
    java = ['-Xmx3G', '-Dfile.encoding=UTF-8', '-Dfabric.development=false',
            '-Dfabric.gameJarPath=' + MINECRAFT.as_posix(),
            '-Djava.library.path=' + natives, '-Dorg.lwjgl.librarypath=' + natives,
            '-cp', CLASSPATH, 'net.fabricmc.loader.impl.launch.knot.KnotClient',
            '--username', 'TrainVerify', '--uuid', '00000000000000000000000000000002',
            '--accessToken', '0', '--version', '1.21.1', '--userType', 'legacy',
            '--gameDir', game.as_posix(), '--assetsDir', (CACHE / 'fabric-loom/assets').as_posix(),
            '--assetIndex', '1.21.1-17', '--width', '640', '--height', '360']
    log = ROOT / f'{label}.log'
    with log.open('wb') as out:
        process = subprocess.Popen(['java', argfile(label + '.args', java)], cwd=game,
                                   stdout=out, stderr=subprocess.STDOUT)
        try:
            process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=30)
    text = log.read_text(encoding='utf-8', errors='replace')
    shader_crash = ('could not reload shaders' in text
                    or 'FileNotFoundException: mega_showdown:shaders' in text
                    or 'Invalid shaders/core/tera_crystal' in text)
    started = 'Sound engine started' in text or 'Stopping!' in text or 'Created: 1024x' in text
    print(f'{label}: exit={process.returncode} shaderCrash={shader_crash} started={started}')
    return shader_crash, started


def main():
    old_crash, _ = run('shader-old-nopack', OLD_MEGA)
    new_crash, new_ok = run('shader-new-nopack', NEW_MEGA)
    assert old_crash, 'old packaging should reproduce the missing core shader crash'
    assert not new_crash and new_ok, 'new packaging must boot without external packs'
    print('SHADER_PACKAGING_REGRESSION_PROVEN')


if __name__ == '__main__':
    main()
