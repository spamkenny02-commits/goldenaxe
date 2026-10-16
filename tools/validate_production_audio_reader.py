"""Compare source8000 cycles/M1, state and audible PSG to the playable ROM."""
import contextlib
import ctypes as c
import hashlib
import io
import json
import re
import struct
from actor_reference import ROOT
from source_rng_refresh import advance_refresh
from run_core import run


def main():
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_livereaderrefresh_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_live_envelope_samples.restype=c.c_uint
    dll.gaw_live_envelope_events.restype=dll.gaw_live_envelope_m1_events.restype=c.POINTER(c.c_uint8)
    vectors=[(f'track-{command:02x}',command,None,None,700) for command in range(0x81,0x8e)]
    vectors.extend((f'effect-{command:02x}',0x84,command,None,700) for command in range(0x90,0xad))
    vectors.extend((f'gate-{gate}',None,None,(10,gate),303) for gate in [1,127,128,129,255])
    vectors.extend((f'phase-{phase}',None,None,(4,phase),303) for phase in [0,1,4,5,6,7,254,255])
    cases=[]
    for region in ['auto','pal']:
        for name,track,effect,context,end in vectors:
            records={};psg={};source_raw=[];source_m1=[]
            for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                dll.gaw_timing_reset();result={};sound={};previous=[0]
                initial=bytearray(400);initial[3]=128 if region=='auto' or name.startswith('phase') else 0
                initial[5]=128
                if track:initial[6]=track
                if context:initial[context[0]]=context[1]
                base=0x1e00 if tag=='sms' else symbols['sound_ram'];writes=[(300,base,bytes(initial))]
                if effect:writes.append((360,base+8,bytes([effect])))
                if tag=='md':writes.extend([(300,symbols['sound_request'],bytes(2)),(300,symbols['sound_effect_request'],bytes(2))])
                def observe(frame,ram):
                    if frame<300:return
                    if tag=='sms':
                        count=dll.gaw_live_envelope_samples();assert not previous[0] or count==previous[0]+1
                        previous[0]=count
                        raw=c.string_at(c.addressof(dll.gaw_live_envelope_events().contents)+(count-1)*824,824)
                        m1=c.string_at(c.addressof(dll.gaw_live_envelope_m1_events().contents)+(count-1)*12,12)
                        fetches,entry,exit=struct.unpack('<3I',m1);assert exit==advance_refresh(entry,fetches)
                        state=raw[424:824];cost=struct.unpack_from('<I',raw,16)[0]
                        result[frame]=(cost,fetches,state);source_raw.append(raw);source_m1.append(m1)
                    else:
                        def data(a,n):return bytes(ram[(a+i)^1] for i in range(n))
                        cost,fetches=struct.unpack('>2I',data(symbols['sound_source_work'],8))
                        result[frame]=(cost,fetches,data(symbols['sound_ram'],400))
                        assert int.from_bytes(data(symbols['sound_unhandled_command'],2),'big')==0,(name,region,frame,'unsupported')
                folder=ROOT/f'validation/production-audio-reader/{name}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(rom,end,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,
                        core=core,psg_observer=lambda f,p:sound.update({f:p}),core_options={'genesis_plus_gx_region_detect':region})
                (folder/'reader-work-records.bin').write_bytes(b''.join(struct.pack('<2I',cost,fetches)+state for cost,fetches,state in result.values()))
                (folder/'psg.json').write_text(json.dumps({f:sound[f] for f in result},separators=(',',':'))+'\n')
                if tag=='sms':
                    (folder/'source-reader-records.bin').write_bytes(b''.join(source_raw))
                    (folder/'source-reader-m1-records.bin').write_bytes(b''.join(source_m1))
                records[tag]=result;psg[tag]=sound
            assert records['sms']==records['md'],(name,region,'reader state/T/M1',
                [(f,a[:2],records['md'][f][:2]) for f,a in records['sms'].items() if a!=records['md'][f]][:5])
            def audible(p):return p[:6]+((p[6] if p[7] else 0),p[7])
            # Gate/phase fixtures retain unknown physical PSG registers from
            # boot. Their state/work are compared; score/effect fixtures mute
            # through the source track loader before audible comparisons.
            if track:assert all(audible(psg['sms'][f])==audible(psg['md'][f]) for f in records['sms']),(name,region,'PSG')
            cases.append(dict(region=region,name=name,reader_states_exact=len(records['sms']),
                              compared_RAM_bytes=400,T_M1_exact=True,audible_PSG_checked=bool(track)))
            print(region,name,len(records['sms']),'reader400/T/M1 exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,
                limits=['Actual SMS8000 read-only cycle/M1 observer vs production native per-IRQ aggregate; sourceR delta checked.',
                        '13tracks/29effects eachregion, gate/compensation boundaries; full400/T/M1. Audible PSG checked for track/effect contexts.',
                        'DE on early gates is foreground-dependent on SMS, so excluded here; component/other production tests cover DE.',
                        'Work is retained but not yet wired to full virtual IRQ/foreground clock. No waveform/hardware/full natural progression proof.'])
    (ROOT/'validation/production_audio_reader_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
