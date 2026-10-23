"""Bind v0242 bell cases and compare eight normalized display frames per region."""
import json
from PIL import Image
from run_core import ROOT
from archive_lossless_evidence import sha

def main():
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());cases=[];pixels=[]
    for path in sorted((ROOT/'analysis').glob('ice_bell_v0242*_report.json')):
        r=json.loads(path.read_bytes());assert r['passed'] and r['md_sha256']==digest
        cases.append(path.name)
    assert len(cases)==8
    for tag in ['v0242','v0242-pal']:
        r=json.loads((ROOT/f'analysis/ice_bell_{tag}_report.json').read_bytes())
        assert r['stage_first_frames']['sms']==r['stage_first_frames']['md']
        for f in [2999,3003,3007,3011,3015,3025,3100,3300]:
            left=Image.open(ROOT/f'validation/ice-bell-{tag}-sms/frame_{f:05d}.png').convert('RGB')
            right=Image.open(ROOT/f'validation/ice-bell-{tag}-md/frame_{f:05d}.png').convert('RGB').crop((0,16,256,208))
            palette=set(left.getdata());conv={v:min(palette,key=lambda c:sum((x-y)**2 for x,y in zip(v,c))) for v in set(right.getdata())}
            differences=sum(x!=conv[y] for x,y in zip(left.getdata(),right.getdata()));assert differences==0,(tag,f,differences)
            pixels.append(dict(case=tag,frame=f,normalized_pixel_differences=differences))
    result=dict(md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=True,cases=cases,controlled_cases=8,normalized_pixel_frames=pixels,full_game_verified=False,limits=['Initial room, ownership, resources and one clock phase are controlled; natural acquisition and full campaign remain unverified.','Eight complete water masks and their sampled frames match in the tested PAL/NTSC scene; individual raster writes and audio waveforms are not established.','Actor conversion, inventory return, overview interaction, one special passage and indoor guards are targeted fixtures.'])
    (ROOT/'analysis/ice_bell_release_v0242_report.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print('v0242: eight controlled cases, sixteen normalized display frames, matching eight-step PAL/NTSC freeze.')

if __name__=='__main__':main()
