"""Final inn messages keep the source stable marker and accept a direction."""
import contextlib,gzip,io,json,sys
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def baseline_symbols():
    folder=ROOT/'analysis/dialogue-glyph-v0222';m=json.loads((folder/'manifest.json').read_bytes());name='megadrive/out/release/symbol.txt'
    if name in m['files']:
        b=(folder/name).read_bytes();assert sha(b)==m['files'][name]
    else:
        i=m['compressed'][name];encoded=(folder/i['stored']).read_bytes();assert sha(encoded)==i['stored_sha256'];b=gzip.decompress(encoded);assert sha(b)==i['raw_sha256']
    p=ROOT/'validation/v0222-symbols.txt';p.write_bytes(b);return symbols(p)

def main():
    baseline='--baseline' in sys.argv;rom=ROOT/'versions/v0222-13edb546/gaw-megadrive-v0222.bin' if baseline else ROOT/'gaw-megadrive.bin'
    sy=baseline_symbols() if baseline else symbols(ROOT/'megadrive/out/release/symbol.txt');digest=sha(rom.read_bytes());version=next(e['version'] for e in json.loads((ROOT/'versions/index.json').read_bytes()) if e['sha256']==digest);cases=[]
    for region in ['auto','pal']:
        for button in [8,4]:
            data={};retained={}
            for tag,path in [('sms',ROOT/'input/original.sms'),('md',rom)]:
                rows={}
                def observe(f,r):
                    if f not in range(3960,4080) and f!=4400:return
                    if tag=='sms':rows[f]=dict(clock=r[0x2f],state=r[0x1d],room=int.from_bytes(r[0xb9:0xbb],'little'),health=r[0x318],gold=r[0xdd])
                    else:
                        word=lambda n:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(2)),'big')
                        long=lambda n:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(4)),'big')
                        rows[f]=dict(clock=(long('vtimer')-long('world_clock_shift'))&255,state=word('game_state'),room=word('room_id'),health=word('hero_health'),gold=word('hero_gold'),phase=word('healer_phase'))
                def video(f,v):
                    if f in rows:rows[f]['marker']=v[0x3cde] if tag=='sms' else ((int.from_bytes(v[0xe000+21*128+30:0xe000+21*128+32],'little')&2047)-16)&255
                inputs=PRESSES[:11]+[(2950,2958,7),(3000,3020,4),(3350,3500,4),(3650,3655,5),(3700,3710,8),(4300,4300,button)]
                writes=[(3300,0x310,(88<<8).to_bytes(2,'little')+(216<<8).to_bytes(2,'little')),(3300,0x30a,b'\0'),(3300,0x318,b'\x09'),(3300,0xda,bytes([24,11,24,87]))] if tag=='sms' else [(3300,sy[n],v.to_bytes(2,'big')) for n,v in [('hero_x',216<<8),('hero_y',88<<8),('hero_direction',0),('hero_health',9),('hero_max_health',24),('hero_magic',11),('hero_max_magic',24),('hero_gold',87)]]
                folder=ROOT/f'validation/service-waits-v{version:04d}/{region}-{button}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):run(path,4400,folder,set(),([(200,220,0)] if tag=='sms' else [])+inputs,ram_writes=writes,ram_observer=observe,vram_observer=video,core_options={'genesis_plus_gx_region_detect':region})
                p=folder/'observations.json';p.write_text(json.dumps(rows,indent=2)+'\n');retained[tag]=dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p.read_bytes()));data[tag]=rows
            marker_bad=[f for f in range(3960,4080) if data['sms'][f]['marker']!=data['md'][f]['marker']]
            assert {data['sms'][f]['marker'] for f in range(3960,4080)}=={252}
            assert all(data['md'][f]['phase']==3 for f in range(3960,4080))
            assert all(data['sms'][4400][n]==data['md'][4400][n] for n in ['state','room','health','gold']) and data['md'][4400]['state']==12 and not data['md'][4400]['phase']
            result=dict(region=region,acknowledgement='up' if button==4 else 'action',frames_compared=120,source_marker=252,native_marker_values=sorted({data['md'][f]['marker'] for f in range(3960,4080)}),marker_mismatch_frames=marker_bad,service_closed_and_resources_restored=True,passed=not marker_bad,evidence=retained);cases.append(result);print(region,button,'stable service marker',not marker_bad,flush=True)
    report=dict(md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=all(c['passed'] for c in cases),diagnostic_only=baseline,cases=cases,scope='First village free inn, refusal path after controlled position/resources.120 final-message marker frames per case; action and Up acknowledgement in PAL/NTSC, settled resource/state comparison. Does not prove every service, absolute pre-message timing or global IRQ clock.')
    (ROOT/f'analysis/service_wait_markers_v{version:04d}_report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not baseline:assert report['passed']

if __name__=='__main__':main()
