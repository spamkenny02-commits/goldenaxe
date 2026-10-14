"""Bind the room-resource milestone and focused regressions to one cartridge."""
import hashlib,json,re
from extract_world import ROOT,initial_room


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=sha(data)
    original=(ROOT/'input/original.sms').read_bytes()
    assert sha(original)=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    assert len(data)==524288
    for name in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin']:
        assert (ROOT/name).read_bytes()==data,name
    assert int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[i:i+2],'big') for i in range(0x200,len(data),2))&65535
    assert int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in
        (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    *_,arrays,_=initial_room(original)
    for name in ['world_room_index','world_room_streams']:
        address=sy[name];assert data[address:address+len(arrays[name])]==arrays[name],name
    names=['dungeon_world_assets_report.json','world_loader_harness_report.json',
        'scroll_objects_report.json','scroll_objects-pal_report.json',
        'timing_report.json','timing-pal_report.json',
        'title_cadence_report.json','title_cadence-pal_report.json',
        'intro_report.json','intro-pal_report.json']
    reports=[]
    for name in names:
        raw=(ROOT/'validation'/name).read_bytes();report=json.loads(raw)
        assert report['md_sha256']==digest,name
        reports.append(dict(file=name,sha256=sha(raw)))
    source=json.loads((ROOT/'validation/dungeon_world_assets_report.json').read_bytes())
    assert source['maps_checked']==512 and source['source_z80_decoders_executed']==['032A','0C00','81C0']
    for name,digest_value in source['files'].items():assert sha((ROOT/name).read_bytes())==digest_value,name
    native=json.loads((ROOT/'validation/world_loader_harness_report.json').read_bytes())
    assert native['rooms_checked']==512 and native['hardware_background_uploads_checked']==512
    for name,digest_value in native['source_copies'].items():assert sha((ROOT/'megadrive/src'/name).read_bytes())==digest_value,name
    for suffix in ['', '-pal']:
        timing=json.loads((ROOT/f'validation/timing{suffix}_report.json').read_bytes())
        assert all(x['differing_state_frames']==0 for x in timing['natural_input_sequences'])
        assert timing['enemy']['differing_motion_counter_frames']==0
        scroll=json.loads((ROOT/f'validation/scroll_objects{suffix}_report.json').read_bytes())
        assert len(scroll['cases'])==4 and all(x['checks']['md']['nonhero_sprite_errors']==0 for x in scroll['cases'])
    report=dict(md_sha256=digest,md_size=len(data),room_index_entries=512,
        compiled_room_stream_bytes=len(arrays['world_room_streams']),
        rom_aliases_exact=True,additive_checksum_valid=True,current_targeted_reports=reports,
        source_z80_maps_verified=512,native_68000_base_room_loads_verified=512,
        full_game_ported=False,natural_dungeon_entry_verified=False,
        limits=['Class-2 resources and native loader are exercised in a separate harness.',
            'The production cartridge contains all map streams; unreachable class-2 graphics may be removed by LTO until entrance integration.',
            'Door conditions, quest-dependent cell edits, dungeon scrolling, puzzles, bosses and natural dungeon progression remain incomplete.',
            'Source animation initializes 576 bytes; the uninitialized remainder of its 1024-byte scratch copy is not invented.'])
    (ROOT/'validation/dungeon_world_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('512 compiled map entries and ten current reports bound; natural dungeon progression remains unverified')


if __name__=='__main__':main()
