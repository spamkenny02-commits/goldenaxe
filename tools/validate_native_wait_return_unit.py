"""Source wait entry through real caller, with old prefix captures unchanged."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import struct
from actor_reference import ROOT
from run_core import run
from native_wait_return_support import compile_helper,prepare_core,validate_record,irq_events,helpers


def main():
    folder,dll_native,function=compile_helper();core,dll=prepare_core();cases=[];rows=[]
    for variant,report_name in [('wait-raster-unit','wait_raster_unit_report.json'),('wait-raster-unit-pal','wait_raster_pal_latched_unit_report.json')]:
        reference=json.loads((ROOT/'analysis'/report_name).read_text());fixture=ROOT/f'validation/{variant}/wait/source.sms';image=fixture.read_bytes()
        assert hashlib.sha256(image).hexdigest()==reference['fixture_sha256']
        for old in reference['rows']:
            region=old['region'];dll.gaw_timing_reset();done=[]
            def observe(frame,ram):
                if ram[4]:done.append(frame)
            base=ROOT/f'validation/wait-return-unit/{variant}-{region}'
            with contextlib.redirect_stdout(io.StringIO()):
                run(fixture,old['cases']*10+100,base,set(),[],core=core,skip_intro=False,ram_observer=observe,
                    core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
            count=dll.gaw_wait_return_samples();assert count==old['cases'] and done,(variant,region,count)
            raw=c.string_at(dll.gaw_wait_return_events(),count*2464);events=irq_events(dll)
            (base/'returns.bin').write_bytes(raw)
            prior=ROOT/f'validation/native-source-wait-unit/{variant}-{region}'
            pairs=(prior/'pairs.bin').read_bytes();meta=(prior/'m1.bin').read_bytes()
            origin_shift=struct.unpack_from('<Q',raw,2400)[0]-struct.unpack_from('<Q',meta)[0]
            for n in range(count):
                record=raw[n*2464:(n+1)*2464]
                previous_meta=meta[n*32:(n+1)*32]
                assert record[:1600]==pairs[n*1600:(n+1)*1600],(variant,region,n,'prior wait state/phase changed')
                for offset in [0,16]:
                    assert struct.unpack_from('<Q',record,2400+offset)[0]-struct.unpack_from('<Q',previous_meta,offset)[0]==origin_shift
                    assert record[2408+offset:2416+offset]==previous_meta[offset+8:offset+16],(variant,region,n,'prior M1 delta/R changed')
                row=validate_record(function,image,record,events,(variant,region,n))
                row.update(kind='full-unit',fixture=str(fixture.relative_to(ROOT)),fixture_sha256=reference['fixture_sha256']);cases.append(row)
            (base/'returns.bin').write_bytes(raw);(base/'irq-entries.json').write_text(json.dumps(events,separators=(',',':'))+'\n')
            rows.append(dict(variant=variant,region=region,cases=count,return_sha256=hashlib.sha256(raw).hexdigest(),prior_prefix_identical=True,M1_global_origin_shift=origin_shift,prior_M1_delta_and_R_identical=True))
            print(variant,region,count,'complete native wait/caller phase,R,M1,RAM/audio exact; prefix capture unchanged',flush=True)
    (folder/'unit-cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    report=dict(cases=len(cases),rows=rows,helper_sha256=helpers(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),
                limits=['Full original wait through real return target. Existing entry/0BB3 states and M1 captures unchanged, plus new caller snapshot.',
                        '331 IRQ RAM bytes,400 audio,phase/R/M1/duration/IRQ entries compare. Native resources/caller variables are not Z80 physical registers.',
                        'Source bank restoration observed separately; production clock wiring/hardware/full progression still open.'])
    (ROOT/'analysis/native_wait_return_unit_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
