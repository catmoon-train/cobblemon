from pathlib import Path
import argparse, hashlib, json, shutil, socket, subprocess, time
from distribution_env import ROOT, WORKSPACE, CACHE, MAPROOT, MINECRAFT, API, CLASSPATH, REGISTRY_SNAPSHOT, argfile, prepare_server, server_args

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def compare(expected, actual):
    a=json.loads(expected.read_text(encoding='utf-8'));b=json.loads(actual.read_text(encoding='utf-8'))
    assert set(a)==set(b),('registry keys',set(a)^set(b))
    states=0
    for key,entries in a.items():
        left={e['id']:e for e in entries};right={e['id']:e for e in b[key]}
        assert left.keys()==right.keys(),(key,left.keys()^right.keys())
        if key=='minecraft:block':
            for id,spec in left.items():
                for field in ['properties','states','defaultState']:assert spec[field]==right[id][field],(id,field)
                states+=len(spec['states'])
    return {'registryTypes':len(a),'entries':sum(map(len,a.values())),'blockStates':states}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--server',type=Path,required=True);parser.add_argument('--client',type=Path,required=True);parser.add_argument('--pack',type=Path,required=True);parser.add_argument('--label',required=True)
    parser.add_argument('--server-mod', type=Path, action='append', default=[])
    parser.add_argument('--client-mod', type=Path, action='append', default=[])
    parser.add_argument('--extra-pack', type=Path, action='append', default=[])
    parser.add_argument('--snapshot', type=Path, default=REGISTRY_SNAPSHOT)
    args=parser.parse_args()
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server_probe=ROOT/'distribution-probe.jar';client_probe=ROOT/'distribution-client-probe.jar'
    server=prepare_server('pair-'+args.label+'-server',args.server,server_probe,port)
    for p in args.server_mod: shutil.copy2(p, server/'mods'/p.name)
    client=ROOT/('pair-'+args.label+'-client');assert not client.exists()
    (client/'mods').mkdir(parents=True);(client/'resourcepacks').mkdir()
    for p in [args.client,API,client_probe,*args.client_mod]:shutil.copy2(p,client/'mods'/p.name)
    packs=[args.pack,*args.extra_pack]
    for p in packs: shutil.copy2(p,client/'resourcepacks'/p.name)
    (client/'options.txt').write_text('onboardAccessibility:false\nresourcePacks:'+json.dumps(['file/'+p.name for p in packs])+'\nincompatibleResourcePacks:[]\nrenderDistance:2\nsimulationDistance:5\nmaxFps:60\n',encoding='utf-8')
    serverlog=ROOT/('pair-'+args.label+'-server.log');clientlog=ROOT/('pair-'+args.label+'-client.log')
    server_dump=ROOT/('pair-'+args.label+'-server-registries.json');client_dump=ROOT/('pair-'+args.label+'-client-registries.json')
    started=time.monotonic();process=None;clientprocess=None
    with serverlog.open('wb') as out:
        process=subprocess.Popen(['java',argfile(args.label+'-server.args',server_args(server,['-Dtrain.registry.output='+server_dump.as_posix()]))],cwd=server,stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT)
        try:
            while time.monotonic()-started<180:
                text=serverlog.read_text(encoding='utf-8',errors='replace')
                if 'TRAIN_SERVER_READY' in text:break
                if process.poll() is not None:raise RuntimeError('Server failed: '+str(serverlog))
                time.sleep(1)
            else:raise TimeoutError('Server startup: '+str(serverlog))
            server_comparison=compare(args.snapshot,server_dump)
            natives=(WORKSPACE/'.gradle/loom-cache/natives').as_posix()
            java=['-Xmx3G','-Dfile.encoding=UTF-8','-Dfabric.development=false','-Dfabric.gameJarPath='+MINECRAFT.as_posix(),'-Djava.library.path='+natives,'-Dorg.lwjgl.librarypath='+natives,'-Dtrain.connect=127.0.0.1:'+str(port),'-Dtrain.client.registry.output='+client_dump.as_posix(),'-cp',CLASSPATH,'net.fabricmc.loader.impl.launch.knot.KnotClient','--username','TrainVerify','--uuid','00000000000000000000000000000002','--accessToken','0','--version','1.21.1','--userType','legacy','--gameDir',client.as_posix(),'--assetsDir',(CACHE/'fabric-loom/assets').as_posix(),'--assetIndex','1.21.1-17','--width','640','--height','360']
            with clientlog.open('wb') as cout:
                clientprocess=subprocess.Popen(['java',argfile(args.label+'-client.args',java)],cwd=client,stdout=cout,stderr=subprocess.STDOUT)
                code=clientprocess.wait(timeout=240)
            text=clientlog.read_text(encoding='utf-8',errors='replace')
            assert code==0 and 'TRAIN_CLIENT_JOIN_PASS' in text,(code,str(clientlog),'\n'.join(text.splitlines()[-30:]))
            client_comparison=compare(args.snapshot,client_dump)
            record={'passed':True,'label':args.label,'serverHeapLimit':server_args(server)[0],'serverJar':{'path':str(args.server),'sha256':digest(args.server)},'clientJar':{'path':str(args.client),'sha256':digest(args.client)},'resourcePack':{'path':str(args.pack),'sha256':digest(args.pack)},'serverRegistries':server_comparison,'clientRegistries':client_comparison,'clientResult':[l for l in text.splitlines() if 'TRAIN_CLIENT_JOIN_PASS' in l],'elapsedSeconds':round(time.monotonic()-started,2)}
            record['serverMods']=[{'path':str(p),'sha256':digest(p)} for p in args.server_mod]
            record['clientMods']=[{'path':str(p),'sha256':digest(p)} for p in args.client_mod]
            record['extraPacks']=[{'path':str(p),'sha256':digest(p)} for p in args.extra_pack]
            (ROOT/('pair-'+args.label+'-verification.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(record,ensure_ascii=False,indent=2))
        finally:
            if clientprocess is not None and clientprocess.poll() is None:clientprocess.terminate();clientprocess.wait(timeout=30)
            if process.poll() is None:
                process.stdin.write(b'stop\n');process.stdin.flush()
                try:process.wait(timeout=60)
                except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=30)
            print('SERVER_EXIT',process.returncode,'LOG',serverlog,'CLIENT_LOG',clientlog)

if __name__=='__main__':main()
