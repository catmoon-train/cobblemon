"""从精确 1.8.4 源码构建的完整 JAR 生成客户端/服务端资源外置发行包。"""
from pathlib import Path, PurePosixPath
import argparse, copy, hashlib, json, re, sys, zipfile
if not Path(__file__).with_name('split_cobblemon_resources.py').is_file():
    sys.path.insert(0, str(Path('G:/exmo/StarRailExpress2/StarRailExpress/tools')))
from split_cobblemon_resources import fallback, language, FALLBACK_FILES

COMMIT = 'b79dbcca802e10fb7eda89c568a874f7891a2d28'
LANGUAGES = {'zh_cn', 'zh_tw', 'en_us'}

def sha256(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def localized(name):return language(name) and PurePosixPath(name).stem in LANGUAGES

def keep_client(name):
    if name.startswith('assets/'):return localized(name) if language(name) else fallback(name)
    if name.startswith('resourcepacks/'):
        parts=name.split('/',2)
        return len(parts)==3 and (parts[2]=='pack.mcmeta' or localized(parts[2]))
    return True

def write(z, name, content):z.writestr(name,content,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

def build(source, destination, shell, asset_reference):
    assert not destination.exists(),destination
    assert sha256(asset_reference)=='77c4866b2e4c38afb488ed09b62ffd2729ce291dc793fca9c055c087f0b03978'
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(asset_reference) as assets:
        names=[i.filename for i in original.infolist() if not i.is_dir()]
        def payload(name):
            return assets.read(name) if name.startswith(('assets/','resourcepacks/')) else original.read(name)
        assert len(names)==len(set(names))
        assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names)
        mod=json.loads(original.read('fabric.mod.json'))
        assert mod['id']=='cobblemon' and mod['version']=='1.8.4+1.21.1',mod
        gitinfo=original.read('cobblemon-git.properties').decode('utf-8')
        assert 'commit='+COMMIT in gitinfo,gitinfo
        assert FALLBACK_FILES <= set(names)
        asset_names={n for n in names if n.startswith(('assets/','resourcepacks/'))}
        assert asset_names=={i.filename for i in assets.infolist() if not i.is_dir() and i.filename.startswith(('assets/','resourcepacks/'))}
        assert 'assets/cobblemon/bedrock/pokemon/animations/0025_pikachu/pikachu.animation.json' in asset_names
        assert not any(n.startswith('META-INF/') and n.upper().endswith(('.RSA','.SF','.DSA','.EC')) for n in names)
        destination.mkdir(parents=True)
        packs=destination/'resourcepacks';packs.mkdir()
        client=destination/'Cobblemon-fabric-1.8.4+1.21.1-client-full-split.jar'
        server=destination/'Cobblemon-fabric-1.8.4+1.21.1-server-full-split.jar'
        pack=packs/'Cobblemon-1.8.4-resources.zip'
        optional_names=sorted({n.split('/')[1] for n in names if n.startswith('resourcepacks/') and len(n.split('/'))>2})
        optional={key:packs/f'Cobblemon-1.8.4-optional-{key}.zip' for key in optional_names}
        clientmeta=copy.deepcopy(mod);clientmeta.setdefault('custom',{})['train:variant']='complete-client-resources-external'
        servermeta=copy.deepcopy(mod);servermeta['environment']='server';servermeta['entrypoints']={'main':mod['entrypoints']['main']};servermeta.pop('icon',None)
        servermeta.setdefault('custom',{})['train:variant']='complete-server-resources-external'
        with zipfile.ZipFile(client,'x') as c,zipfile.ZipFile(server,'x') as s,zipfile.ZipFile(pack,'x') as p:
            write(p,'pack.mcmeta',json.dumps({'pack':{'pack_format':34,'description':'Cobblemon 1.8.4 完整客户端资源（语言由模组提供）'}},ensure_ascii=False).encode('utf-8'))
            write(p,'LICENSE',assets.read('LICENSE'))
            for name in names:
                data=payload(name)
                if keep_client(name):write(c,name,json.dumps(clientmeta,ensure_ascii=False,indent=2).encode('utf-8') if name=='fabric.mod.json' else data)
                if not name.startswith(('assets/','resourcepacks/')):write(s,name,json.dumps(servermeta,ensure_ascii=False,indent=2).encode('utf-8') if name=='fabric.mod.json' else data)
                if name.startswith('assets/') and not language(name):write(p,name,data)
        for key,target in optional.items():
            prefix=f'resourcepacks/{key}/'
            with zipfile.ZipFile(target,'x') as z:
                write(z,'LICENSE',assets.read('LICENSE'))
                for name in names:
                    if name.startswith(prefix):
                        relative=name[len(prefix):]
                        if language(relative) and not localized(relative):continue
                        write(z,relative,assets.read(name))
        with zipfile.ZipFile(client) as c,zipfile.ZipFile(server) as s,zipfile.ZipFile(pack) as p:
            expected_client={n for n in names if keep_client(n)}
            expected_server={n for n in names if not n.startswith(('assets/','resourcepacks/'))}
            assert set(c.namelist())==expected_client
            assert set(s.namelist())==expected_server
            assert set(p.namelist())=={'pack.mcmeta','LICENSE'}|{n for n in names if n.startswith('assets/') and not language(n)}
            classes=0
            for name in names:
                data=payload(name)
                if name in expected_client and name!='fabric.mod.json':assert c.read(name)==data,name
                if name in expected_server and name!='fabric.mod.json':assert s.read(name)==data,name
                if name.startswith('assets/') and not language(name):assert p.read(name)==assets.read(name),name
                if name.endswith('.class'):
                    assert name in expected_client and name in expected_server
                    classes+=1
            assert {PurePosixPath(n).stem for n in c.namelist() if language(n)}==LANGUAGES
            assert all(z.testzip() is None for z in [c,s,p])
            language_files=[n for n in c.namelist() if '/lang/' in n]
        for key,target in optional.items():
            prefix=f'resourcepacks/{key}/'
            with zipfile.ZipFile(target) as z:
                assert z.testzip() is None
                for name in z.namelist():
                    if name!='LICENSE':assert z.read(name)==assets.read(prefix+name)
        shell_target=destination/shell.name
        with shell.open('rb') as input,shell_target.open('xb') as out:
            import shutil;shutil.copyfileobj(input,out)
        with zipfile.ZipFile(shell_target) as z:
            assert z.testzip() is None
            assert not any(n.startswith(('com/cobblemon/','META-INF/jars/','data/','assets/')) for n in z.namelist())
            assert json.loads(z.read('fabric.mod.json'))['environment']=='server'
        outputs=[client,server,shell_target,pack,*optional.values()]
        manifest={'upstream':'https://gitlab.com/cable-mc/cobblemon','tag':'1.8.4','commit':COMMIT,'sourceJar':{'path':str(source),'sha256':sha256(source),'bytes':source.stat().st_size},'classesPreservedInBothCompleteVariants':classes,'clientLanguages':language_files,'retainedFallbacks':[n for n in names if n.startswith('assets/') and not language(n) and fallback(n)],'outputs':{p.relative_to(destination).as_posix():{'sha256':sha256(p),'bytes':p.stat().st_size} for p in outputs},'scope':'Shell excludes gameplay, addons and old Cobblemon saves. Complete variants preserve every class, gameplay data and nested runtime from exact upstream source build.'}
        manifest['assetReference']={'path':str(asset_reference),'sha256':sha256(asset_reference),'resourceEntries':len(asset_names),'reason':'Reuse exact previously split 1.8.4 release resources; avoid inflating unprocessed source assets.'}
        (destination/'distribution-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (destination/'SHA256SUMS.txt').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in sorted(manifest['outputs'].items())),encoding='utf-8')
        print(json.dumps(manifest['outputs'],ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('destination',type=Path);parser.add_argument('--shell',type=Path,required=True);parser.add_argument('--asset-reference',type=Path,required=True)
    args=parser.parse_args();build(args.source,args.destination,args.shell,args.asset_reference)
