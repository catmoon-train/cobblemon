from pathlib import Path
import argparse, hashlib, json, shutil
p=argparse.ArgumentParser();p.add_argument('suite',type=Path);p.add_argument('--addons',type=Path,required=True);p.add_argument('--dependencies',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--readme',type=Path,required=True)
a=p.parse_args()
def copy(src,dst):
 assert src.is_file() and not dst.exists(),(src,dst)
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for n in ['mega-showdown','cobblenav','spawn-notification']:
 for variant in ['client','server-full','server-shell','resourcepacks']:
  for f in (a.addons/n/variant).iterdir():copy(f,a.suite/variant/f.name)
 copy(a.addons/n/'manifest.json',a.suite/'addon-manifests'/(n+'.json'))
 license='LICENSE.md' if n=='mega-showdown' else 'LICENSE'
 copy(a.source/'sre-addons'/n/license,a.suite/'licenses'/(n+'.txt'))
for f in a.dependencies.glob('*.jar'):
 for variant in ['client','server-full']:copy(f,a.suite/variant/f.name)
for f in a.dependencies.glob('*provenance.json'):copy(f,a.suite/'dependency-provenance'/f.name)
copy(a.source/'LICENSE',a.suite/'LICENSE')
copy(a.source/'LICENSE',a.suite/'licenses/Cobblemon.txt')
copy(a.readme,a.suite/'README.md')
copy(a.source/'sre-distribution/riding-compat/README.md',a.suite/'riding-compat.md')
print('ASSEMBLED',a.suite)
