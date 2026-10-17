"""Replay retained paid routes through actual source wait return targets."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import struct
from actor_reference import ROOT
from run_core import run
from validate_key_door_gameplay import initial_room,rle_planes,maps
from native_wait_return_support import compile_helper,prepare_core,validate_record,irq_events,helpers


def main():
    folder,dll_native,function=compile_helper();core,dll=prepare_core();source=(ROOT/'input/original.sms').read_bytes()
    _,ext,_,_,arrays,_=initial_room(source);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors']
    reference=json.loads((ROOT/'analysis/wait_refresh_report.json').read_text());cases=[];rows=[]
    dll.gaw_timing_count.restype=c.c_uint;dll.gaw_timing_events.restype=c.POINTER(c.c_uint64)
    dll.gaw_wait_samples.restype=c.c_uint;dll.gaw_wait_events.restype=c.POINTER(c.c_uint8)
    for row in reference['rows']:
        town=row['town'];mask=row['mask'];region=row['region']
        target=next(r[1] for r in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes'] if r[0]==town)
        old_base=ROOT/f'validation/wait-refresh/{town:02x}-{mask:02x}'
        metadata=json.loads((old_base/f'captures-{region}-sms/capture.json').read_text())
        old_waits=(old_base/f'{region}-save-wait-records.bin').read_bytes()
        starts=[struct.unpack_from('<Q',old_waits,n)[0] for n in range(0,len(old_waits),112)];required=set(starts)
        old_fore=(old_base/f'{region}-foreground-phase-records.bin').read_bytes();old_m1=(old_base/f'{region}-foreground-m1-records.bin').read_bytes();old_lookup={}
        for n in range(len(old_fore)//800):
            raw=old_fore[n*800:(n+1)*800];pc,time=struct.unpack_from('<2Q',raw)
            if pc in [0xb95,0xbb3]:old_lookup[(pc,time)]=(raw,old_m1[n*16:(n+1)*16])
        cells=bytearray(160);offset=int.from_bytes(arrays['world_room_index'][town*2:town*2+2],'little')
        rle_planes(arrays['world_room_streams'],offset,cells,0,1);osms,_=maps(cells,ext)
        door=next(d for d in doors if d['room']==town and d['target']==159)
        writes=[(3100,0x100+target,b'\1'),(3100,0xdd,bytes([20])),(3100,0x100+town,b'\0'),
                (3120,0xb9,town.to_bytes(2,'little')),(3120,0xa4,door['script_entry'].to_bytes(2,'little')),
                (3120,0x1c00,bytes(cells)),(3120,0x1600,osms),(3120,0x600,bytes(768)),
                (3120,0x304,b'\1'),(3120,0x301,b'\1'),(3120,0x303,b'\3'),(3120,0x30a,b'\0'),
                (3120,0x310,(door['y']<<8).to_bytes(2,'little')+((door['x']-1)<<8).to_bytes(2,'little')+bytes(2)+(256).to_bytes(2,'little')),
                (3400,0x310,(72<<8).to_bytes(2,'little')+(136<<8).to_bytes(2,'little')+bytes(4)),
                (3400,0x301,b'\1'),(3400,0x303,b'\3\0\0'),(3400,0x30a,b'\0'),(3100,0x200+target,bytes([mask]))]
        by_address={(f,a):(f,a,data) for f,a,data in writes}
        assert set(by_address)=={(entry['frame'],entry['address']) for entry in metadata['test_ram_writes']}
        writes=[by_address[(entry['frame'],entry['address'])] for entry in metadata['test_ram_writes']]
        assert [dict(frame=f,address=a,byte_count=len(data)) for f,a,data in writes]==metadata['test_ram_writes']
        dll.gaw_timing_reset();cache={};previous=[0,0];cycles=[];frame_at=[0]
        def observe(frame,ram):
            if frame==4199:
                dll.gaw_timing_reset();previous[:]=[0,0];cache.clear();cycles.clear()
            frame_at[0]=frame;count=dll.gaw_wait_return_samples();pointer=c.addressof(dll.gaw_wait_return_events().contents)
            for n in range(previous[0],count):
                data=c.string_at(pointer+n*2464,2464);start=struct.unpack_from('<Q',data,8)[0]
                if start in required:cache[start]=data
            previous[0]=count
            count=dll.gaw_timing_count();pointer=dll.gaw_timing_events()
            if 4200<=frame<=metadata['frames']:
                cycles.extend([frame]+[pointer[n*8+k] for k in range(8)] for n in range(previous[1],count))
            previous[1]=count
        base=ROOT/f'validation/wait-return-live/{town:02x}-{mask:02x}/{region}'
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/'input/original.sms',metadata['frames']+2,base,set(),[tuple(p) for p in metadata['presses']],
                core=core,ram_writes=writes,skip_intro=False,ram_observer=observe,core_options=metadata['core_options'],
                stop_when=lambda:frame_at[0]>=metadata['frames'] and required.issubset(cache))
        (base/'cycle-events.json').write_text(json.dumps(cycles,separators=(',',':'))+'\n')
        expected_cycles=json.loads((old_base/f'{region}-cycle-events.json').read_text())
        assert required==set(cache) and cycles==expected_cycles,(town,mask,region,'source route changed',len(cache),len(required),len(cycles),len(expected_cycles),
            next(((a,b) for a,b in zip(cycles,expected_cycles) if a!=b),None))
        all_waits=c.string_at(dll.gaw_wait_events(),dll.gaw_wait_samples()*112)
        wait_lookup={struct.unpack_from('<Q',all_waits,n)[0]:all_waits[n:n+112] for n in range(0,len(all_waits),112)}
        assert b''.join(wait_lookup[start] for start in starts)==old_waits
        events=irq_events(dll);raw=b''.join(cache[start] for start in starts);origin_shift=None;callers={}
        (base/'returns.bin').write_bytes(raw)
        for n,start in enumerate(starts):
            record=cache[start];restore_time=struct.unpack_from('<Q',record,808)[0]
            first,fmeta=old_lookup[(0xb95,start)];restore,rmeta=old_lookup[(0xbb3,restore_time)]
            assert record[:1600]==first+restore,(town,mask,region,n,'old prefix changed')
            if origin_shift is None:origin_shift=struct.unpack_from('<Q',record,2400)[0]-struct.unpack_from('<Q',fmeta)[0]
            for offset,meta in [(2400,fmeta),(2416,rmeta)]:
                assert struct.unpack_from('<Q',record,offset)[0]-struct.unpack_from('<Q',meta)[0]==origin_shift and record[offset+8:offset+16]==meta[8:16]
            case=validate_record(function,source,record,events,(town,mask,region,n));case.update(kind='full-live',fixture='input/original.sms',fixture_sha256=metadata['rom_sha256'])
            cases.append(case);callers[f"{case['caller']:04X}"]=callers.get(f"{case['caller']:04X}",0)+1
        (base/'cycle-events.json').write_text(json.dumps(cycles,separators=(',',':'))+'\n');(base/'irq-entries.json').write_text(json.dumps(events,separators=(',',':'))+'\n')
        rows.append(dict(town=town,mask=mask,region=region,cases=len(starts),callers=callers,return_sha256=hashlib.sha256(raw).hexdigest(),prior_source_cycles_and_prefix_unchanged=True,M1_global_origin_shift=origin_shift))
        print(town,mask,region,len(starts),'complete native wait to actual caller exact; old source route/prefix unchanged',flush=True)
    (folder/'live-cases.json').write_text(json.dumps(cases,separators=(',',':'))+'\n')
    report=dict(cases=len(cases),rows=rows,helper_sha256=helpers(),core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),
                limits=['Controlled paid routes replayed with identical inputs/RAM fixtures; all old source cycles and prefix checkpoints unchanged.',
                        'Full wait through caller opcode: 331 RAM,400 audio,phase,R,M1,time and IRQ offsets. Observed initial context remains an input.',
                        'Source bank restoration checked separately; native C caller resources/register allocation remain its own. Production clock wiring/hardware/full progression not proved.'])
    (ROOT/'analysis/native_wait_return_live_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
