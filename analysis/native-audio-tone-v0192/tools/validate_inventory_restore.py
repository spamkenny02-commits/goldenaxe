"""Exercise normal inventory open/close in initial exteriors and village houses."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES
from audit_item_reward_visuals import sms_pixels,md_pixels

def main():
    baseline='--baseline' in sys.argv
    md=ROOT/('versions/v0095-f2f9fdc1/gaw-megadrive-v0095.bin' if baseline else 'gaw-megadrive.bin')
    symbols=ROOT/('analysis/inventory-restore-baseline-v0095/symbol.txt' if baseline else 'megadrive/out/release/symbol.txt')
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in symbols.read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    cases=[]
    for region in ['auto','pal']:
      for name,route,expected_room,kind in [('exterior',PRESSES[:8],0x95,0),('first_house',PRESSES[:11]+[(2950,2958,7),(3000,3020,4)],0,1),('second_house',PRESSES[:11]+[(2950,2965,5),(3000,3023,6),(3050,3061,4),(3100,3110,4)],2,1)]:
        data={};tiles={}
        for tag,rom in [('sms',ROOT/'input/original.sms'),('md',md)]:
            rows={};patterns={}
            def observe(f,r):
                if f not in [3300,3370,3440,3470]:return
                def word(k):return int.from_bytes(bytes(r[(sy[k]+i)^1] for i in range(2)),'big')
                rows[f]=dict(animated_tile=r[0x9e0] if tag=='sms' else r[(sy['scratch']+0x1e0)^1],state=r[0x1d] if tag=='sms' else word('game_state'),room=int.from_bytes(r[0xb9:0xbb],'little') if tag=='sms' else word('room_id'))
            def vram(f,v):
                if f in rows:patterns[f]=[sms_pixels(v,n) if tag=='sms' else md_pixels(v,16+n) for n in range(124)]
            folder=ROOT/f'validation/inventory-restore-{name}-{region}-{tag}{"-baseline" if baseline else ""}'
            inputs=([(200,220,0)] if tag=='sms' else [])+route+[(3350,3355,0),(3400,3405,0)]
            with contextlib.redirect_stdout(io.StringIO()):run(rom,3470,folder,{3300,3370,3440,3470},inputs,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
            assert rows[3300]['room']==expected_room and rows[3300]['state']==12,(name,tag,rows)
            assert rows[3370]['state']==16 and rows[3440]['state']==12,(name,tag,rows)
            data[tag]=rows;tiles[tag]=patterns
        diffs={str(f):[n for n in range(124) if tiles['sms'][f][n]!=tiles['md'][f][n]] for f in [3300,3440,3470]}
        static_diffs={str(f):[n for n in diffs[str(f)] if not (kind==1 and data['sms'][f]['animated_tile']<=n<data['sms'][f]['animated_tile']+4)] for f in [3300,3440,3470]}
        assert not static_diffs['3300'],(name,region,'static background already wrong before menu',diffs)
        early_native_changes=[n for n in range(124) if tiles['md'][3300][n]!=tiles['md'][3440][n]]
        early_static_changes=[n for n in early_native_changes if not (kind==1 and data['sms'][3300]['animated_tile']<=n<data['sms'][3300]['animated_tile']+4)]
        if not baseline:assert not early_static_changes and not static_diffs['3440'] and not static_diffs['3470'],(name,region,diffs,early_native_changes)
        cases.append(dict(name=name,region=region,room=expected_room,graphics_class=kind,normal_controller_route=True,inventory_open_and_closed=True,background_pattern_difference_indices=diffs,static_background_pattern_difference_indices=static_diffs,animated_source_tile=data['sms'][3300]['animated_tile'],early_native_pattern_changes_from_before_menu=early_native_changes,early_native_static_pattern_changes_from_before_menu=early_static_changes,settled_background_tiles_compared=124))
        print(name,region,{f:len(v) for f,v in diffs.items()},flush=True)
    result=dict(md_sha256=hashlib.sha256(md.read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),cases=cases,diagnostic_only=baseline,full_game_ported=False,limits=['All static background tiles among the first 124 match source; four animated house tiles are identified by original C9E0 and excluded from static equality. All raw differences remain recorded. Native early restored static tiles match its pre-menu tiles. Complete framebuffer and animated phase are outside this check.','Initial exterior and two village houses reached by normal input; dungeon inventory restoration is not exercised by these routes.'])
    (ROOT/f'validation/inventory_restore{"_baseline" if baseline else ""}_report.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
