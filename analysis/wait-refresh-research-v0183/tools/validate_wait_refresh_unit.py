"""Reuse original wait boundary fixtures to check independently composed M1/R."""
import contextlib,ctypes as c,hashlib,io,json,struct
from actor_reference import ROOT
from wait_raster_prediction import predict_save_wait
from run_core import run

def main():
 source=(ROOT/'input/original.sms').read_bytes();core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_waitrefresh_libretro.dll';dll=c.CDLL(str(core))
 for name in ['gaw_foreground_phase_events','gaw_foreground_m1_events','gaw_wait_events']:getattr(dll,name).restype=c.POINTER(c.c_uint8)
 for name in ['gaw_foreground_phase_samples','gaw_wait_samples']:getattr(dll,name).restype=c.c_uint
 rows=[];folder=ROOT/'validation/wait-refresh-unit';folder.mkdir(exist_ok=True)
 for variant,report_name in [('wait-raster-unit','wait_raster_unit_report.json'),('wait-raster-unit-pal','wait_raster_pal_latched_unit_report.json')]:
  old=json.loads((ROOT/'analysis'/report_name).read_text());fixture=ROOT/f'validation/{variant}/wait/source.sms';assert hashlib.sha256(fixture.read_bytes()).hexdigest()==old['fixture_sha256']
  for row in old['rows']:
   region=row['region'];dll.gaw_timing_reset();previous=[0];done=[];waits=bytearray();m1=bytearray()
   def observe(f,r):
    if r[4]:done.append(f)
    count=dll.gaw_wait_samples()
    if count==previous[0]:return
    assert count==previous[0]+1;wraw=c.string_at(dll.gaw_wait_events(),count*112)[-112:];w=struct.unpack('<14Q',wraw)
    fore=dll.gaw_foreground_phase_samples();base=c.addressof(dll.gaw_foreground_phase_events().contents);mbase=c.addressof(dll.gaw_foreground_m1_events().contents);found={}
    for i in range(max(0,fore-16),fore):
     raw=c.string_at(base+i*800,800);pc,t=struct.unpack_from('<2Q',raw)
     if (pc,t) in [(0xb95,w[0]),(0xbb3,w[2])]:found[pc]=(raw,c.string_at(mbase+i*16,16))
    first,fmeta=found[0xb95];last,lmeta=found[0xbb3];startM,startR,_=struct.unpack('<Q2I',fmeta);endM,endR,_=struct.unpack('<Q2I',lmeta)
    p=predict_save_wait(source,struct.unpack_from('<12I',first,16),first[64:400],first[400:800],startR)
    assert (p['taken'],p['exits'])==w[4:6] and p['wall_master_cycles']==w[2]-w[0] and p['IRQ_tstates']*15==w[3]-w[1]
    assert p['refresh']==endR and p['foreground_M1']+p['IRQ_M1']==endM-startM,(variant,region,count,'M1/R')
    assert p['sound']==last[400:800] and all(p['ram'][i]==last[64+i] for i in range(336) if i not in [0x1b,0x20,0x21,0x22,0x23])
    waits.extend(wraw);m1.extend(fmeta+lmeta);previous[0]=count
   with contextlib.redirect_stdout(io.StringIO()):run(fixture,row['cases']*10+100,folder/f'{variant}-{region}',set(),[],core=core,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
   assert done and previous[0]==row['cases'] and hashlib.sha256(waits).hexdigest()==row['wait_sha256']
   (folder/f'{variant}-{region}-m1.bin').write_bytes(m1);rows.append(dict(variant=variant,region=region,cases=previous[0],M1_sha256=hashlib.sha256(m1).hexdigest()));print(variant,region,previous[0],'boundary wait M1/R exact;prior trace unchanged',flush=True)
 report=dict(cases=sum(r['cases'] for r in rows),rows=rows,production_ROM_changed=False,limits=['Reused fixtures include DI,EI+NOP andEI fallthrough,latched IRQ,skip/compensation andtimer0/1/255. Hardware/other modes/full game not proved.'])
 (ROOT/'analysis/wait_refresh_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
