"""Original restore tail with synthetic balanced frames and IRQ-edge phases."""
import argparse
import contextlib
import ctypes as c
import hashlib
import io
import itertools
import json
from actor_reference import ROOT
from run_core import run
from validate_audio_prefix_cost import generate,SOURCE
from native_wait_return_support import compile_helper,prepare_core,validate_record,irq_events,helpers


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pal-latched',action='store_true');args=parser.parse_args()
    folder,dll_native,function=compile_helper();core,dll=prepare_core()
    delays=sorted(set([0,1,127,511,1023,2047]+list(range(1800,2201,7))))
    if args.pal_latched:delays=list(range(2400,2701,7))
    records=[(delay&255,delay>>8,mode,comp,timer,pause,track) for delay,mode,comp,timer,pause,track in
             itertools.product(delays,[0,1,2],[0,1],[0,1,255],[0,1,128],[0,0x84])]
    rom,base=generate('restore',records,list(range(0x20,0x27)),0x3040,'wait-restore-boundaries-pal' if args.pal_latched else 'wait-restore-boundaries')
    image=bytearray(rom.read_bytes());image[0x3430:0x3430+400]=bytes(400);image[0xbb2]=0xfb
    stub=bytearray();labels={};fix=[]
    def emit(h):stub.extend(bytes.fromhex(h))
    def label(name):labels[name]=0x3040+len(stub)
    def jump(op,name):emit(op);fix.append((len(stub),name));emit('0000')
    emit('f3af322ec03a23de3203de3a24de3230c03a25de320ade3a26de3206de3e803205de3ea0d3bf3e81d3bfdbbfed4b20de78b128050b78b120fb')
    jump('21','finish');emit('e5')
    stub.extend(SOURCE[0xb95:0xba7])
    emit('3a22deb7');jump('ca','disabled');emit('fe01');jump('ca','enabled')
    emit('c3b20b');label('enabled');emit('fb00c3b30b');label('disabled');emit('c3b30b')
    label('finish');emit('f33e80d3bf3e81d3bfc9')
    for offset,name in fix:stub[offset:offset+2]=labels[name].to_bytes(2,'little')
    assert 0x3040+len(stub)<0x3100
    image[0x3040:0x3040+len(stub)]=stub
    assert image[0xbb3:0xbc6]==SOURCE[0xbb3:0xbc6] and image[0x137:0x227]==SOURCE[0x137:0x227]
    assert image[0x10000:0x14000]==SOURCE[0x10000:0x14000] and image[0x18000:0x1c000]==SOURCE[0x18000:0x1c000]
    rom.write_bytes(image);cases=[];rows=[]
    if args.pal_latched:
        old=json.loads((ROOT/'analysis/native_wait_restore_boundaries_report.json').read_text());assert old['helper_sha256']==helpers()
        cases=[row for row in json.loads((folder/'restore-cases.json').read_text()) if row['kind']!='restore-boundary-pal']
        rows=[row for row in old['rows'] if row.get('variant','base')!='pal-latched']
        for row in rows:
            row.setdefault('fixture',cases[0]['fixture']);row.setdefault('fixture_sha256',cases[0]['fixture_sha256']);row.setdefault('variant','base')
    for region in (['pal'] if args.pal_latched else ['auto','pal']):
        dll.gaw_timing_reset();done=[]
        def observe(frame,ram):
            if ram[4]:done.append(frame)
        with contextlib.redirect_stdout(io.StringIO()):
            run(rom,len(records)*10+100,base/region,set(),[],core=core,skip_intro=False,ram_observer=observe,
                core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(done))
        count=dll.gaw_wait_return_samples();assert count==len(records) and done,(region,count,len(records))
        raw=c.string_at(dll.gaw_wait_return_events(),count*2464);events=irq_events(dll);with_irq=0
        (base/f'{region}-returns.bin').write_bytes(raw)
        for n in range(count):
            row=validate_record(function,image,raw[n*2464:(n+1)*2464],events,(region,n))
            assert row['tail'] and row['caller']==labels['finish']
            row.update(kind='restore-boundary-pal' if args.pal_latched else 'restore-boundary',fixture=str(rom.relative_to(ROOT)),fixture_sha256=hashlib.sha256(image).hexdigest());cases.append(row)
            with_irq+=bool(row['expected'][7])
        (base/f'{region}-irq-entries.json').write_text(json.dumps(events,separators=(',',':'))+'\n')
        rows.append(dict(variant='pal-latched' if args.pal_latched else 'base',region=region,cases=count,IRQs_inside_restore=with_irq,return_sha256=hashlib.sha256(raw).hexdigest(),fixture=str(rom.relative_to(ROOT)),fixture_sha256=hashlib.sha256(image).hexdigest()))
        print(region,count,'source/native restore/caller phase,R,M1,state exact;',with_irq,'cases interrupt inside restore',flush=True)
    (folder/'restore-cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    report=dict(cases=len(cases),rows=rows,helper_sha256=helpers(),
                limits=['Original0BB3..0BC5/vector/audio/IRQ code intact. Custom balanced register/caller frame, VINT-enabled busy phases and DI/EI/EI-fallthrough contexts.',
                        'Preceding byte0BB2 changed to EI only for boundary fixture; tail itself unchanged. Pauses0/1/128,timers0/1/255,comp0/1,queued music0/84.',
                        '331 IRQ RAM bytes,400 audio,phase/R/M1/duration/IRQ entries compare; source mapper restoration observed separately.',
                        'No production clock wiring, native Z80 register emulation, hardware acknowledgement/waveforms/full natural progression proof.'])
    (ROOT/'analysis/native_wait_restore_boundaries_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
