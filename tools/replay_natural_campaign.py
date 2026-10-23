"""Cold fixed-input replay of a complete recorded campaign prefix, without feedback."""
import argparse,contextlib,io,json,time
from run_core import ROOT,run
from archive_lossless_evidence import sha

def main():
 p=argparse.ArgumentParser();p.add_argument('--trace',required=True);a=p.parse_args();folder=(ROOT/'validation'/a.trace).resolve();assert folder.is_relative_to(ROOT/'validation')
 capture=json.loads((folder/'capture.json').read_bytes());controls=json.loads((folder/'controls.json').read_bytes());end=capture['frames'];assert not capture['test_ram_writes'] and capture['sram_input'] is None
 rom=ROOT/'input/original.sms' if folder.name.startswith('sms') else ROOT/'gaw-megadrive.bin';assert sha(rom.read_bytes())==capture['rom_sha256']
 presses=list(map(tuple,capture['presses']))
 for i,row in enumerate(controls):
  stop=controls[i+1]['frame']-1 if i+1<len(controls) else end
  presses.extend((row['frame'],stop,b) for b in row['buttons'])
 out=folder.with_name(folder.name+'-fixed-replay');assert not out.exists();started=time.perf_counter()
 with contextlib.redirect_stdout(io.StringIO()):run(rom,end,out,{end},presses,skip_intro=False,core_options=capture['core_options'])
 for stem,ext in [('ram','bin'),('frame','png')]:assert (folder/f'{stem}_{end:05d}.{ext}').read_bytes()==(out/f'{stem}_{end:05d}.{ext}').read_bytes(),(folder.name,stem)
 r=dict(passed=True,rom_sha256=sha(rom.read_bytes()),trace=folder.relative_to(ROOT).as_posix(),frames=end,whole_ram_bytes=(out/f'ram_{end:05d}.bin').stat().st_size,final_png_exact=True,elapsed_seconds=time.perf_counter()-started,fixed_intervals=len(presses),feedback_reads=False,ram_injections=False,evidence={n:sha((folder/n).read_bytes()) for n in ['capture.json','controls.json']});(out/'replay_report.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
if __name__=='__main__':main()
