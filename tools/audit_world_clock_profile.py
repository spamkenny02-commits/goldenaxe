"""Bind observed new-game timing differences; this is a diagnostic, not a pass gate."""
import hashlib,json
from actor_reference import ROOT

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source=ROOT/'input/original.sms';native=ROOT/'gaw-megadrive.bin'
    rom=source.read_bytes();cases=[];evidence=[]
    assert rom[0x7444:0x7452]==bytes.fromhex('cd9b77cd950b3a21c0e63f28f6c9')
    for suffix in ['', '-pal']:
        p=ROOT/f'validation/world_clock{suffix}_profile.json';d=json.loads(p.read_bytes())
        assert d['md_sha256']==sha(native) and d['source_sha256']==sha(source)
        assert d['production_roms_unmodified'] and not d['ram_injections']
        ev=d['source_events'];reset=[x for x in ev if x['pc']==0x0803]
        assert len(reset)==1 and reset[0]['frame']==2200 and reset[0]['hl']==0xc02f
        samples={tag:{x['frame']:x for x in rows} for tag,rows in d['traces'].items()}
        assert samples['sms'][2200]['clock']==255
        assert samples['sms'][2201]['clock']==0
        waits=[x for x in ev if x['pc']==0x7447]
        final=next(x for x in ev if x['pc']==0x7451)
        assert final['frame']==2400
        assert not any(x['pc'] in [0x07ee,0x07f4,0x0803] and x['frame']>2200 for x in ev)
        ready={tag:next(x for x in rows if x['state']==12 and x['room']==0x95) for tag,rows in d['traces'].items()}
        assert ready['md']['frame']-ready['sms']['frame']==-29
        native_waits=[x for x in d['native_events'] if x['function']=='wait_dialog_continue']
        assert len(native_waits)==2
        case=dict(region=d['region'],source_page_wait_entry=next(x['frame'] for x in ev if x['pc']==0x07f4),source_page_confirmation=2200,source_final_wait_entry=waits[0]['frame'],source_final_confirmation=2400,native_dialogue_wait_entries=[x['frame'] for x in native_waits],first_gameplay=ready,first_gameplay_frame_delta=-29,source_final_wait_uses_any_direction_or_button_without_clock_reset=True)
        cases.append(case);evidence.append(dict(file=str(p.relative_to(ROOT)),sha256=sha(p)))
    core=ROOT.parents[1]/'work/genesis-plus-gx'
    files=[ROOT/'tools/profile_world_clock.py',ROOT/'tools/audit_world_clock_profile.py',ROOT/'megadrive/src/main.c',core/'core/z80/z80.c',core/'core/m68k/m68kcpu.c',core/'genesis_plus_gx_clock_libretro.dll']
    report=dict(md_sha256=sha(native),source_sha256=sha(source),diagnostic_only=True,production_modified=False,cases=cases,evidence=evidence,files={str(p):sha(p) for p in files},full_game_ported=False,limits=['One natural new-game input sequence in each video region.','Selected instruction entry observations prove reset and waits but not every missed IRQ cause.','Merchant/NPC/Continue paths, smooth dialogue scrolling and complete initial framebuffer sequence need separate measurements.'])
    (ROOT/'validation/world_clock_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Natural new-game clock diagnostic verified: two regions; 29-frame early native room activation.')

if __name__=='__main__':main()
