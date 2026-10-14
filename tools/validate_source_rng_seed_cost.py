"""Execute original04E1 for every16-bit seed; check seed evolution and cycles."""
import contextlib,ctypes as c,hashlib,io,json
from actor_reference import ROOT
from source_rng_reference import source_rng
from run_core import run

def generate():
 image=bytearray((ROOT/'input/original.sms').read_bytes());code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(n):labels[n]=0x3000+len(code)
 def jp(op,n):emit(op);fix.append((len(code),n));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf')
 label('case');emit('af3202c02a00c02228c0cde1043e013202c00603')
 label('hold');emit('dbbfe680');jp('ca','hold');emit('05');jp('c2','hold')
 emit('2a00c0232200c07cb5');jp('c2','case');emit('af3202c03e013204c0')
 label('done');jp('c3','done')
 for p,n in fix:code[p:p+2]=labels[n].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 folder=ROOT/'validation/source-rng-seed-cost';folder.mkdir(exist_ok=True)
 rom=folder/'source.sms';rom.write_bytes(image);return rom,folder

def main():
 rom,folder=generate();source=(ROOT/'input/original.sms').read_bytes()
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_transition_libretro.dll'
 dll=c.CDLL(str(core));dll.gaw_timing_count.restype=c.c_uint
 dll.gaw_timing_events.restype=c.POINTER(c.c_uint64);regions=[]
 expected=bytearray()
 for seed in range(65536):
  m=source_rng(seed,0);expected.extend(m['seed'].to_bytes(2,'little'));expected.extend(m['foreground_tstates'].to_bytes(2,'little'))
 for region in ['auto','pal']:
  dll.gaw_timing_reset();previous=[0];starts={};checked=set();done=[];measured=bytearray(len(expected))
  def observe(f,r):
   if r[4]:done.append(f)
   seed=int.from_bytes(r[:2],'little');count=dll.gaw_timing_count();events=dll.gaw_timing_events()
   for n in range(previous[0],count):
    e=[events[n*8+k] for k in range(8)]
    if e[0]==0x4e1:starts[seed]=e
    elif e[0]==0x4fd:
     a=starts[seed];observed=((e[1]-a[1])-(e[2]-a[2]))//15+10
     model=source_rng(seed,0)
     assert (e[5],observed)==(model['seed'],model['foreground_tstates']),(region,seed,e[5],observed,model)
     measured[seed*4:seed*4+4]=e[5].to_bytes(2,'little')+observed.to_bytes(2,'little');checked.add(seed)
   previous[0]=count
   if count>24000 and r[2]:dll.gaw_timing_reset();previous[0]=0
  with contextlib.redirect_stdout(io.StringIO()):
   run(rom,65536*4+100,folder/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
  assert done and len(checked)==65536 and measured==expected,(region,len(checked),len(done))
  path=folder/f'{region}-seed-costs.bin';path.write_bytes(measured)
  regions.append(dict(region=region,cases=len(checked),seed_cost_table_sha256=hashlib.sha256(measured).hexdigest(),record_format='Seed-indexed4byte records:next_seed LE16,full04E1 T states LE16.'))
  print(region,len(checked),'original04E1 seed transitions and costs exact',flush=True)
 report=dict(source_sha256=hashlib.sha256(source).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(r['cases'] for r in regions),regions=regions,normal_cost_tstates=130,zero_fallback_cost_tstates=135,production_ROM_changed=False,full_game_ported=False,limits=[
  'Original04E1 unchanged; custom boot supplies each16-bit C028 seed. Read-only transition core observes04E1 and04FD; final RET10 included arithmetically. Interrupts disabled for this isolated recurrence test.',
  'All65536 seed transitions and normal/zero-fallback foreground costs match in both regions. Validates seed recurrence only; output LD A,R XOR L is represented with an explicit refresh argument but not validated by these HL/cycle observations.',
  'No faithful native refresh-register model or native RNG replacement is supplied. Initial RNG seed,caller instruction fetches and IRQ-dependent refresh evolution,natural actors/combat and full progression remain open.'])
 (ROOT/'analysis/source_rng_seed_cost_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
