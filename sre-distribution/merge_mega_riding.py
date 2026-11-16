"""Merge native riding data into Mega Showdown's full species overrides.

Mega ships complete data/cobblemon/species files for the species it touches, so they replace
core species wholesale. Only the riding block and missing seat locators are merged here; all
other Mega gameplay data (moves, stats, evolutions, forms' stats) stays byte-identical.
"""
from pathlib import Path
import json, argparse

TARGETS = set('charizard blastoise lapras metagross swampert ursaluna'.split())

def seat_list(riding):
    return riding.get('seats') if isinstance(riding, dict) else None

def model_for(mega, species, aspects):
    for resolver in (mega / 'assets/cobblemon/bedrock/pokemon/resolvers').glob(f'*{species}*/*.json'):
        data = json.loads(resolver.read_text(encoding='utf-8'))
        for variation in data.get('variations', []):
            if aspects and set(variation.get('aspects', [])) == set(aspects):
                model = variation.get('model')
                if model:
                    return mega / 'assets/cobblemon/bedrock/pokemon/models' / (model.split(':')[-1])
    return None

def add_locator(model_path):
    data = json.loads(model_path.read_text(encoding='utf-8'))
    geometry = data['minecraft:geometry'][0]
    bones = geometry['bones']
    seats = {k: (bone, v) for bone in bones for k, v in bone.get('locators', {}).items()}
    if 'seat_2' in seats:
        return False
    anchor, position = seats['seat_1']
    target = [position[0], position[1], position[2] - 12]
    name = 'compat_locator_seat_2'
    assert all(b['name'] != name for b in bones)
    bones.append({'name': name, 'parent': anchor['name'], 'pivot': target, 'locators': {'seat_2': target}})
    model_path.write_text(json.dumps(data, ensure_ascii=False, indent='\t') + '\n', encoding='utf-8', newline='\n')
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--mega', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    core_species = {p.stem: p for p in (args.core / 'data/cobblemon/species').rglob('*.json')}
    changed, locators, warnings = [], [], []
    for path in sorted((args.mega / 'data/cobblemon/species').rglob('*.json')):
        if path.stem not in TARGETS:
            continue
        core = json.loads(core_species[path.stem].read_text(encoding='utf-8'))
        mega = json.loads(path.read_text(encoding='utf-8'))
        assert 'riding' in core, path
        # 标准形态：完整采用本体的原生骑乘（含双座、模式、音效与数值）。
        mega['riding'] = core['riding']
        core_forms = {form['name'].lower(): form for form in core.get('forms', [])}
        for form in mega.get('forms', []):
            if 'riding' not in form:
                continue
            original = core_forms.get(form['name'].lower())
            if original and 'riding' in original:
                form['riding'] = original['riding']
                continue
            seats = seat_list(form['riding']) or []
            if len(seats) >= 2:
                continue
            model = model_for(args.mega, path.stem, form.get('aspects', []))
            if model is not None and model.is_file() and add_locator(model):
                seats = list(seats) + [{'locator': 'seat_2'}]
                form['riding']['seats'] = seats
                locators.append(f'{path.stem}:{form["name"]}:{model.relative_to(args.mega).as_posix()}')
            else:
                warnings.append(f'{path.stem}:{form["name"]}: kept {len(seats)} seat(s); no model locator available')
        path.write_text(json.dumps(mega, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        changed.append(path.relative_to(args.mega).as_posix())
    assert changed, 'no Mega species override was merged'
    args.report.write_text(json.dumps({'mergedSpecies': changed, 'addedSeatLocators': locators, 'warnings': warnings,
        'scope': 'Only riding blocks and missing seat_2 locators merged; all other Mega gameplay data unchanged.'},
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'merged': len(changed), 'locators': len(locators), 'warnings': warnings}, ensure_ascii=False))

if __name__ == '__main__':
    main()
