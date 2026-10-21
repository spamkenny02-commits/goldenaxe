"""Boot-to-boss/crystal/exit evidence, including fixed-input fresh-process replays."""
import contextlib,gzip,io,json,subprocess,sys
from PIL import Image
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols
from audit_item_reward_visuals import sms_pixels,md_pixels

BASE=ROOT/'validation/natural-dungeon-combat'
FINAL=['sms-auto-17','md-auto-22'];MODAL=['sms-auto-15','md-auto-21']

def read(path):
    if path.exists():return path.read_bytes()
    name=path.relative_to(ROOT).as_posix()
    for archive in [ROOT/'analysis/first-dungeon-v0226',ROOT/'analysis/terrain-publication-v0225']:
        if not (archive/'manifest.json').exists():continue
        m=json.loads((archive/'manifest.json').read_bytes())
        if name in m['files']:
            raw=(archive/name).read_bytes();assert sha(raw)==m['files'][name];return raw
        if name in m['compressed']:
            i=m['compressed'][name];encoded=(archive/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'];return raw
    raise FileNotFoundError(path)

def replay(name):
    assert name in FINAL
    folder=BASE/name;capture=json.loads(read(folder/'capture.json'));end=capture['frames'];controls=json.loads(read(folder/'controls.json'));timeline=[()]*(end+1)
    for n,item in enumerate(controls):
        stop=controls[n+1]['frame']-1 if n+1<len(controls) else end
        timeline[item['frame']:stop+1]=[tuple(item['buttons'])]*(stop-item['frame']+1)
    out=BASE/(name+'-story-replay-fresh');assert not out.exists(),out
    rom=ROOT/'input/original.sms' if name.startswith('sms') else ROOT/'gaw-megadrive.bin';assert sha(rom.read_bytes())==capture['rom_sha256']
    with contextlib.redirect_stdout(io.StringIO()):run(rom,end,out,{end},capture['presses'],input_provider=lambda f:timeline[f],core_options=capture['core_options'])
    (out/'controls.json').write_bytes(read(folder/'controls.json'))

def main():
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');cases=[];records=[];evidence={};modal_records=[]
    for name,modal in zip(FINAL,MODAL):
        folder=BASE/name;capture=json.loads(read(folder/'capture.json'));report=json.loads(read(folder/'report.json'));end=capture['frames']
        assert report['failure'] is None and report['full_dungeon_cleared'] and report['last_state']['room']==0xb9 and report['last_state']['first_gem']==128 and report['last_state']['max_health']==32
        lineage=[];cursor=name
        while (BASE/cursor/'report.json').exists():
            assert cursor not in lineage;lineage.append(cursor);r=json.loads(read(BASE/cursor/'report.json'));c=json.loads(read(BASE/cursor/'capture.json'))
            assert r['failure'] is None and c['rom_sha256']==capture['rom_sha256'] and not c['test_ram_writes'] and c['sram_input'] is None
            cursor=r['recorded_new_game_prefix']
        route=ROOT/'validation/natural-dungeon-route'/cursor;c=json.loads(read(route/'capture.json'));r=json.loads(read(route/'route_report.json'))
        assert r['reached_entrance'] and not r['failure'] and not c['test_ram_writes'] and c['sram_input'] is None and c['rom_sha256']==capture['rom_sha256']
        if '--verify-existing' not in sys.argv:subprocess.run([sys.executable,__file__,'--replay',name],cwd=ROOT,check=True)
        replay_folder=BASE/(name+'-story-replay-fresh');rc=json.loads(read(replay_folder/'capture.json'));assert not rc['test_ram_writes'] and rc['sram_input'] is None and rc['rom_sha256']==capture['rom_sha256']
        for stem,ext in [('ram','bin'),('frame','png')]:
            a=read(folder/f'{stem}_{end:05d}.{ext}');b=read(replay_folder/f'{stem}_{end:05d}.{ext}');assert a==b,(name,stem)
        raw=read(folder/f'ram_{end:05d}.bin')
        if name.startswith('sms'):flags=raw[0x100:0x200];tilemap=raw[0x1600:0x1b00];progress=raw[0xcf];music=raw[0x65]
        else:
            data=lambda k,n:bytes(raw[(sy[k]+i)^1] for i in range(n))
            flags=data('game_save_state',0x250)[0x50:0x150];tilemap=data('sms_vram',0x4000)[0x3800:0x3d00];progress=data('game_save_state',0x250)[0x1f];music=int.from_bytes(data('sound_current_track',2),'big')
        assert progress==128 and music==0x82 and flags[0x75]&4
        rooms=set();deaths=0;events=[]
        for part in reversed(lineage):
            r=json.loads(read(BASE/part/'report.json'));rooms.update(n for n in r['itinerary'] if n>=256);deaths+=r['deaths'];events.extend(e for e in json.loads(read(BASE/part/'events.json')) if 'actors' in e)
            for file in ['report.json','capture.json','controls.json','events.json']:evidence[(BASE/part/file).relative_to(ROOT).as_posix()]=sha(read(BASE/part/file))
        assert len(rooms)==13 and any(any(a['type']==0x68 for a in e['actors']) for e in events) and any(any(a['type']==7 for a in e['actors']) for e in events)
        keys=[];previous=0
        for e in events:
            if e['keys']!=previous:keys.append((e['room'],previous,e['keys']));previous=e['keys']
        assert keys==[(0x1e5,0,1),(0x1b5,1,0),(0x193,0,1),(0x185,1,0)],keys
        mr=json.loads(read(BASE/modal/'report.json'));me=[e for e in json.loads(read(BASE/modal/'events.json')) if 'actors' in e];pick=next(e['frame'] for e in me if e.get('progress')==128);frame=pick+150
        heal=[(e['frame'],e['health']) for e in me if e.get('max_health')==32 and e.get('progress')==128]
        heal=[v for n,v in enumerate(heal) if n==0 or v[1]!=heal[n-1][1]]
        assert heal[-1][1]==32 and all(b[0]-a[0]==2 and b[1]-a[1]==1 for a,b in zip(heal,heal[1:]))
        assert mr['last_state']['health']==32 and mr['last_state']['max_health']==32
        modal_ram=read(BASE/modal/f'ram_{frame:05d}.bin')
        modal_music=modal_ram[0x65] if name.startswith('sms') else int.from_bytes(bytes(modal_ram[(sy['sound_current_track']+i)^1] for i in range(2)),'big')
        assert modal_music==0x8c
        modal_records.append((read(BASE/modal/f'vram_{frame:05d}.bin'),read(BASE/modal/f'frame_{frame:05d}.png')))
        records.append((flags,tilemap));cases.append(dict(system='sms' if name.startswith('sms') else 'md',case=name,rom_sha256=capture['rom_sha256'],frames=end,lineage=lineage,dungeon_rooms=sorted(rooms),boss_type=0x68,keys=keys,normal_continue_count=deaths,final_health=report['last_state']['health'],max_health=32,gem_progress=128,final_music=music,fixed_replay_ram_bytes=len(raw),fixed_replay_png_exact=True,modal_case=modal,modal_frame=frame,health_refill_interval_frames=2))
    assert records[0]==records[1]
    a,b=modal_records[0][0],modal_records[1][0];tiles=set()
    for y in range(19,24):
        for x in range(1,31):
            w=int.from_bytes(a[0x3800+y*64+x*2:0x3802+y*64+x*2],'little');tiles.add(w&511);expected=((w>>11)&1)<<13|((w>>12)&1)<<15|((w>>10)&1)<<12|((w>>9)&1)<<11|16+(w&511);off=0xe000+(y+2)*128+x*2
            assert int.from_bytes(b[off:off+2],'little')==expected
    for tile in tiles|set(range(496,502)):assert sms_pixels(a,tile)==md_pixels(b,tile+16)
    s=Image.open(io.BytesIO(modal_records[0][1])).convert('RGB').crop((8,152,248,192));m=Image.open(io.BytesIO(modal_records[1][1])).convert('RGB').crop((8,168,248,208));colors=set(m.getdata());mapping={p:min(colors,key=lambda q:sum((x-y)**2 for x,y in zip(p,q))) for p in set(s.getdata())};assert all(mapping[p]==q for p,q in zip(s.getdata(),m.getdata()))
    result=dict(md_sha256=cases[1]['rom_sha256'],source_sha256=cases[0]['rom_sha256'],passed=True,region='auto',first_dungeon_boss_crystal_exit_verified=True,all_dungeon_rooms_explored=False,full_game_validated=False,cases=cases,source_native_final_flags_exact_bytes=256,source_native_final_map_exact_bytes=1280,reward_window_words_exact=150,reward_window_normalized_rgb_pixels_exact=9600,reward_window_and_hero_tiles_exact=len(tiles|set(range(496,502))),evidence=evidence,limits=['Critical story path through13 dungeon rooms: boss68, crystal, HP capacity24->32, refill and return toB9. Optional rooms/items, all other dungeons and full campaign remain unverified.','NTSC only; feedback controllers read game state and send normal buttons. Complete streams replay from cold boot without RAM reads or injections, with whole final RAM/PNG equality per machine.','Source/native encounters, buttons, HP and elapsed route times differ. Native route uses one ordinary death/Continue; no exact RNG, complete animation/cadence or waveform claim.','Reward display compares one settled window; palette normalization maps SMS RGB to nearest observed MD window color.'])
    (ROOT/'analysis/first_dungeon_story_v0226_report.json').write_text(json.dumps(result,indent=2)+'\n');print(cases)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--replay':replay(sys.argv[2])
    else:main()
