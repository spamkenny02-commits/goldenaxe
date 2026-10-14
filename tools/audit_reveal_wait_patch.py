"""Exact reveal-only fresh IRQ patch and current targeted regression audit."""
import hashlib,json
from actor_reference import ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 prior=ROOT/'versions/v0179-d018ed93/source';before=(prior/'main.c').read_text()
 old='    u16 target[32],n,address,height,width;'
 assert before.count(old)==1
 expected=before.replace(old,old+'\n    u32 wait_started;')
 old='    wait_frame();VDP_setEnable(TRUE);'
 new='''    /* 0BA7..0BB3 waits for a fresh IRQ even while display is disabled. */
    wait_started=vtimer;wait_frame();while(vtimer==wait_started);
    VDP_setEnable(TRUE);'''
 assert expected.count(old)==1
 assert expected.replace(old,new)==(ROOT/'megadrive/src/main.c').read_text()
 unchanged=[]
 for p in (ROOT/'megadrive/src').iterdir():
  if p.is_file() and p.name!='main.c':assert p.read_bytes()==(prior/p.name).read_bytes();unchanged.append(p.name)
 baseline=ROOT/'analysis/reveal-wait-v0179/validation/reveal_wait_report.json';b=json.loads(baseline.read_text())
 assert b['md_sha256']==sha(ROOT/'versions/v0179-d018ed93/gaw-megadrive-v0179.bin')
 assert [c['rows'][0]['zero_tick_calls'] for c in b['cases']]==[216,224]
 assert all(all(t==1 for t in c['rows'][1]['ticks_by_start_scanline']) for c in b['cases'])
 source=(ROOT/'input/original.sms').read_bytes()
 assert source[0xba7:0xbb3]==bytes.fromhex('3e01322ec0fb3a2ec0b720fa')
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(rom).hexdigest()
 assert len(rom)==1048576 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
 checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 assert checksum==int.from_bytes(rom[0x18e:0x190],'big')
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:assert (ROOT/name).read_bytes()==rom
 evidence={}
 for name in ['standard_door_transitions_report.json','paid_passage_gameplay_report.json','save_report.json','resume_report.json','resume_capacity_report.json']:
  p=ROOT/'validation'/name;r=json.loads(p.read_text());assert r['md_sha256']==digest,(name,'stale evidence');evidence[name]=sha(p)
 transitions=json.loads((ROOT/'validation/standard_door_transitions_report.json').read_text())
 assert len(transitions['cases'])==4 and all(x['native_fade_in_frames']==18 for c in transitions['cases'] for x in c['transitions'])
 resume=json.loads((ROOT/'validation/resume_report.json').read_text());assert len(resume['contours'])==len(resume['images'])==16
 assert len(json.loads((ROOT/'validation/paid_passage_gameplay_report.json').read_text())['cases'])==20
 assert len(json.loads((ROOT/'validation/save_report.json').read_text())['cases'])==3
 report=dict(md_sha256=digest,checksum=f'{checksum:04X}',bytes=len(rom),only_reveal_initial_wait_changed=True,unchanged_production_files=unchanged,display_off_wait_baseline_sha256=sha(baseline),current_evidence=evidence,full_game_ported=False,limits=['Only initial reveal wait requires a fresh vtimer IRQ after wait_frame;global wait_frame/audio/loader/clock logic unchanged. Compiled scanline sweep validates candidate fresh gate semantics.','Eight live standard door transitions now have18 fade-in frames;16 phase-aligned death/Continue contour images match. Three-slot save/Continue,capacity and20 paid passage regressions pass. Full physical loading time,RNG,audio phase,hardware and natural playthrough remain unproved.'])
 (ROOT/'validation/reveal_wait_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Reveal-only fresh IRQ patch audited:',digest[:8],f'{checksum:04X}')

if __name__=='__main__':main()
