"""Source vs playable MD84C7 composition and audible PSG across tonal slots."""
import contextlib
import ctypes as c
import hashlib
import io
import itertools
import json
import re
import struct
from actor_reference import ROOT
from run_core import run


def main():
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_livereaderrefresh_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_live_envelope_samples.restype=c.c_uint
    dll.gaw_live_envelope_events.restype=c.POINTER(c.c_uint8)
    def initial(slot,count,flags,mode=0,env=0,release=0,transpose=0):
        r=bytearray(400);r[5]=128;r[slot]=flags
        r[slot+1]={0x40:0x80,0x70:0xa0,0xa0:0xc0,0x100:0x80,0x130:0xa0,0x160:0xc0}[slot]
        r[slot+2]=1;r[slot+3:slot+5]=bytes([0x80,0xde]);r[slot+6]=mode;r[slot+7]=env
        r[slot+9]=0x30;r[slot+10]=count;r[slot+11:slot+13]=bytes([0x23,1])
        r[slot+14]=release;r[slot+16:slot+18]=bytes([0x0b,0x8a])
        r[slot+20:slot+24]=bytes([1,1,1,1]);r[slot+37]=transpose
        r[0x80:0x84]=bytes([0x91,7,0x81,7]);return r
    vectors=[]
    for slot in [0x40,0x70,0xa0,0x100,0x130,0x160]:
        for flags,transpose in itertools.product([128,130,160,192],[0,128]):
            vectors.append((f'note-{slot:03x}-{flags}-{transpose}',initial(slot,1,flags,transpose=transpose)))
        for mode,env in itertools.product([0,1,128],[0,1,128]):
            vectors.append((f'held-{slot:03x}-{mode}-{env}',initial(slot,4,128,mode,env)))
        for env,flags in itertools.product([0,128],[128,130]):
            vectors.append((f'release-{slot:03x}-{env}-{flags}',initial(slot,4,flags,env=env,release=1)))
    mute=bytearray(400);mute[5]=0xb1;cases=[]
    for region in ['auto','pal']:
        for name,initial_ram in vectors:
            records={};psg={}
            for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                dll.gaw_timing_reset();result={};sound={}
                base=0x1e00 if tag=='sms' else symbols['sound_ram']
                writes=[(297,base,bytes(mute)),(300,base,bytes(initial_ram))]
                if tag=='md':
                    for frame in [297,300]:
                        writes.extend([(frame,symbols['sound_request'],bytes(2)),(frame,symbols['sound_effect_request'],bytes(2))])
                def observe(frame,ram):
                    if frame<300:return
                    if tag=='sms':
                        count=dll.gaw_live_envelope_samples()
                        raw=c.string_at(c.addressof(dll.gaw_live_envelope_events().contents)+(count-1)*824,824)
                        result[frame]=(struct.unpack_from('<I',raw,8)[0],raw[424:824])
                    else:
                        def data(a,n):return bytes(ram[(a+i)^1] for i in range(n))
                        result[frame]=(int.from_bytes(data(symbols['sound_source_de'],2),'big'),data(symbols['sound_ram'],400))
                        assert int.from_bytes(data(symbols['sound_unhandled_command'],2),'big')==0,(region,name,frame,'unsupported')
                folder=ROOT/f'validation/production-audio-tone/{name}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(rom,302,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,
                        core=core,psg_observer=lambda f,p:sound.update({f:p}),core_options={'genesis_plus_gx_region_detect':region})
                (folder/'de-reader-records.bin').write_bytes(b''.join(struct.pack('<I',de)+state for de,state in result.values()))
                (folder/'psg.json').write_text(json.dumps({f:sound[f] for f in result},indent=2)+'\n')
                records[tag]=result;psg[tag]=sound
            assert records['sms']==records['md'],(region,name,'DE/state')
            def audible(p):return p[:6]+((p[6] if p[7] else 0),p[7])
            assert all(audible(psg['sms'][f])==audible(psg['md'][f]) for f in [300,301,302]),(region,name,'PSG')
            cases.append(dict(region=region,name=name,reader_states_exact=3,compared_RAM_bytes=400,audible_PSG_states_exact=3))
            print(region,name,'three IRQ states/DE/audiblePSG exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,
                limits=['Controlled notes/held/release contexts in six tonal slots, real SMS/MD readers over three IRQs.',
                        'All400 bytes, DE and audible PSG registers compared; muted noise config excluded.',
                        'Does not prove waveform equivalence, full IRQ clock, physical hardware or full natural progression.'])
    (ROOT/'validation/production_audio_tone_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
