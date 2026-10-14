"""Bind the narrow paid-exit clock fix to source evidence and current ROM checks."""
import hashlib,json
from actor_reference import ROOT

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
 prior=ROOT/'versions/v0175-82520cf7';baseline=(prior/'paid_passage.inc').read_text()
 helper='''static void load_paid_passage_room(void)
{
    u32 started=vtimer;
    load_house_room(paid_passage_target,0);
    /* 16D0..1FA7: only the 1DE2/229C wait advances SMS C02F.
     * Conversion interrupts keep audio running without advancing game time. */
    world_clock_shift+=vtimer-started-1;
}
'''
 expected=baseline.replace('static bool check_paid_passage(',helper+'static bool check_paid_passage(',1)
 expected=expected.replace('        load_house_room(paid_passage_target,0);','        load_paid_passage_room();',1)
 assert expected==(ROOT/'megadrive/src/paid_passage.inc').read_text()
 unchanged=[]
 for path in prior.iterdir():
  current=ROOT/'megadrive/src'/path.name
  if path.name=='paid_passage.inc' or not current.is_file():continue
  if path.suffix not in ['.c','.inc','.h']:continue
  assert path.read_bytes()==current.read_bytes(),('unexpected source change',path.name)
  unchanged.append(path.name)
 assert 'main.c' in unchanged and 'actors.c' in unchanged
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(rom)
 assert len(rom)==1048576 and int.from_bytes(rom[0x1a4:0x1a8],'big')==len(rom)-1
 checksum=sum(int.from_bytes(rom[n:n+2],'big') for n in range(0x200,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum
 for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:
  assert (ROOT/name).read_bytes()==rom,('alias differs',name)
 evidence={}
 for name in ['paid_passage_native_loading_clock_report.json','paid_passage_unit_report.json','paid_passage_gameplay_report.json']:
  path=ROOT/'validation'/name;report=json.loads(path.read_text());assert report['md_sha256']==digest
  evidence[name]=sha(path.read_bytes())
 clock=json.loads((ROOT/'validation/paid_passage_native_loading_clock_report.json').read_text())
 assert clock['cases']==3072
 gameplay=json.loads((ROOT/'validation/paid_passage_gameplay_report.json').read_text())
 assert len(gameplay['cases'])==20
 units=json.loads((ROOT/'validation/paid_passage_unit_report.json').read_text());assert units['cases']==18528
 source_path=ROOT/'analysis/paid_passage_source_loading_clock_report.json';source=json.loads(source_path.read_text())
 assert source['cases']==24 and all(r['logical_ticks']==1 and r['original_wait_calls']==1 for r in source['rows'])
 assert source['md_sha256']==sha((prior/'gaw-megadrive-v0175.bin').read_bytes())
 report=dict(md_sha256=digest,checksum=f'{checksum:04X}',bytes=len(rom),only_paid_passage_clock_wrapper_changed=True,unchanged_archived_source_files=unchanged,current_evidence=evidence,source_clock_evidence_sha256=sha(source_path.read_bytes()),native_clock_cases=3072,rule_cases=18528,controlled_gameplay_cases=20,full_game_ported=False,limits=[
  'Source24 actual PAL/NTSC paid-exit paths demonstrate exactly one logical clock tick during16D0..1FA7; original0137 gates main IRQ work on C02E,while no-wait IRQ audio path01E3 leaves C02F unchanged.',
  'Native production patch retains one logical tick and removes vtimer ticks consumed by load_house_room. Actors/main and other archived modules unchanged.3072 compiled full-loader clock cases,18528 source/native rules and20 controlled actual payment/exit/menu cases pass on current ROM.',
  'This does not add the missing physical loading budget,fix reveal cadence,align earlier dialogue clocks,implement source refresh RNG or prove natural encounters/full progression. The uncontrolled baseline profiles remain diagnostic only.'])
 (ROOT/'validation/paid_passage_clock_patch_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Paid-exit logical clock patch audited; current ROM',digest[:8],flush=True)

if __name__=='__main__':main()
