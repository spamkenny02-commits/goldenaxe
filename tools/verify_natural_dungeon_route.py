"""Replay recorded controller inputs and compare naturally reached dungeon1."""
import contextlib,gzip,io,json,subprocess,sys
from PIL import Image
from run_core import ROOT,run
from archive_lossless_evidence import sha
from validate_playable_sprite_limit import symbols

CASES=[('auto','sms-06','md-04'),('pal','sms-pal-01','md-pal-01')]

def read(path):
    if path.exists():return path.read_bytes()
    archive=ROOT/'analysis/natural-route-v0223';manifest=json.loads((archive/'manifest.json').read_bytes());name=path.relative_to(ROOT).as_posix()
    if name in manifest['files']:
        raw=(archive/name).read_bytes();assert sha(raw)==manifest['files'][name];return raw
    item=manifest['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256'];raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'];return raw

def replay_case(name):
    assert name in [n for _,a,b in CASES for n in [a,b]]
    base=ROOT/'validation/natural-dungeon-route';folder=base/name;capture=json.loads((folder/'capture.json').read_bytes());end=capture['frames']
    controls=json.loads((folder/'controls.json').read_bytes());presses=list(map(tuple,capture['presses']))
    for n,item in enumerate(controls):
        stop=controls[n+1]['frame']-1 if n+1<len(controls) else end
        presses.extend((item['frame'],stop,b) for b in item['buttons'])
    replay=base/(name+'-replay-fresh');assert not replay.exists(),replay
    rom=ROOT/'input/original.sms' if name.startswith('sms') else ROOT/'gaw-megadrive.bin'
    with contextlib.redirect_stdout(io.StringIO()):run(rom,end,replay,{end},presses,core_options=capture['core_options'])

def main():
    base=ROOT/'validation/natural-dungeon-route';cases=[];evidence={}
    for region,source_name,native_name in CASES:
        rows={}
        for tag,name in [('sms',source_name),('md',native_name)]:
            folder=base/name;r=json.loads((folder/'route_report.json').read_bytes());capture=json.loads((folder/'capture.json').read_bytes())
            assert r['reached_entrance'] and r['directional_probe_succeeded'] and r['rendered_final_frame_nonblack'] and not r['failure']
            assert not capture['test_ram_writes'] and capture['sram_input'] is None
            end=capture['frames']
            replay=base/(name+'-replay-fresh')
            rom=ROOT/'input/original.sms' if tag=='sms' else ROOT/'gaw-megadrive.bin';assert sha(rom.read_bytes())==r['rom_sha256']
            if '--verify-existing' not in sys.argv:
                assert not replay.exists(),('Preserve replay evidence; use a new output directory',replay)
                subprocess.run([sys.executable,__file__,'--replay-case',name],cwd=ROOT,check=True)
            expected=read(folder/f'ram_{end:05d}.bin');actual=read(replay/f'ram_{end:05d}.bin');assert expected==actual,(name,'fixed-controller replay differs')
            assert (folder/f'frame_{end:05d}.png').read_bytes()==(replay/f'frame_{end:05d}.png').read_bytes(),(name,'replay framebuffer differs')
            assert read(folder/f'vdp_regs_{end:05d}.bin')[1]&0x40
            if tag=='sms':
                assert actual[0x1e4]&16 and int.from_bytes(actual[0xc4:0xc6],'little')==0x1e4
            else:
                sy=symbols(ROOT/'megadrive/out/release/symbol.txt');start=sy['game_save_state'];assert actual[(start+0x134)^1]&16 and bytes(actual[(start+0x14+n)^1] for n in range(2))==b'\xe4\x01'
            rooms=[]
            for event in json.loads((folder/'events.json').read_bytes()):
                if 'room' in event and (not rooms or rooms[-1]!=event['room']):rooms.append(event['room'])
            assert rooms==[0x95,0x94,0xa4,0xb4,0xb5,0xb6,0xb7,0xb8,0xb9,0x1e4],rooms
            rows[tag]=dict(trace=name,reached_frame=r['first_controllable_frame'],door_transition_frames=r['door_transition_frames'],arrival_health=r['last_state']['health'],rooms=rooms,full_final_RAM_replay_bytes_exact=len(actual),fixed_input_replay_PNG_exact=True,dungeon_checkpoint_and_visited_flag=True,final_frame=end)
            for filename in ['route_report.json','capture.json','controls.json','events.json',f'ram_{end:05d}.bin',f'frame_{end:05d}.png']:
                path=folder/filename;evidence[path.relative_to(ROOT).as_posix()]=sha(read(path))
        source=base/source_name;native=base/native_name
        pixel_samples=[]
        for offset in [60,100]:
            sf=json.loads((source/'route_report.json').read_bytes())['first_controllable_frame']+offset;mf=json.loads((native/'route_report.json').read_bytes())['first_controllable_frame']+offset
            source_png=source/f'frame_{sf:05d}.png';native_png=native/f'frame_{mf:05d}.png'
            a=Image.open(io.BytesIO(read(source_png))).convert('RGB').crop((0,0,256,160));b=Image.open(io.BytesIO(read(native_png))).convert('RGB').crop((0,16,256,176))
            palette=set(a.getdata());mapping={color:min(palette,key=lambda p:sum((x-y)**2 for x,y in zip(color,p))) for color in set(b.getdata())}
            mismatch=sum(x!=mapping[y] for x,y in zip(a.getdata(),b.getdata()));assert not mismatch,(region,'settled entrance playfield',offset)
            pixel_samples.append(dict(offset_from_ready=offset,sms_frame=sf,md_frame=mf,normalized_mismatches=mismatch))
            for path in [source_png,native_png]:evidence[path.relative_to(ROOT).as_posix()]=sha(read(path))
        assert rows['sms']['door_transition_frames']==rows['md']['door_transition_frames']
        cases.append(dict(region=region,reference=rows['sms'],native=rows['md'],settled_playfield_normalized_pixels_compared=81920,settled_playfield_samples=pixel_samples,whole_route_timing_equal=False,arrival_health_equal=rows['sms']['arrival_health']==rows['md']['arrival_health']))
        print(region,'normal boot to dungeon1, fixed-input replay and normalized playfield passed',flush=True)
    result=dict(md_sha256=sha((ROOT/'gaw-megadrive.bin').read_bytes()),source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=True,cases=cases,evidence=evidence,ram_mutations=False,rom_mutations=False,checkpoint_injections=False,first_dungeon_cleared=False,full_game_validated=False,limits=['State-observing controller walks a ROM-derived route and recovers from actual knockback; each resulting input stream is replayed in a fresh emulator process without controller feedback, with full final RAM and PNG equality.','Nine exterior screens then entrance1E4; forward motion inside is tested. The first dungeon/boss/gem are not completed.','Source/native feedback controllers produce different inputs after differing encounters. Arrival HP and route durations differ, so no combat/RNG or full timing equivalence. Door duration measured from first destination-room publication to post-reveal idle initialization.','Only settled entrance playfield pixels use nearest-palette normalization; HUD health differs and intermediate transition pixels/audio are not compared.'])
    (ROOT/'analysis/natural_dungeon_route_v0223_report.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--replay-case':replay_case(sys.argv[2])
    else:main()
