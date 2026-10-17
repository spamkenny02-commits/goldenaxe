"""Remove reproducible, untracked emulator save states; retain all other files."""
import argparse,collections,json,os,re,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 target=(ROOT/'validation').resolve()
 assert target.parent==ROOT.resolve() and target.name=='validation'
 tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8').split('\0'))
 before=collections.Counter();removed=collections.Counter();failures=[];files=0;started=time.monotonic()
 for directory,dirs,names in os.walk(target,followlinks=False):
  dirs[:]=[d for d in dirs if not (Path(directory)/d).is_symlink()]
  for name in names:
   if not re.fullmatch(r'state_[0-9]+\.bin',name):continue
   p=Path(directory)/name;rel=p.relative_to(ROOT).as_posix()
   if rel in tracked or p.is_symlink():continue
   resolved=p.resolve();assert resolved.is_relative_to(target) and resolved.parent!=target.parent
   size=p.stat().st_size;before[str(p.parent.relative_to(target))]+=size;files+=1
   if args.apply:
    try:p.unlink();removed[str(p.parent.relative_to(target))]+=size
    except OSError as error:failures.append(dict(file=rel,error=str(error)))
   if files%10000==0:print(files,'save states',round(sum(before.values())/1073741824,2),'GiB',flush=True)
 report=dict(applied=args.apply,scope=str(target),pattern='state_[0-9]+.bin',tracked_files_excluded=True,symlinks_excluded=True,files=files,bytes=sum(before.values()),removed_bytes=sum(removed.values()),failures=failures,seconds=round(time.monotonic()-started,2),largest_directories=before.most_common(20),preserved=['All tracked files, numbered ROMs and Git history','All analysis archives, source code and input ROM','RAM, VRAM, CRAM, VDP registers, screenshots and reports in validation'])
 (target/('cleanup_states_report.json' if args.apply else 'cleanup_states_plan.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2),flush=True)
 assert not failures

if __name__=='__main__':main()
