"""Observe original/native contact caches during normal controller movement."""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    pal='--pal' in sys.argv;suffix='-pal' if pal else '';records={}
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    inputs=PRESSES[:8]+[(2600,2620,7),(2650,2690,4),(2720,2760,6),(2790,2830,5),(2855,2940,4),(2950,2970,5)]
    for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
        samples={}
        def observe(f,d):
            if f<2600:return
            def word(o):return int.from_bytes(d[o:o+2],'little')
            if tag=='sms':samples[f]=dict(state=d[0x1d],room=word(0xb9),coordinate=word(0x62),direction=d[0x64],flags=d[0xa6])
            else:samples[f]=dict(state=word(sy['game_state']),room=word(sy['room_id']),coordinate=word(sy['room_script_coordinate']),direction=word(sy['room_script_direction']))
        with contextlib.redirect_stdout(io.StringIO()):run(rom,2970,ROOT/f'validation/contact-cache-{tag}{suffix}',set(),([(200,220,0)] if tag=='sms' else [])+inputs,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
        records[tag]=samples
    differences=[];checked=0;flag_values=set()
    for f,sms in records['sms'].items():
        md=records['md'][f]
        if sms['state']!=12 or md['state']!=12:continue
        checked+=1;flag_values.add(sms['flags'])
        if any(sms[k]!=md[k] for k in ['room','coordinate','direction']):differences.append(dict(frame=f,sms=sms,md=md))
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),region='pal' if pal else 'auto',frames_checked=checked,differing_cached_state_frames=len(differences),examples=differences[:12],source_flag_values=sorted(flag_values),controller_only_no_ram_injections=True,full_game_ported=False,limits=['Bounded exterior movement sequence; full contact effects and dungeon routes remain unverified.'])
    (ROOT/f'validation/contact_cache_gameplay{suffix}_report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert checked>200 and not differences,(checked,differences[:3]);print(checked,'live contact-cache frames match')
if __name__=='__main__':main()
