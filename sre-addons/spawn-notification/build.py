#!/usr/bin/env python3
"""Offline, non-incremental JVM 21 build using read-only Cobblemon named outputs.

No Gradle invocation, dependency download or writes into the Cobblemon checkout.
All compiler inputs and commands are recorded in --output for reproduction.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile

SOURCE = Path(__file__).resolve().parent
VERSION = '1.5-fabric-1.2.1'  # Upstream version, deliberately unchanged.


def jars(root, pattern):
    return sorted(p for p in root.glob(pattern) if not p.name.endswith(('-sources.jar', '-javadoc.jar')))


def one(root, pattern):
    found = jars(root, pattern)
    if len(found) != 1:
        raise RuntimeError(f'Expected one {root}/{pattern}, found {found}')
    return found[0]


def main():
    scratch = Path(os.environ.get('PI_SCRATCH_DIR', str(SOURCE.parent)))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cobblemon-build', type=Path, default=scratch/'cobblemon-1.8.4-upstream')
    parser.add_argument('--gradle-home', type=Path, default=Path(os.environ.get('GRADLE_USER_HOME', 'H:/gradle-home')))
    parser.add_argument('--output', type=Path, default=scratch/'spawn-notification-build')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if SOURCE == out or SOURCE in out.parents:
        raise RuntimeError('Use a separate scratch output directory, not the source module')
    out.mkdir(parents=True, exist_ok=True)
    marker = out/'.spawn-notification-build'
    if not marker.exists():
        assert not any(out.iterdir()), f'Refusing to overwrite non-build directory: {out}'
        marker.write_text('spawn-notification\n', encoding='utf-8')
    assert marker.read_text(encoding='utf-8') == 'spawn-notification\n'
    tmp = out/'tmp'
    tmp.mkdir(exist_ok=True)
    env = dict(os.environ, TEMP=str(tmp), TMP=str(tmp), TMPDIR=str(tmp))
    cache = args.gradle_home/'caches/modules-2/files-2.1'
    built = args.cobblemon_build
    common = one(built, 'common/build/devlibs/common-1.8.4+1.21.1-dev.jar')
    minecraft = jars(built, '.gradle/loom-cache/minecraftMaven/net/minecraft/minecraft-merged-*/1.21.1-loom.mappings.1_21_1.layered+hash.652182843-v2/*.jar')[0]
    mappings = args.gradle_home/'caches/fabric-loom/1.21.1/loom.mappings.1_21_1.layered+hash.652182843-v2/mappings.tiny'
    assert mappings.is_file(), mappings
    assert mappings.read_text(encoding='utf-8').splitlines()[0].endswith('official\tintermediary\tnamed')

    def dep(group, artifact, version):
        return one(cache, f'{group}/{artifact}/{version}/*/*.jar')

    stdlib = dep('org.jetbrains.kotlin', 'kotlin-stdlib', '2.2.20')
    loader = dep('net.fabricmc', 'fabric-loader', '0.17.2')
    compile_cp = [minecraft, common, loader, stdlib, dep('org.jetbrains', 'annotations', '23.0.0')]
    minecraft_info = json.loads((args.gradle_home/'caches/fabric-loom/1.21.1/mojang_minecraft_info.json').read_text(encoding='utf-8'))
    library_caches = [cache, Path.home()/'.gradle/caches/modules-2/files-2.1']
    for library in minecraft_info['libraries']:
        rules = library.get('rules', [])
        allowed = not rules
        for rule in rules:
            platform = rule.get('os', {}).get('name')
            if platform is None or platform == ('windows' if os.name == 'nt' else 'linux'):
                allowed = rule['action'] == 'allow'
        if not allowed:
            continue
        artifact = library.get('downloads', {}).get('artifact')
        if artifact is None:
            continue
        group, name, version = library['name'].split(':')[:3]
        filename = Path(artifact['path']).name
        for library_cache in library_caches:
            found = jars(library_cache, f'{group}/{name}/{version}/*/{filename}')
            if found:
                compile_cp.append(found[0])
                break
        else:
            raise RuntimeError(f'Missing cached Minecraft library: {library["name"]}')
    compile_cp.extend(jars(built, 'fabric/build/loom-cache/remapped_working/remapped.net.fabricmc.fabric-api-*-6c7f229b-*.jar'))
    cp = os.pathsep.join(p.as_posix() for p in compile_cp)
    (out/'named-classpath.txt').write_text(cp+'\n', encoding='utf-8')
    compiler_cp = [dep('org.jetbrains.kotlin', 'kotlin-compiler-embeddable', '2.2.20'), stdlib,
                   dep('org.jetbrains.kotlin', 'kotlin-script-runtime', '2.2.20'),
                   dep('org.jetbrains.kotlin', 'kotlin-reflect', '1.6.10'),
                   dep('org.jetbrains.kotlin', 'kotlin-daemon-embeddable', '2.2.20'),
                   dep('org.jetbrains.kotlinx', 'kotlinx-coroutines-core-jvm', '1.8.0'),
                   dep('org.jetbrains', 'annotations', '13.0')]
    java_prefix = ['-Djava.io.tmpdir='+tmp.as_posix(), '-Dfile.encoding=UTF-8']

    def run(tool, name, command):
        argfile = out/(name+'.args')
        argfile.write_text('\n'.join('"'+str(a).replace('\\', '/')+'"' for a in command)+'\n', encoding='utf-8')
        subprocess.run([tool, '@'+argfile.as_posix()], check=True, cwd=out, env=env)

    classes = out/'classes'
    if classes.exists():
        shutil.rmtree(classes)
    classes.mkdir()
    run('javac', 'javac', ['--release', '21', '-proc:none', '-encoding', 'UTF-8', '-cp', cp,
                          '-d', classes.as_posix(), *[p.as_posix() for p in sorted((SOURCE/'src/main/java').rglob('*.java'))]])
    kotlin_prefix = [*java_prefix, '-Xmx1G', '-cp', os.pathsep.join(p.as_posix() for p in compiler_cp),
                     'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler', '-no-stdlib', '-no-reflect', '-jvm-target', '21']
    run('java', 'kotlinc', [*kotlin_prefix, '-classpath', cp, '-d', classes.as_posix(),
                          *[p.as_posix() for p in sorted((SOURCE/'src/main/kotlin').rglob('*.kt'))]])
    named = out/f'spawnnotification-{VERSION}-mc1.21.1-named.jar'
    with zipfile.ZipFile(named, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\nFabric-Mapping-Namespace: named\n\n')
        z.write(SOURCE/'LICENSE', 'LICENSE')
        z.write(SOURCE/'upstream/commit.txt', 'META-INF/spawn-notification-upstream.txt')
        for folder in [classes, SOURCE/'src/main/resources']:
            for p in sorted(folder.rglob('*')):
                if p.is_file():
                    z.write(p, p.relative_to(folder).as_posix())
    # Use Loom's real Kotlin metadata extension as well as bytecode remapping.
    # Auxiliary artifacts are read-only from existing caches, never copied to C:.
    auxiliary = Path.home()/'.gradle/caches/modules-2/files-2.1'
    def build_dep(group, artifact, version):
        pattern = f'{group}/{artifact}/{version}/*/{artifact}-{version}.jar'
        found = jars(cache, pattern) or jars(auxiliary, pattern)
        if len(found) != 1:
            raise RuntimeError(f'Missing cached build tool: {group}:{artifact}:{version}')
        return found[0]
    remap_cp = [build_dep('net.fabricmc', 'tiny-remapper', '0.14.0'),
                build_dep('net.fabricmc', 'mapping-io', '0.8.0'),
                one(cache, 'dev.architectury/architectury-loom/1.11-SNAPSHOT/*/*.jar'),
                build_dep('org.jetbrains.kotlin', 'kotlin-metadata-jvm', '2.2.20'), stdlib]
    remap_cp.extend(build_dep('org.ow2.asm', artifact, '9.10.1') for artifact in ['asm', 'asm-commons', 'asm-tree', 'asm-util', 'asm-analysis'])
    remap_cp.extend(p for p in compile_cp if '/org.slf4j/' in p.as_posix())
    tool_classes = out/'tool-classes'
    tool_classes.mkdir(exist_ok=True)
    tool_cp = os.pathsep.join(p.as_posix() for p in remap_cp)
    run('javac', 'remap-tool-javac', ['--release', '21', '-proc:none', '-encoding', 'UTF-8',
        '-cp', tool_cp, '-d', tool_classes.as_posix(), (SOURCE/'tools/BuildRemap.java').as_posix()])
    target = out/f'spawnnotification-{VERSION}-mc1.21.1.jar'
    if target.exists():
        target.unlink()
    run('java', 'remap', [*java_prefix, '-Xmx1G', '-cp', os.pathsep.join([tool_classes.as_posix(), tool_cp]),
                         'BuildRemap', named.as_posix(), target.as_posix(),
                         mappings.as_posix(), *[p.as_posix() for p in compile_cp]])
    if args.test:
        import sys
        # Test helper is loaded without generating __pycache__ in the source tree.
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(SOURCE/'tests'))
        from verify import verify
        verify(SOURCE, out, target, classes, cp, loader, kotlin_prefix, run)
    report = {'version': VERSION, 'minecraft': '1.21.1', 'cobblemon': '1.8.4',
              'upstream': '21c2359d9246145d15ae06e92ef9b4f105f90d74',
              'artifact': target.as_posix(), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
              'namedClasspath': [p.as_posix() for p in compile_cp], 'tests': 'passed' if args.test else 'not run'}
    (out/'build-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('BUILD_PASS '+target.as_posix())


if __name__ == '__main__':
    main()
