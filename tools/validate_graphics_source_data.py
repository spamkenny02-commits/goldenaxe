"""Independent source buffer observation; keep original loader phase records intact."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import struct
from actor_reference import ROOT
from run_core import run
from validate_native_graphics_load import source_data_hashes
from validate_key_door_gameplay import initial_room,rle_planes,maps

def main():
    rom=(ROOT/'input/original.sms').read_bytes();expected=source_data_hashes(rom)
    _,ext,_,_,arrays,_=initial_room(rom);doors=json.loads((ROOT/'analysis/doors_reference.json').read_text())['direct_unconditional_doors']
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_graphicsdata_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_foreground_phase_samples.restype=c.c_uint;dll.gaw_foreground_phase_events.restype=c.POINTER(c.c_uint8)
    dll.gaw_graphics_hash_events.restype=c.POINTER(c.c_uint32)
    dll.gaw_foreground_m1_events.restype=c.POINTER(c.c_uint8)
    rows=[]
    for row in json.loads((ROOT/'analysis/native_graphics_load_report.json').read_text())['rows']:
        town=row['town'];mask=row['mask'];region=row['region']
        target=next(r[1] for r in json.loads((ROOT/'analysis/paid_passage_reference.json').read_text())['routes'] if r[0]==town)
        base=ROOT/f'validation/graphics-load-refresh/{town:02x}-{mask:02x}'
        metadata=json.loads((base/f'captures-{region}-sms/capture.json').read_text())
        old=(base/f'{region}-foreground-phase-records.bin').read_bytes();old_m1=(base/f'{region}-foreground-m1-records.bin').read_bytes()
        cycles=json.loads((base/f'{region}-cycle-events.json').read_text())
        start=next(e[2] for e in cycles if e[1]==0x16d0 and e[4]==target)
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
        writes=[by_address[(e['frame'],e['address'])] for e in metadata['test_ram_writes']]
        assert [dict(frame=f,address=a,byte_count=len(data)) for f,a,data in writes]==metadata['test_ram_writes']
        dll.gaw_timing_reset()
        def observe(frame,ram):
            if frame==4199:dll.gaw_timing_reset()
        folder=ROOT/f'validation/graphics-source-data/{town:02x}-{mask:02x}/{region}'
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/'input/original.sms',metadata['frames'],folder,set(),metadata['presses'],skip_intro=False,
                core=core,ram_writes=writes,ram_observer=observe,core_options=metadata['core_options'])
        count=dll.gaw_foreground_phase_samples();raw=c.string_at(dll.gaw_foreground_phase_events(),count*800)
        m1=c.string_at(dll.gaw_foreground_m1_events(),count*16)
        hashes=c.string_at(dll.gaw_graphics_hash_events(),count*20)
        assert raw==old,(town,mask,region,'source phases changed')
        # Global observer origin may differ between frontend runs; all deltas/R stay exact.
        origin=struct.unpack_from('<Q',m1)[0]-struct.unpack_from('<Q',old_m1)[0]
        for n in range(count):
            a=struct.unpack_from('<Q2I',m1,n*16);b=struct.unpack_from('<Q2I',old_m1,n*16)
            assert a[0]-b[0]==origin and a[1:]==b[1:]
        index=next(n for n in range(count) if struct.unpack_from('<Q',raw,n*800)[0]==0x24b9 and struct.unpack_from('<Q',raw,n*800+8)[0]>start)
        actual=list(struct.unpack_from('<5I',hashes,index*20));assert actual==expected,(town,mask,region,'source graphics buffers',actual,expected)
        (folder/'foreground.bin').write_bytes(raw);(folder/'m1.bin').write_bytes(m1);(folder/'data-hashes.bin').write_bytes(hashes)
        rows.append(dict(town=town,mask=mask,region=region,hashes=actual,record_index=index,source_phase_records_unchanged=True))
        print(town,mask,region,'source graphics/backup/terrain/SRAM hashes match',flush=True)
    report=dict(cases=len(rows),rows=rows,source_sha256=hashlib.sha256(rom).hexdigest(),
                limits=['6176 pattern bytes,912 base metatile bytes plus56 extra bytes,16 backup bytes,512 decoded terrain bytes and512 copied SRAM bytes.',
                        'Unused pattern/metatile gaps and previous terrain bytes512..1023 not initialized by this decode are excluded. Native1024-byte copy is checked separately.',
                        'Read-only observer; original source phases/R/M1 deltas unchanged. Controlled route setup preserved; not a natural full playthrough.'])
    (ROOT/'analysis/graphics_source_data_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
