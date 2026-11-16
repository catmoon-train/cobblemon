"""Focused JSON + static conversion contracts, not a JVM/game integration test.
Usage: python -X utf8 sre-distribution/riding-compat/check_riding_compat.py [--baseline-ref HEAD]
All generated files, if any, belong to the caller's scratch directory; this check is read-only.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
K = ROOT / 'common/src/main/kotlin/com/cobblemon/mod/common'
HERE = Path(__file__).resolve().parent


def read(path):
    return path.read_text(encoding='utf-8')


def baseline(ref, paths):
    # One Git invocation for all original JSON files; decode concatenated complete JSON documents.
    result = subprocess.run(['git', '-C', str(ROOT), 'show', *[f'{ref}:{p}' for p in paths]],
                            check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    decoder = json.JSONDecoder()
    docs, pos = [], 0
    for _ in paths:
        while pos < len(result) and result[pos].isspace():
            pos += 1
        doc, size = decoder.raw_decode(result[pos:])
        docs.append(doc)
        pos += size
    assert not result[pos:].strip(), 'unexpected extra baseline documents'
    return dict(zip(paths, docs))


def without_riding(doc):
    doc = json.loads(json.dumps(doc))
    doc.pop('riding', None)
    for form in doc.get('forms', []):
        form.pop('riding', None)
    return doc


def validate_riding(data, label):
    assert 'behaviour' not in data and 'stats' not in data, label
    assert data.get('behaviours') and len(data['seats']) >= 2, label
    for style, settings in data['behaviours'].items():
        assert style in {'LAND', 'AIR', 'LIQUID'}, label
        assert settings['key'].startswith('cobblemon:'), label
        assert settings.get('stats'), label
        for stat, value in settings['stats'].items():
            assert stat in {'SPEED', 'ACCELERATION', 'SKILL', 'JUMP', 'STAMINA'}, label
            match = re.fullmatch(r'(\d+)(?:-(\d+))?', value)
            assert match, (label, value)
            lo, hi = int(match[1]), int(match[2] or match[1])
            assert 0 <= lo <= hi <= 100, label


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-ref', help='Optional local Git ref for semantic preservation checks')
    args = parser.parse_args()
    manifest = json.loads(read(HERE / 'species-manifest.json'))
    assert len(manifest) == len({e['species'] for e in manifest}) == 47
    assert next(e for e in manifest if e['oldKey'] == 'Espahtla')['species'] == 'espathra'
    species_paths = [e['speciesFile'] for e in manifest]
    model_paths = sorted({p for e in manifest for p in e['models']})
    old = baseline(args.baseline_ref, species_paths + model_paths) if args.baseline_ref else {}
    added = fixed = 0
    for entry in manifest:
        path = entry['speciesFile']
        data = json.loads(read(ROOT / path))
        all_rides = [data['riding']] + [f['riding'] for f in data.get('forms', []) if f.get('riding')]
        for index, ride in enumerate(all_rides):
            validate_riding(ride, (path, index))
        required = {s.get('locator', f'seat_{i+1}') for ride in all_rides for i, s in enumerate(ride['seats'])}
        for model in entry['models']:
            doc = json.loads(read(ROOT / model))
            bones = doc['minecraft:geometry'][0]['bones']
            names = [bone['name'] for bone in bones]
            assert len(names) == len(set(names)), model
            locators = {name: value for bone in bones for name, value in bone.get('locators', {}).items()}
            assert required <= locators.keys(), (model, required - locators.keys())
            points = []
            for seat in ['seat_1', 'seat_2']:
                point = locators[seat]
                point = point.get('offset') if isinstance(point, dict) else point
                assert len(point) == 3 and all(isinstance(v, (int, float)) for v in point), model
                points.append(point)
            assert points[0] != points[1], (model, 'coincident seats')
            for bone in bones:
                assert not bone.get('parent') or bone['parent'] in names, (model, bone['name'])
            if old:
                original = old[model]
                before = original['minecraft:geometry'][0]['bones']
                assert bones[:len(before)] == before, (model, 'original bones changed')
                assert doc['minecraft:geometry'][0]['description'] == original['minecraft:geometry'][0]['description']
        if old:
            previous = old[path]
            assert without_riding(previous) == without_riding(data), (path, 'unrelated data changed')
            native = previous.get('riding', {})
            added += not bool(native.get('behaviours'))
            fixed += bool(native.get('behaviour'))
            if native.get('behaviours'):
                assert data['riding']['behaviours'] == native['behaviours'], (path, 'native styles/stats/sounds changed')
                assert data['riding']['seats'][:len(native['seats'])] == native['seats'], path
    if old:
        assert added == 19 and fixed == 3, (added, fixed)

    source = read(K / 'api/riding/LegacyRidingConfig.kt')
    # Explicit source contracts: these assertions do not execute Kotlin or pretend to test Gson/runtime sync.
    for contract in [
        'getWorldPath(LevelResource.ROOT)', 'resolve("pokemonRideConfig.json")',
        'restoreOriginals()', 'originals[form] = form.ridingOverride',
        'form.ridingOverride = converted', 'it == "espahtla"',
        'species.standardForm', 'species.forms.firstOrNull',
        'value.asJsonPrimitive.isNumber', 'n.isFinite() && n in min..max',
        'number(it, 0.05, 4.0, "speedModifier")', 'number(it, 0.0, 72000.0, "stamina")',
        'n % 1.0 == 0.0', 'it.asJsonArray.size() <= 7', 'value.asJsonArray.size() == 3',
        'number(it, -16.0, 16.0, "offset")', 'SeatOffset(xyz[2], xyz[1], xyz[0])',
        'config.stamina in setOf(0, 200)', 'config.stamina / 20.0',
        '"walkSpeedMultiplier", oldMultiplier * config.speed', 'original.conditions',
        'config.passengerOffsets?.map', 'mustAllowEntityRiding is not enabled',
        'JsonSerializer<Expression>', 'context.serialize(value.sounds)',
    ]:
        assert contract in source, contract
    assert not re.search(r'Files\.(write|delete|create)|newBufferedWriter|ConfigS2C|KeyBinding', source)
    seat = read(K / 'api/riding/Seat.kt')
    for field in 'x y z'.split():
        assert f'buffer.writeDouble(value.{field})' in seat
    assert 'SeatOffset(buffer.readDouble(), buffer.readDouble(), buffer.readDouble())' in seat
    assert 'offsetPosition(getEntity())' in read(K / 'client/entity/PokemonClientDelegate.kt')
    assert 'offsetPosition(entity)' in read(K / 'entity/pokemon/PokemonServerDelegate.kt')
    species = read(K / 'pokemon/Species.kt')
    assert 'writeNullable(this.standardForm.ridingOverride)' in species
    assert 'this.standardForm.ridingOverride = buffer.readNullable' in species
    horse = read(K / 'api/riding/behaviour/types/land/HorseBehaviour.kt')
    assert 'getWalkSpeed(vehicle) * settings.walkSpeedMultiplier' in horse
    assert 'writeDouble(walkSpeedMultiplier)' in horse and 'walkSpeedMultiplier = buffer.readDouble()' in horse
    liquid = read(K / 'api/riding/behaviour/types/liquid/SubmarineBehaviour.kt')
    assert 'writeNullable(legacyFluid)' in liquid and 'legacyFluid = buffer.readNullable' in liquid
    assert 'var legacyFluid: String? = null' in liquid
    controller = read(K / 'api/riding/behaviour/RidingController.kt')
    assert controller.count('!liquid.isInRideFluid(entity)') == 2
    print(f'PASS: 47 species, {len(model_paths)} models, native seat/format and conversion-source contracts' +
          (f'; baseline preserved, {added} missing riding blocks fixed ({fixed} old base schemas)' if old else ''))


if __name__ == '__main__':
    main()
