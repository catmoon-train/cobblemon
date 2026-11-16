from pathlib import Path
import hashlib
import json
import os
import struct
import tarfile
import zipfile


def verify(source, out, target, classes, cp, loader, kotlin_prefix, run):
    test_classes = out/'test-classes'
    fixtures = out/'test-fixtures'
    test_classes.mkdir(exist_ok=True)
    fixtures.mkdir(exist_ok=True)
    run('javac', 'test-fixtures-javac', ['--release', '21', '-proc:none', '-encoding', 'UTF-8',
        '-cp', loader.as_posix(), '-d', fixtures.as_posix(),
        *[p.as_posix() for p in sorted((source/'tests/fixtures').rglob('*.java'))]])
    run('javac', 'tests-javac', ['--release', '21', '-proc:none', '-encoding', 'UTF-8',
        '-cp', os.pathsep.join([classes.as_posix(), cp]), '-d', test_classes.as_posix(),
        *[p.as_posix() for p in sorted((source/'tests').glob('*.java'))]])
    # Fabric Loader is signed. Copy only its API bytecode without signatures so the
    # test-only FabricLoader replacement can share the package in this isolated JVM.
    loader_api = out/'test-loader-api.jar'
    with zipfile.ZipFile(loader) as original, zipfile.ZipFile(loader_api, 'w') as api:
        for name in original.namelist():
            if name.endswith('.class') and name.startswith(('net/fabricmc/api/', 'net/fabricmc/loader/api/')):
                api.writestr(name, original.read(name))
    run('java', 'bootstrap-isolation-test', ['-cp', test_classes.as_posix(), 'BootstrapIsolationTest',
        fixtures.as_posix(), target.as_posix(), loader_api.as_posix()])
    run('java', 'config-compatibility-test', ['-cp', os.pathsep.join([test_classes.as_posix(), classes.as_posix(), cp]),
        'ConfigCompatibilityTest'])
    with tarfile.open(source/'upstream/source.tar.gz', 'r:gz') as archive:
        hashes = json.loads((source/'upstream/sha256.json').read_text(encoding='utf-8'))
        for name, expected in hashes.items():
            assert hashlib.sha256(archive.extractfile(name).read()).hexdigest() == expected, name
        original_metadata = json.load(archive.extractfile('src/main/resources/fabric.mod.json'))
        original_languages = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile() and '/lang/' in m.name}
        original_sound = archive.extractfile('src/main/resources/assets/spawn_notification/sounds/shiny.ogg').read()
    with zipfile.ZipFile(target) as jar:
        names = jar.namelist()
        meta = json.loads(jar.read('fabric.mod.json'))
        assert meta['version'] == original_metadata['version'] == '1.5-fabric-1.2.1'
        assert meta['entrypoints'] == {'main': ['us.timinc.mc.cobblemon.spawnnotification.SpawnNotificationBootstrap']}
        assert jar.read('LICENSE') == (source/'LICENSE').read_bytes()
        assert jar.read('assets/spawn_notification/sounds/shiny.ogg') == original_sound
        for name, value in original_languages.items():
            assert jar.read(name.removeprefix('src/main/resources/')) == value
        sound = json.loads(jar.read('assets/spawn_notification/sounds.json'))
        for name in original_languages:
            language = json.loads(jar.read(name.removeprefix('src/main/resources/')))
            assert sound['pla_shiny']['subtitle'] in language
        assert not any('Test' in n or n.startswith(('net/fabricmc/', 'com/cobblemon/', 'kotlin/')) for n in names)
        for name in names:
            if not name.endswith('.class'):
                continue
            data = jar.read(name)
            assert struct.unpack('>H', data[6:8])[0] == 65, name
            # 生产包必须是 intermediary，不能把 named 开发 JAR 当成发布包。
            for forbidden in [b'net/minecraft/server/level/ServerLevel', b'net/minecraft/network/chat/Component',
                              b'net/minecraft/resources/ResourceLocation', b'getCtx']:
                assert forbidden not in data, (name, forbidden)
    print('ARTIFACT_CONTRACT_PASS (JVM21/intermediary, metadata, exact upstream archive/license/audio/languages, subtitle)')
