"""Controlled ownership/context fixtures for source 7320..7356, normal menu input."""
import argparse,contextlib,io,json
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',required=True);p.add_argument('--pal',action='store_true');p.add_argument('--diagnostic',action='store_true');args=p.parse_args()
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');results=[]
    for slot,owned,graphics in [(1,0,0),(1,1,2),(9,1,0),(9,1,1),(9,1,2),(11,1,0),(11,1,1),(11,1,2)]:
        expected=slot if owned and not(slot in [9,11] and graphics) else 0
        case=[]
        for sms in [True,False]:
            tag='sms' if sms else 'md';rom=ROOT/('input/original.sms' if sms else 'gaw-megadrive.bin')
            folder=ROOT/f'validation/inventory-acceptance-{args.tag}/{slot}-{owned}-{graphics}-{tag}';assert not folder.exists()
            items=bytearray(17);items[0]=1;items[slot]=owned
            writes=[(2800,0xe0 if sms else sy['hero_items'],bytes(items)),(2800,0x600 if sms else sy['world_actor_state'],bytes(768)),(2820,0x40 if sms else sy['world_graphics_class'],bytes([graphics]) if sms else graphics.to_bytes(2,'big'))]
            if not sms:writes.append((2800,sy['hero_weapon_level'],(owned if slot==1 else 0).to_bytes(2,'big')))
            nav=[];f=2850
            for b in [7]*(slot%4)+[5]*(slot//4):nav.append((f,f+1,b));f+=10
            confirm=f+10;nav.append((confirm,confirm+1,8));rows=[]
            def observe(frame,r):
                if frame<2840:return
                word=lambda n:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(2)),'big')
                audio=bytes(r[0x1e00:0x1f90]) if sms else bytes(r[(sy['sound_ram']+i)^1] for i in range(400))
                rows.append(dict(frame=frame,game=r[0x1d] if sms else word('game_state'),slot=r[0xa0] if sms else word('inventory_slot'),selected=r[0xdf] if sms else word('hero_selected_item'),request=r[0x1e08] if sms else word('sound_effect_request'),audio_command=audio[5]))
            with contextlib.redirect_stdout(io.StringIO()):run(rom,confirm+30,folder,{confirm+30},([(200,220,0)] if sms else [])+PRESSES[:8]+[(2800,2805,0)]+nav,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if args.pal else 'auto'})
            assert rows[-1]['game']==16 and rows[-1]['slot']==slot,(tag,slot,rows[-1])
            commands=sorted(set(x['request'] for x in rows if x['frame']>=confirm)|set(x['audio_command'] for x in rows if x['frame']>=confirm))
            record=dict(tag=tag,selected=rows[-1]['selected'],commands=commands,expected=expected,selection_pass=rows[-1]['selected']==expected)
            record['sound_pass']=(0xab if expected else 0xa1) in commands
            (folder/'states.json').write_text(json.dumps(rows,indent=2)+'\n');case.append(record)
        results.append(dict(slot=slot,owned=owned,graphics=graphics,cases=case))
    report=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=all(x['selection_pass'] and x['sound_pass'] for c in results for x in c['cases']),controlled_ram_fixtures=True,region='pal' if args.pal else 'auto',results=results)
    (ROOT/f'analysis/inventory_acceptance_{args.tag}_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not args.diagnostic:assert report['passed']

if __name__=='__main__':main()
