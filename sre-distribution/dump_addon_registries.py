from pathlib import Path
import argparse, shutil, subprocess
from distribution_env import ROOT, prepare_server, server_args, argfile
p=argparse.ArgumentParser();p.add_argument('--cobblemon',type=Path,required=True);p.add_argument('--mod',type=Path,action='append',default=[]);p.add_argument('--label',required=True)
p.add_argument('--legacy-config',type=Path)
a=p.parse_args()
game=prepare_server('registry-'+a.label,a.cobblemon,ROOT/'distribution-probe.jar')
for mod in a.mod:shutil.copy2(mod,game/'mods'/mod.name)
if a.legacy_config:
 (game/'world').mkdir();shutil.copy2(a.legacy_config,game/'world/pokemonRideConfig.json')
output=ROOT/('registry-'+a.label+'.json');log=ROOT/('registry-'+a.label+'.log')
with log.open('wb') as f:
 result=subprocess.run(['java',argfile(a.label+'-registry.args',server_args(game,['-Dtrain.registry.output='+output.as_posix(),'-Dtrain.probe.stop=true', '-Dtrain.legacy.fixture='+str(bool(a.legacy_config)).lower()]))],cwd=game,stdout=f,stderr=subprocess.STDOUT,timeout=300)
text=log.read_text(encoding='utf-8',errors='replace')
print('\n'.join(text.splitlines()[-55:]))
assert result.returncode==0 and 'TRAIN_REGISTRY_DUMP_PASS' in text,(result.returncode,log)
if a.legacy_config:
 assert (game/'world/pokemonRideConfig.json').read_bytes()==a.legacy_config.read_bytes()
 assert 'TRAIN_LEGACY_CONFIG_PASS' in text
 print('LEGACY_CONFIG_UNCHANGED_PASS')
print('REGISTRY_PASS',output)
