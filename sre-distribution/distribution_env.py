from pathlib import Path
import json, os, shutil, subprocess, zipfile

SOURCE_DIR = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('COBBLEMON_DIST_WORK', os.environ.get('PI_SCRATCH_DIR', str(SOURCE_DIR/'build'))))
ROOT.mkdir(parents=True, exist_ok=True)
REGISTRY_SNAPSHOT = SOURCE_DIR/'cobblemon-1.8.4-registries.json'
WORKSPACE = Path(os.environ.get('TRAIN_WORKSPACE', 'G:/exmo/StarRailExpress2/StarRailExpress'))
CACHE = Path.home() / '.gradle/caches'
NAMED_CP = os.environ.get('COBBLEMON_NAMED_CLASSPATH') or (WORKSPACE/'sre-performance/build/loom-cache/argFiles/runPerfSmoke').read_text(encoding='utf-8').splitlines()[1].replace('\\','/')
LIBRARIES = [p for p in NAMED_CP.split(';') if '/.gradle/caches/modules-2/files-2.1/' in p and '/net.fabricmc.fabric-api/' not in p]
MAPROOT = CACHE/'fabric-loom/1.21.1/loom.mappings.1_21_1.layered+hash.2198-v2'
MAPPINGS = MAPROOT/'mappings.tiny'
MINECRAFT = ROOT/'minecraft-1.21.1-intermediary-smoke.jar'
API = next((CACHE/'modules-2/files-2.1/net.fabricmc.fabric-api/fabric-api/0.116.13+1.21.1').rglob('fabric-api-0.116.13+1.21.1.jar'))
TINY = next((CACHE/'modules-2/files-2.1/net.fabricmc/tiny-remapper/0.14.0').rglob('tiny-remapper-0.14.0.jar'))
MAPIO = sorted(p for p in (CACHE/'modules-2/files-2.1/net.fabricmc/mapping-io').rglob('*.jar') if not p.name.endswith('-sources.jar'))[-1]
CLASSPATH = ';'.join([*LIBRARIES,MINECRAFT.as_posix(),(MAPROOT/'mappings.jar').as_posix()])

def argfile(name, args):
    p=ROOT/name
    p.write_text('\n'.join('"'+str(a).replace('\\','/')+'"' for a in args),encoding='utf-8')
    return '@'+p.as_posix()

def remap(source, target):
    cp=';'.join([TINY.as_posix(),MAPIO.as_posix(),*LIBRARIES])
    args=['-Xmx2G','-cp',cp,'net.fabricmc.tinyremapper.Main',source.as_posix(),target.as_posix(),MAPPINGS.as_posix(),'named','intermediary']
    args.extend(p for p in NAMED_CP.split(';') if p.endswith('.jar') and Path(p).is_file())
    subprocess.run(['java',argfile(target.stem+'-remap.args',args)],check=True)

def compile_mod(name, sources, metadata, resources=None):
    out=ROOT/(name+'-classes');out.mkdir(exist_ok=True)
    args=['--release','21','-proc:none','-encoding','UTF-8','-cp',NAMED_CP,'-d',out.as_posix(),*[p.as_posix() for p in sources]]
    subprocess.run(['javac','-J-Duser.language=en',argfile(name+'-javac.args',args)],check=True)
    named=ROOT/(name+'-named.jar');target=ROOT/(name+'.jar')
    with zipfile.ZipFile(named,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('fabric.mod.json',json.dumps(metadata,ensure_ascii=False))
        z.writestr('META-INF/MANIFEST.MF','Manifest-Version: 1.0\nFabric-Mapping-Namespace: named\n\n')
        for p in sorted(out.rglob('*.class')):z.write(p,p.relative_to(out).as_posix())
        for key,value in (resources or {}).items():z.writestr(key,value)
    remap(named,target)
    return target

def server_args(game, extra=None):
    return ['-Xmx'+os.environ.get('TRAIN_SERVER_HEAP','3G'),'-Dfile.encoding=UTF-8','-Dfabric.development=false','-Dfabric.gameJarPath='+MINECRAFT.as_posix(),*(extra or []),'-cp',CLASSPATH,'net.fabricmc.loader.impl.launch.knot.KnotServer','nogui']

def prepare_server(name, mod, probe, port=0):
    game=ROOT/name
    assert not game.exists(),game
    (game/'mods').mkdir(parents=True)
    for p in [mod,API,probe]:shutil.copy2(p,game/'mods'/p.name)
    (game/'eula.txt').write_text('eula=true\n',encoding='utf-8')
    (game/'server.properties').write_text('online-mode=false\nserver-ip=127.0.0.1\nserver-port='+str(port)+'\nview-distance=2\nsimulation-distance=2\nspawn-protection=0\nmax-players=2\nlevel-type=minecraft:flat\ngenerator-settings={"layers":[{"block":"minecraft:bedrock","height":1}],"biome":"minecraft:the_void","features":false,"lakes":false}\n',encoding='utf-8')
    return game

if __name__=='__main__':
    probe=compile_mod('distribution-probe',[SOURCE_DIR/'DistributionProbe.java'],{'schemaVersion':1,'id':'train_distribution_probe','version':'1.0.0','environment':'*','entrypoints':{'main':['train.cobblemon.probe.DistributionProbe']},'depends':{'fabric-api':'*'}})
    game=prepare_server(os.environ.get('TRAIN_PROBE_GAME','cobblemon-original-registry'),Path('G:/download/Cobblemon-fabric-1.8.4+1.21.1.jar'),probe)
    log=ROOT/'cobblemon-original-registry.log'
    args=server_args(game,['-Dtrain.registry.output='+(ROOT/'cobblemon-1.8.4-registries.json').as_posix(),'-Dtrain.probe.stop=true'])
    with log.open('wb') as stream:
        result=subprocess.run(['java',argfile('registry-server.args',args)],cwd=game,stdout=stream,stderr=subprocess.STDOUT,timeout=240)
    text=log.read_text(encoding='utf-8',errors='replace')
    print('\n'.join(text.splitlines()[-65:]))
    assert result.returncode==0 and 'TRAIN_REGISTRY_DUMP_PASS' in text,(result.returncode,log)
