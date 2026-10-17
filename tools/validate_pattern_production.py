"""Natural transition regression; retain explicit existing PAL timing gaps."""
import contextlib
import hashlib
import io
import json
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    profile=json.loads((ROOT/'validation/menu_transition_profile.json').read_text())
    digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
    assert profile['md_sha256']==digest
    baseline=ROOT/'versions/v0194-2fceb892/gaw-megadrive-v0194.bin'
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_menu_libretro.dll'
    routes=dict(exterior=PRESSES[:8],first_house=PRESSES[:11]+[(2950,2958,7),(3000,3020,4)],
                second_house=PRESSES[:11]+[(2950,2965,5),(3000,3023,6),(3050,3061,4),(3100,3110,4)])
    frames=list(range(3348,3371))+list(range(3398,3441));cases=[]
    def black(folder,sms=False):
        dy=0 if sms else 16
        return [f for f in frames if not any(Image.open(folder/f'frame_{f:05}.png').convert('RGB').crop((0,dy,256,dy+160)).tobytes())]
    for case in profile['cases']:
        name=case['name'];region=case['region'];source=ROOT/f'validation/menu-transition-{name}-{region}-sms'
        target=ROOT/f'validation/menu-transition-{name}-{region}-md'
        src=black(source,True);actual=black(target)
        if region=='auto':
            assert actual==src,(name,region,src,actual)
            resume={tag:next(r['frame'] for r in case['results'][tag]['rows'] if r['frame']>3400 and r['state']==12) for tag in ['sms','md']}
            assert resume['sms']==resume['md'],resume
            comparison='SMS black windows and resume exact'
        else:
            folder=ROOT/f'validation/native-patterns/baseline-{name}-pal'
            with contextlib.redirect_stdout(io.StringIO()):
                run(baseline,3470,folder,set(frames),routes[name]+[(3350,3355,0),(3400,3405,0)],
                    core=core,core_options={'genesis_plus_gx_region_detect':region})
            assert actual==black(folder),(name,'PAL baseline changed')
            # Compare decoded pixels over the complete captured screen, not just black windows.
            for f in frames:
                assert Image.open(folder/f'frame_{f:05}.png').tobytes()==Image.open(target/f'frame_{f:05}.png').tobytes(),(name,f,'PAL pixels differ')
            comparison='PAL framebuffer unchanged from v0194 on all captured frames'
        assert all(r['effect_latch']==0 for r in case['results']['md']['rows'] if 3398<=r['frame']<=3440)
        cases.append(dict(name=name,region=region,comparison=comparison,
                          source_black_frames=src,md_black_frames=actual,source_exact=src==actual))
    report=dict(md_sha256=digest,baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),cases=cases,
                full_game_ported=False,limits=['Natural initial exterior and two shops only.',
                'PAL black-window ends still differ by one frame from SMS as in v0194; strict validate_menu_transitions remains unsatisfied.',
                'Global source clock and complete transition framebuffer equivalence with SMS remain pending.'])
    (ROOT/'validation/pattern_production_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Three NTSC source-exact black/resume checks; three PAL baseline framebuffer checks passed. PAL SMS timing gap remains.')

if __name__=='__main__':main()
