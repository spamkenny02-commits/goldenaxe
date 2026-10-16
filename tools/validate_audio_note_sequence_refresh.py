"""Replay retained original8357 fixtures with semantic M1 andactual opcode counts."""
import contextlib,ctypes as c,hashlib,io,json,struct,collections,sys
from actor_reference import ROOT
from audio_note_sequence_refresh import note_sequence_refresh
from source_rng_refresh import advance_refresh
from validate_audio_prefix_cost import SOURCE
from run_core import run

SPECS={
 'notes':('audio-note-sequence','audio_note_sequence_cost_report.json'),
 'commands':('audio-note-commands','audio_note_commands_cost_report.json'),
 'termination':('audio-note-sequence','audio_note_termination_cost_report.json'),
 'ownership':('audio-note-sequence','audio_note_ownership_cost_report.json')}

def main():
 kind=sys.argv[1] if len(sys.argv)>1 else 'notes';dirname,reference_name=SPECS[kind];reference=json.loads((ROOT/'analysis'/reference_name).read_text());expected=reference['cases']//2
 image=(ROOT/'validation'/dirname/kind/'source.sms').read_bytes();assert hashlib.sha256(image).hexdigest()==reference['fixture_sha256'];assert image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
 folder=ROOT/'validation/audio-note-sequence-refresh'/kind;folder.mkdir(parents=True,exist_ok=True);rom=folder/'source.sms'
 if rom.exists():assert rom.read_bytes()==image
 else:rom.write_bytes(image)
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_enveloperefresh_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_prefix_samples','gaw_envelope_return_de','gaw_envelope_did_unwind','gaw_prefix_refresh_before','gaw_prefix_refresh_after']:getattr(dll,name).restype=c.c_uint
 dll.gaw_prefix_tstates.restype=c.c_uint64;dll.gaw_prefix_m1_fetches.restype=c.c_uint64;dll.gaw_prefix_entry.restype=c.POINTER(c.c_uint8);dll.gaw_prefix_return.restype=c.POINTER(c.c_uint8)
 rows=[]
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];checked={};done=[];histogram=collections.Counter();unwinds=[0]
  def observe(f,r):
   if r[4]:done.append(f)
   n=dll.gaw_prefix_samples()
   if n==previous[0]:return
   assert n==previous[0]+1
   before=c.string_at(dll.gaw_prefix_entry(),400);after=c.string_at(dll.gaw_prefix_return(),400);case=int.from_bytes(r[:2],'little');prediction=note_sequence_refresh(image,before)
   cost=dll.gaw_prefix_tstates();fetches=dll.gaw_prefix_m1_fetches();entryR=dll.gaw_prefix_refresh_before();exitR=dll.gaw_prefix_refresh_after();de=dll.gaw_envelope_return_de();unwind=bool(dll.gaw_envelope_did_unwind())
   assert (cost,fetches,unwind,after)==(prediction['tstates'],prediction['m1_fetches'],prediction.get('unwind',False),prediction['state']),(kind,region,case,cost,fetches,prediction['m1_fetches'],unwind)
   assert de==prediction['de'],(kind,region,case,'DE',de,prediction['de'])
   assert exitR==advance_refresh(entryR,fetches+1),(kind,region,case,'R',entryR,exitR,fetches)
   checked[case]=struct.pack('<6I',cost,fetches,entryR,exitR,de,unwind)+hashlib.sha256(after).digest();histogram[fetches]+=1;unwinds[0]+=unwind;previous[0]=n
  with contextlib.redirect_stdout(io.StringIO()):run(rom,expected*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==expected,(kind,region,len(checked),expected);data=b''.join(checked[n] for n in range(expected));(folder/f'{region}-results.bin').write_bytes(data)
  rows.append(dict(region=region,cases=expected,caller_unwind_cases=unwinds[0],M1_histogram=dict(histogram),raw_sha256=hashlib.sha256(data).hexdigest()));print(kind,region,expected,'original8357 M1/R/cost/state/DE/unwind exact;',unwinds[0],'unwinds',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(image).hexdigest(),reference_report=reference_name,kind=kind,cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Exact retained fixture ROM hash equals prior validated cost report;original bank6 helpers/tables intact. Custom DI caller/synthetic fixed-ROM streams,IXDE40. Absolute M1,R,cost/all400 bytes,DE/unwind compare against original execution.','Generated semantic model adds explicit M1 arithmetic to audited8357 cost plans;duration multiplication uses4 or6+2*((scale-1)&255) fetches. No runtime ROM instruction interpretation. Notes/raw/rest/tie/loops/calls/returns,20 deterministic command families,F1/F2 inactive restoration andF3 ownership covered in separate suites.','R-dependent command families andF1/F2 restoration8211 nonzero remain unsupported. Full channels/IRQ fetch composition,load-entry R/native RNG replacement,waveform/hardware/full progression remain open.'])
 (ROOT/'analysis'/f'audio_note_{kind}_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
