from pathlib import Path
import argparse, os, subprocess, sys
p=argparse.ArgumentParser();p.add_argument('suite',type=Path);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--mode',choices=['both','shell','full'],default='both');a=p.parse_args()
for mode in (['shell','full'] if a.mode=='both' else [a.mode]):
 server=a.suite/('server-'+mode);client=a.suite/'client';base='Cobblemon-fabric-1.8.4+1.21.1.jar'
 cmd=[sys.executable,'-X','utf8',str(Path(__file__).with_name('verify_distribution_pair.py')),'--server',str(server/base),'--client',str(client/base),'--pack',str(a.suite/'resourcepacks/Cobblemon-1.8.4-resources.zip'),'--snapshot',str(a.snapshot),'--label',a.label+'-'+mode]
 for flag,folder in [('--server-mod',server),('--client-mod',client)]:
  for mod in sorted(folder.glob('*.jar')):
   if mod.name!=base:cmd += [flag,str(mod)]
 for pack in sorted((a.suite/'resourcepacks').glob('*-resources.zip')):
  if pack.name!='Cobblemon-1.8.4-resources.zip':cmd+=['--extra-pack',str(pack)]
 env=dict(os.environ,TRAIN_SERVER_HEAP='512M' if mode=='shell' else '3G')
 subprocess.run(cmd,check=True,env=env)
