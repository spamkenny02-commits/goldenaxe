"""Verify complete hero model on real unpatched six-route paid exits."""
import hashlib,json
from actor_reference import ROOT
from hero_initialization_cost import hero_initialization_cost
from profile_paid_passage_loader_phases import main as profile

def main():
 source=(ROOT/'input/original.sms').read_bytes();rows=[]
 routes=json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes']
 for town,target,*_ in routes:
  for mask in [0,255]:
   output=f'paid-passage-hero-init/{town:02x}-{mask:02x}'
   profile(town,mask,output,'genesis_plus_gx_hero_libretro.dll')
   folder=ROOT/'validation'/output
   for region in ['auto','pal']:
    files=sorted(folder.glob(f'{region}-hero-*-before.bin'));assert len(files)==1,(town,mask,region,files)
    before=files[0].read_bytes();after=files[0].with_name(files[0].name.replace('-before','-after')).read_bytes()
    assert int.from_bytes(before[0xb9:0xbb],'little')==target
    model=hero_initialization_cost(source,before);parts=model['components']
    events=json.loads((folder/f'{region}-cycle-events.json').read_text())
    def measured(start,end):
     a=next(e for e in events if e[1]==start and e[4]==target)
     b=next(e for e in events if e[1]==end and e[2]>a[2])
     delta=(b[2]-a[2])-(b[3]-a[3]);assert delta%15==0
     return delta//15
    checks=[('initial',0x2c63,0x369f,parts['initial_fields']+17),
            ('pose',0x369f,0x2c8a,parts['pose']-17),
            ('auxiliary_and_defense',0x2c8a,0x2ca6,parts['auxiliary_clear']+parts['defense']),
            ('attack_contact_terrain',0x2ca6,0x2d3e,parts['attack']+parts['contact_copy']+parts['water_collision_flags']+parts['terrain_classifier']-13),
            ('earth_and_return',0x2d3e,0x24e7,13+parts['earth_collision_flags_and_return']),
            ('complete',0x2c63,0x24e7,model['foreground_tstates'])]
    for name,start,end,expected in checks:assert measured(start,end)==expected,(town,mask,region,name,measured(start,end),expected)
    indices=list(range(0x41,0x6c))+list(range(0x300,0x4b0))
    assert all(model['ram'][i]==after[i] for i in indices),(town,mask,region,'hero/collision RAM')
    rows.append(dict(town=town,target=target,mask=mask,region=region,foreground_tstates=model['foreground_tstates'],components=parts,entry_sha256=hashlib.sha256(before).hexdigest(),return_sha256=hashlib.sha256(after).hexdigest(),snapshot_path=str(files[0].relative_to(ROOT))))
   print('Live hero model verified',hex(town),hex(target),mask,flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(source).hexdigest(),cases=len(rows),independent_phase_comparisons=len(rows)*6,compared_RAM_bytes_per_case=475,rows=rows,production_ROM_changed=False,full_game_ported=False,limits=[
  'Actual unpatched source six paid-exit routes,two extreme destination enemy masks,both regions. Entrance/hero/initial clock and pre-entry mask controlled;no per-choice RNG mutation or hero-state repair during loading.',
  'Read-only core captures full8192-byte RAM at2C63 entry and24E7 return. Model predicts full hero cost,475 relevant/preserved RAM bytes and five independent internal phase costs. Source IRQ work is subtracted,not simulated.',
  'Native production remains v0177. Model is not integrated as a delay;source audio IRQ costs/phase alignment,refresh RNG,physical hardware and whole natural progression remain incomplete.'])
 (ROOT/'analysis/live_hero_initialization_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(len(rows),'live hero initializations and',len(rows)*6,'phases exact',flush=True)

if __name__=='__main__':main()
