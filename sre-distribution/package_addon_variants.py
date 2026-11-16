"""Build independent registry-only addon shells and external-resource complete variants."""
from pathlib import Path, PurePosixPath
import argparse, copy, hashlib, json, zipfile
from distribution_env import ROOT, SOURCE_DIR, compile_mod

LANGUAGES={'zh_cn','zh_tw','en_us'}
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lang(n):return n.startswith('assets/') and '/lang/' in n and n.endswith('.json')
def runtime_resource(n):return n.startswith('assets/mega_showdown/showdown/')
def fallback(n):
    return n.endswith('/icon.png') or (n.endswith('.json') and not any(x in n for x in ['/models/','/blockstates/','/bedrock/','/lang/']))
def write(z,n,b):z.writestr(n,b,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
def build(source, snapshot, destination, license_file):
    assert not destination.exists(),destination
    with zipfile.ZipFile(source) as original:
        names=[i.filename for i in original.infolist() if not i.is_dir()]
        assert len(set(names))==len(names)
        assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names)
        meta=json.loads(original.read('fabric.mod.json'));modid=meta['id'];version=meta['version']
        destination.mkdir(parents=True)
        for n in ['client','server-full','server-shell','resourcepacks']:(destination/n).mkdir()
        filename=f'{modid}-fabric-{version}.jar'
        client=destination/'client'/filename;server=destination/'server-full'/filename
        pack=destination/'resourcepacks'/f'{modid}-{version}-resources.zip'
        clientmeta=copy.deepcopy(meta);clientmeta.setdefault('custom',{})['train:variant']='complete-client-resources-external'
        servermeta=copy.deepcopy(meta);servermeta['environment']='server';servermeta.pop('icon',None)
        servermeta['entrypoints']={k:v for k,v in meta.get('entrypoints',{}).items() if k not in ['client','modmenu']}
        servermeta.setdefault('custom',{})['train:variant']='complete-server-resources-external'
        keep_client=lambda n:runtime_resource(n) or not n.startswith('assets/') or (lang(n) and PurePosixPath(n).stem in LANGUAGES) or (not lang(n) and fallback(n))
        with zipfile.ZipFile(client,'x') as c,zipfile.ZipFile(server,'x') as s,zipfile.ZipFile(pack,'x') as p:
            write(p,'pack.mcmeta',json.dumps({'pack':{'pack_format':34,'description':f'{modid} complete client resources'}}).encode())
            write(p,'LICENSE',license_file.read_bytes())
            for n in names:
                b=original.read(n)
                if keep_client(n):write(c,n,json.dumps(clientmeta,indent=2).encode() if n=='fabric.mod.json' else b)
                if runtime_resource(n) or not n.startswith(('assets/','resourcepacks/')):write(s,n,json.dumps(servermeta,indent=2).encode() if n=='fabric.mod.json' else b)
                if n.startswith('assets/') and not lang(n) and not runtime_resource(n):write(p,n,b)
            for z in [c,s]:
                if 'LICENSE-train-upstream' not in names:write(z,'LICENSE-train-upstream',license_file.read_bytes())
        dump=json.loads(snapshot.read_text(encoding='utf-8'))
        entries={k:[e for e in v if e['id'].split(':')[0]==modid] for k,v in dump.items()}
        entries={k:v for k,v in entries.items() if v}
        class_name='AddonRegistryShell'
        package='train.addons.shell.'+modid
        resource=f'train-shell-{modid}-registries.json'
        text=(SOURCE_DIR/'RegistryShell.java').read_text(encoding='utf-8')
        text=text.replace('package train.cobblemon.shell;',f'package {package};').replace('RegistryShell',class_name).replace('train-shell-registries.json',resource).replace('COBBLEMON_REGISTRY_SHELL_READY',modid.upper()+'_REGISTRY_SHELL_READY')
        folder=ROOT/'addon-shell-sources'/modid;folder.mkdir(parents=True,exist_ok=True)
        java=folder/(class_name+'.java');java.write_text(text,encoding='utf-8')
        shellmeta={'schemaVersion':1,'id':modid,'version':version,'name':meta['name']+' Registry Shell','environment':'server','license':meta.get('license','SEE LICENSE'),'entrypoints':{'main':[package+'.'+class_name]},'depends':{'fabricloader':'>=0.17.2','minecraft':'1.21.1','java':'>=21','fabric-api':'*','cobblemon':'1.8.4+1.21.1'},'custom':{'train:variant':'registry-only-shell','train:gameplay':False}}
        built=compile_mod(modid+'-registry-shell',[java],shellmeta,{resource:json.dumps(entries).encode(),'LICENSE':license_file.read_bytes()})
        shell=destination/'server-shell'/filename;shell.write_bytes(built.read_bytes())
        with zipfile.ZipFile(client) as c,zipfile.ZipFile(server) as s,zipfile.ZipFile(pack) as p,zipfile.ZipFile(shell) as h:
            assert all(z.testzip() is None for z in [c,s,p,h])
            classes=[n for n in names if n.endswith('.class')]
            for n in names:
                if n.endswith('.class') or runtime_resource(n) or n.startswith(('data/','META-INF/jars/')):
                    assert c.read(n)==original.read(n)==s.read(n),n
                if n.startswith('assets/') and not lang(n) and not runtime_resource(n):assert p.read(n)==original.read(n),n
            assert not any(n.startswith(('com/','dev/','data/','assets/','META-INF/jars/')) for n in h.namelist())
        outputs=[client,server,shell,pack]
        manifest={'modId':modid,'version':version,'sourceJar':{'path':str(source),'sha256':digest(source)},'preservedClasses':len(classes),'shellRegistries':{k:len(v) for k,v in entries.items()},'outputs':{p.relative_to(destination).as_posix():{'sha256':digest(p),'bytes':p.stat().st_size} for p in outputs},'scope':'Full: all gameplay retained, art externalized, English/Simplified/Traditional Chinese where supplied. Shell: registration only; no gameplay, API, old saves, or business component payload support.'}
        manifest['retainedRuntimeResources']=[n for n in names if runtime_resource(n)]
        if modid=='mega_showdown':assert len(manifest['retainedRuntimeResources'])>=13
        (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('snapshot',type=Path);p.add_argument('destination',type=Path);p.add_argument('--license',dest='license_file',type=Path,required=True)
    a=p.parse_args();build(a.source,a.snapshot,a.destination,a.license_file)
