"""Execute original04E1 and verify output/R sample for all seeds and R sweeps."""
import contextlib,ctypes as c,hashlib,io,json,struct
from actor_reference import ROOT
from source_rng_refresh import source_rng_from_entry,advance_refresh
from validate_audio_prefix_cost import generate,SOURCE
from run_core import run

def seed_fixture():
 image=bytearray(SOURCE);code=bytearray();labels={};fix=[]
 def emit(h):code.extend(bytes.fromhex(h))
 def label(name):labels[name]=0x3000+len(code)
 def jp(op,name):emit(op);fix.append((len(code),name));emit('0000')
 emit('f331f0df2100c01101c001ff1f3600edb0af32fcff32fdff3e0132feff3e04d3bf3e80d3bfafd3bf3e81d3bf')
 label('case');emit('2a00c02228c07ded4fcde1043205c02a00c0232200c07cb5');jp('c2','case')
 emit('3e013204c0');label('done');jp('c3','done')
 for pos,name in fix:code[pos:pos+2]=labels[name].to_bytes(2,'little')
 image[:3]=bytes.fromhex('c30030');image[0x3000:0x3000+len(code)]=code
 folder=ROOT/'validation/rng-refresh-seeds';folder.mkdir(exist_ok=True);rom=folder/'source.sms';rom.write_bytes(image);return rom,folder

def main():
 rom,folder=seed_fixture();matrix=[(seed&255,seed>>8,refresh) for seed in [0,1,0x8000,0xffff,0x1234,0x733c,0x7fff,0xaaaa] for refresh in range(256)]
 mrom,mfolder=generate('rng',matrix,[0x20,0x21,0x22],0x3040,'rng-refresh-matrix')
 image=bytearray(mrom.read_bytes());stub=bytes.fromhex('ed6b20de2228c03a22deed4fcde104c9');image[0x3040:0x3040+len(stub)]=stub;mrom.write_bytes(image)
 for fixture in [rom,mrom]:assert fixture.read_bytes()[0x4e1:0x4fe]==SOURCE[0x4e1:0x4fe]
 core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_rngrefresh_libretro.dll';dll=c.CDLL(str(core));dll.gaw_rng_refresh_samples.restype=c.c_uint;dll.gaw_rng_refresh_events.restype=c.POINTER(c.c_uint64)
 rows=[]
 for name,path,out,count,frames in [('all-seeds',rom,folder,65536,1000),('R-sweep',mrom,mfolder,len(matrix),len(matrix)*4+100)]:
  for region in ['auto','pal']:
   dll.gaw_timing_reset();previous=[0];group=[];checked=set();done=[];retained=bytearray();fallback=[0];high=[0]
   def observe(f,r):
    if r[4]:done.append(f)
    n=dll.gaw_rng_refresh_samples();events=dll.gaw_rng_refresh_events()
    for index in range(previous[0],n):
     e=tuple(events[index*8+k] for k in range(8));retained.extend(struct.pack('<8Q',*e));group.append(e)
     if e[0]!=0x4fd:continue
     assert [x[0] for x in group]==[0x4e1,0x4f7,0x4fd];entry,sample,end=group;case=entry[7]
     seed=case if name=='all-seeds' else matrix[case][0]|matrix[case][1]<<8;refresh=(case&255) if name=='all-seeds' else matrix[case][2]
     assert entry[3]==seed and entry[6]==advance_refresh(refresh,2)
     prediction=source_rng_from_entry(seed,entry[6]);assert entry[2]==sample[2]==end[2]
     assert advance_refresh(sample[6],1)==prediction['sampled_refresh'] #ED prefix second fetch occurs after observer.
     assert (end[3],end[4],end[5],end[6])==(prediction['seed'],prediction['seed'],prediction['value'],prediction['refresh_at_RET_entry']),(name,region,case,entry,sample,end,prediction)
     assert (end[1]-entry[1])//15+10==prediction['foreground_tstates']
     fallback[0]+=prediction['zero_seed_replaced'];high[0]+=bool(prediction['sampled_refresh']&128);checked.add(case);group.clear()
    previous[0]=n
    if n>12000 and not group:dll.gaw_timing_reset();previous[0]=0
   with contextlib.redirect_stdout(io.StringIO()):run(path,frames,out/region,set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
   assert done and len(checked)==count and not group,(name,region,len(checked),count)
   p=out/f'{region}-rng-records.bin';p.write_bytes(retained)
   rows.append(dict(kind=name,region=region,cases=len(checked),fallback_cases=fallback[0],high_bit_samples=high[0],raw_sha256=hashlib.sha256(retained).hexdigest(),fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
   print(name,region,len(checked),'original seed/R/output/cost exact',flush=True)
 report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(SOURCE).hexdigest(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),cases=sum(x['cases'] for x in rows),rows=rows,production_ROM_changed=False,full_game_ported=False,limits=['Original04E1 bytes unchanged. DI callers deliberately set R before CALL. Entry observer occurs after first M1 fetch; ED prefix second fetch is included in LD A,R output. All65536 seeds plus all256 R inputs for eight seeds,PAL/NTSC.','No IRQ inside helper. This validates local helper fetch counts and output,not R evolution from load entry or IRQ audio reader fetch counts. Initial R supplied; native SGDK RNG remains provisional. Hardware IRQ acknowledgement behavior not proved by this local GPG core.'])
 (ROOT/'analysis/rng_refresh_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
