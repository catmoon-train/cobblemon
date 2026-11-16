"""Guarded delivery of this task's Cobblemon subtree, preserving previous outputs."""
from pathlib import Path
import argparse, hashlib, json, shutil
OLD={
'Cobblemon-fabric-1.8.4+1.21.1-client-full-split.jar':'543dbcc1884400e84238a58db3c0e41b62093f41e08bef5a90d568fbcad7a981',
'Cobblemon-fabric-1.8.4+1.21.1-server-full-split.jar':'add9b33e19ebd35f25ba843427121116868aebc8dbe45c06a5ecca47aa458bbe',
'Cobblemon-fabric-1.8.4+1.21.1-server-shell.jar':'bc68e817ec458b7b10c38ee24bad074bdf728c552e00c21cb4db4b24be42a3b3'}
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inventory(root):return {p.relative_to(root).as_posix():digest(p) for p in root.rglob('*') if p.is_file()}
def main():
 p=argparse.ArgumentParser();p.add_argument('stage',type=Path);p.add_argument('destination',type=Path);p.add_argument('--backup',type=Path,required=True);a=p.parse_args()
 assert a.destination.name=='Cobblemon-1.8.4' and a.destination.parent.name=='待更新'
 assert a.destination.is_dir() and not a.backup.exists()
 before=inventory(a.destination)
 for n,h in OLD.items():assert before.get(n)==h,('Previous output changed; refusing replacement',n)
 previous=json.loads((a.destination/'distribution-manifest.json').read_text(encoding='utf-8'))
 for n,v in previous['outputs'].items():assert before.get(n)==v['sha256'],('Previous manifest mismatch',n)
 staged=inventory(a.stage)
 for n in ['client','server-full','server-shell']:
  f=a.stage/n/'Cobblemon-fabric-1.8.4+1.21.1.jar';assert f.is_file(),f
 shutil.copytree(a.destination,a.backup)
 assert inventory(a.backup)==before,'Backup mismatch'
 # Preserve all unrelated files even inside the task subtree; replace only staged paths.
 for n,h in staged.items():
  src=a.stage/n;dst=a.destination/n
  if dst.exists():assert digest(dst)==before[n],('Concurrent change',dst)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  assert digest(dst)==h,dst
 for n,h in OLD.items():
  f=a.destination/n;assert digest(f)==h;f.unlink()
 after=inventory(a.destination)
 assert all(after[n]==h for n,h in staged.items())
 assert all(after[n]==h for n,h in before.items() if n not in staged and n not in OLD)
 print(json.dumps({'delivered':str(a.destination),'backup':str(a.backup),'files':len(staged),'verified':True},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
