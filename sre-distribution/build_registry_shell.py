from pathlib import Path
from distribution_env import compile_mod, ROOT, SOURCE_DIR, REGISTRY_SNAPSHOT

metadata = {
    'schemaVersion': 1, 'id': 'cobblemon', 'version': '1.8.4+1.21.1',
    'name': 'Cobblemon Registry Shell (Train Server Only)',
    'description': 'Registry-only server replacement; no Pokemon gameplay, addons or old saves.',
    'license': 'MPL-2.0', 'environment': 'server',
    'entrypoints': {'main': ['train.cobblemon.shell.RegistryShell']},
    'depends': {'fabricloader': '>=0.17.2', 'fabric-api': '>=0.116.6+1.21.1', 'minecraft': '1.21.1', 'java': '>=21'},
    'custom': {'train:variant': 'registry-only-shell', 'train:upstreamCommit': 'b79dbcca802e10fb7eda89c568a874f7891a2d28'}
}
resources = {
    'train-shell-registries.json': REGISTRY_SNAPSHOT.read_bytes(),
    'LICENSE': Path('G:/download/cobblemon-main (1)/cobblemon-main/LICENSE').read_bytes()
}
print(compile_mod('Cobblemon-fabric-1.8.4+1.21.1-server-shell', [SOURCE_DIR/'RegistryReplayEngine.java', SOURCE_DIR/'RegistryShell.java'], metadata, resources))
