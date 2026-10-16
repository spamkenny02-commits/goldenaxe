"""Compare all29 source effects, priority and seven PSG channel records every IRQ."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    results=[]
    for command in range(0x90,0xad):
        source={};target={};errors={};source_psg={};target_psg={}
        core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_libretro.dll'
        def sms_observe(frame,raw):
            if frame>=301:source[frame]=raw[0x1e00:0x1f90]
        def md_observe(frame,raw):
            if frame<301:return
            d=bytes(v for n in range(0,len(raw),2) for v in (raw[n+1],raw[n]));off=symbols['sound_ram'];target[frame]=d[off:off+0x190];off=symbols['sound_unhandled_command'];errors[frame]=int.from_bytes(d[off:off+2],'big')
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/'input/original.sms',960,ROOT/f'validation/sfx-sms-{command:02x}',set(),[],ram_writes=[(300,0x1e04,b'\0'),(300,0x1e06,b'\x84'),(360,0x1e08,bytes([command]))],skip_intro=False,ram_observer=sms_observe,core=core,psg_observer=lambda f,p:source_psg.update({f:p}))
            run(ROOT/'gaw-megadrive.bin',960,ROOT/f'validation/sfx-md-{command:02x}',set(),[],ram_writes=[(300,symbols['sound_ram']+4,b'\0'),(300,symbols['sound_request'],(0x84).to_bytes(2,'big')),(360,symbols['sound_effect_request'],command.to_bytes(2,'big'))],skip_intro=False,ram_observer=md_observe,core=core,psg_observer=lambda f,p:target_psg.update({f:p}))
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
        assert not psg_mismatches,(hex(command),'PSG registers',psg_mismatches[:5])
        assert not mismatches,(hex(command),len(mismatches),mismatches[:12])
        results.append(dict(command=hex(command),irq_states_exact=len(source),channel_records=7,audible_psg_register_states_exact=len(source),unsupported_commands=0));print(results[-1],flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),effects=results,scope='All29 original effects over track84; seven channels, direct command injection and compensation phase aligned; event hooks tested separately',muted_noise_register_excluded=True,audio_waveform_equivalence_verified=False,sound_effect_arbitration_ported=True)
    (ROOT/'validation/sfx_report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
