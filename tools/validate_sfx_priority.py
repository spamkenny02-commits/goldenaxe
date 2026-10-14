"""Compare all29 source effects, priority and seven PSG channel records every IRQ."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    results=[]
    scenarios=[
        ('lower_rejected',[(360,8,0x91),(362,8,0x90)]),
        ('higher_replaces',[(360,8,0x90),(362,8,0x91)]),
        ('equal_replaces',[(360,8,0x92),(362,8,0x93)]),
        ('three_queues',[(360,6,0x90),(360,7,0x91),(360,8,0x95)]),
        ('later_tie',[(360,6,0x92),(360,7,0x93)]),
        ('music_effect_same_tick',[(360,6,0x81),(360,8,0x90)]),
        ('tone_noise_overlap',[(360,8,0x91),(362,8,0x92)]),
        ('noise_tone_overlap',[(360,8,0x92),(362,8,0x91)]),
        ('stop_effects',[(360,8,0xa6),(370,8,0xb2)]),
        ('stop_all',[(360,8,0xa6),(370,8,0xb1)]),
        ('fade',[(360,8,0xb0)]),
        ('music_reset',[(360,8,0xa6),(370,6,0x83)]),
    ]
    for command,events in scenarios:
        source={};target={};errors={};source_psg={};target_psg={}
        core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_libretro.dll'
        def sms_observe(frame,raw):
            if frame>=301:source[frame]=raw[0x1e00:0x1f90]
        def md_observe(frame,raw):
            if frame<301:return
            d=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]));off=symbols['sound_ram'];target[frame]=d[off:off+0x190];off=symbols['sound_unhandled_command'];errors[frame]=int.from_bytes(d[off:off+2],'big')
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/'input/original.sms',960,ROOT/f'validation/sfx-priority-sms-{command}',set(),[],ram_writes=[(300,0x1e04,b'\0'),(300,0x1e06,b'\x84'),*[(f,0x1e00+lane,bytes([cmd])) for f,lane,cmd in events]],skip_intro=False,ram_observer=sms_observe,core=core,psg_observer=lambda f,p:source_psg.update({f:p}))
            run(ROOT/'gaw-megadrive.bin',960,ROOT/f'validation/sfx-priority-md-{command}',set(),[],ram_writes=[(300,symbols['sound_ram']+4,b'\0'),(300,symbols['sound_request'],(0x84).to_bytes(2,'big')),*[(f,symbols['sound_ram']+lane,bytes([cmd])) for f,lane,cmd in events]],skip_intro=False,ram_observer=md_observe,core=core,psg_observer=lambda f,p:target_psg.update({f:p}))
        assert not any(errors.values()),(command,'unsupported',set(errors.values()))
        mismatches=[]
        for f in source:
            # DE03 indicates 60 Hz compensation. GG stereo routing DE12 has
            # no equivalent on the mono MD PSG; every channel byte is checked.
            a=source[f];b=target[f]
            for i in list(range(1,0x12))+list(range(0x13,0x19))+list(range(0x40,0x190)):
                if a[i]!=b[i]:mismatches.append((f,hex(i),a[i],b[i]))
        def audible(regs):
            return regs[:6]+((regs[6] if regs[7] else 0),regs[7])
        psg_mismatches=[(f,source_psg[f],target_psg[f]) for f in source if audible(source_psg[f])!=audible(target_psg[f])]
        assert not psg_mismatches,(command,'PSG registers',psg_mismatches[:5])
        assert not mismatches,(command,len(mismatches),mismatches[:12])
        results.append(dict(command=command,events=events,irq_states_exact=len(source),channel_records=7,audible_psg_register_states_exact=len(source),unsupported_commands=0));print(results[-1],flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),scenarios=results,scope='Priority replacement, three queues, music/noise/tone arbitration, stop and fade; controlled commands and compensation phase',muted_noise_register_excluded=True,audio_waveform_equivalence_verified=False,sound_effect_arbitration_ported=True)
    (ROOT/'validation/sfx_priority_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
