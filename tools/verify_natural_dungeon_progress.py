"""Verify nine natural dungeon fights, two keys and the194 switch; no injections."""
import contextlib,gzip,io,json,subprocess,sys
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols

CASES=['sms-auto-09','md-auto-11']
BASE=ROOT/'validation/natural-dungeon-combat'

def read(path):
    if path.exists():return path.read_bytes()
    archive=ROOT/'analysis/terrain-publication-v0225';m=json.loads((archive/'manifest.json').read_bytes());name=path.relative_to(ROOT).as_posix()
    if name in m['files']:
        raw=(archive/name).read_bytes();assert sha(raw)==m['files'][name];return raw
    i=m['compressed'][name];encoded=(archive/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==i['raw_sha256'];return raw

def replay(name):
    assert name in CASES
    folder=BASE/name;c=json.loads(read(folder/'capture.json'));end=c['frames'];controls=json.loads(read(folder/'controls.json'));presses=list(map(tuple,c['presses']))
    for n,row in enumerate(controls):
        stop=controls[n+1]['frame']-1 if n+1<len(controls) else end
        presses.extend((row['frame'],stop,b) for b in row['buttons'])
    out=BASE/(name+'-replay-fresh');assert not out.exists(),out
    rom=ROOT/'input/original.sms' if name.startswith('sms') else ROOT/'gaw-megadrive.bin';assert sha(rom.read_bytes())==c['rom_sha256']
    with contextlib.redirect_stdout(io.StringIO()):run(rom,end,out,{end},presses,core_options=c['core_options'])

def main():
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');rows=[];records=[];evidence={}
    for name in CASES:
        folder=BASE/name;c=json.loads(read(folder/'capture.json'));r=json.loads(read(folder/'report.json'));end=c['frames']
        assert r['room_cleared'] and r['failure'] is None and r['deaths']==0 and r['target_room']==0x193
        assert not c['test_ram_writes'] and c['sram_input'] is None
        if '--verify-existing' not in sys.argv:subprocess.run([sys.executable,__file__,'--replay',name],cwd=ROOT,check=True)
        out=BASE/(name+'-replay-fresh');rc=json.loads(read(out/'capture.json'));assert not rc['test_ram_writes'] and rc['sram_input'] is None and rc['frames']==end and rc['rom_sha256']==r['rom_sha256']
        for stem,suffix in [('ram','bin'),('frame','png')]:
            a=read(folder/f'{stem}_{end:05d}.{suffix}');b=read(out/f'{stem}_{end:05d}.{suffix}');assert a==b,(name,stem)
            evidence[(folder/f'{stem}_{end:05d}.{suffix}').relative_to(ROOT).as_posix()]=sha(a)
        raw=read(folder/f'ram_{end:05d}.bin')
        if name.startswith('sms'):flags=raw[0x100:0x200];tilemap=raw[0x1600:0x1b00];actors=raw[0x600:0x780]
        else:
            data=lambda k,n:bytes(raw[(sy[k]+i)^1] for i in range(n))
            flags=data('game_save_state',0x250)[0x50:0x150];tilemap=data('sms_vram',0x4000)[0x3800:0x3d00];actors=data('world_actor_state',384)
        assert not any(actors)
        assert flags[0x94]&0x64==0x64 and flags[0xb5]&0x20 and flags[0x93]&8 and flags[0xe5]&8
        events=[e for e in json.loads(read(folder/'events.json')) if 'actors' in e]
        key_events=[];previous=0
        for e in events:
            if e['keys']!=previous:key_events.append((e['room'],previous,e['keys']));previous=e['keys']
        assert key_events==[(0x1e5,0,1),(0x1b5,1,0),(0x193,0,1)],key_events
        assert len(set(r['itinerary']))==10
        records.append((flags,tilemap));rows.append(dict(system='sms' if name.startswith('sms') else 'md',case=name,rom_sha256=r['rom_sha256'],frames=end,visited_itinerary_rooms=r['itinerary'],key_events=key_events,final_health=r['last_state']['health'],final_keys=1,full_final_ram_bytes_replayed=len(raw),full_final_png_replayed=True,deaths=0))
        for filename in ['report.json','capture.json','events.json','controls.json']:evidence[(folder/filename).relative_to(ROOT).as_posix()]=sha(read(folder/filename))
    assert records[0]==records[1]
    result=dict(md_sha256=rows[1]['rom_sha256'],source_sha256=rows[0]['rom_sha256'],passed=True,region='auto',cases=rows,source_native_persistent_flags_exact_bytes=256,source_native_settled_map_exact_bytes=1280,evidence=evidence,ram_mutations=False,rom_mutations=False,sram_injections=False,first_dungeon_cleared=False,full_game_validated=False,limits=['Nine combat rooms, two generated keys, one consumed key and194 stationary UP switch; boss/gem and the rest of the dungeon not reached.','Feedback controllers read RAM and send normal buttons; each resulting stream also replays in a separate fresh process without feedback.','Source/native timings, inputs, HP and random decisions differ; flags/map equality is only asserted at the final settled room193. NTSC only.'])
    (ROOT/'analysis/natural_dungeon_progress_v0225_report.json').write_text(json.dumps(result,indent=2)+'\n');print(rows)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--replay':replay(sys.argv[2])
    else:main()
