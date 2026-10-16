"""Real SMS/MD noise controls, borrowed rests and whole-reader exits with effects."""
import contextlib,ctypes as c,hashlib,io,json,re,struct
from actor_reference import ROOT
from validate_audio_note_commands_cost import COMMANDS
from run_core import run

def main():
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_livereaderrefresh_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_live_envelope_samples.restype=c.c_uint;dll.gaw_live_envelope_events.restype=c.POINTER(c.c_uint8)
    def initial(address,program,flags=128,pending=0,latch=0):
        r=bytearray(400);r[5]=128;r[0xd0]=flags;r[0xd1]=0xe0;r[0xd2]=1;r[0xd3:0xd5]=address.to_bytes(2,'little');r[0xda]=1;r[0xd9]=0x30;r[14]=pending;r[15]=latch
        offset=(address&0x1fff)-0x1e00;r[offset:offset+len(program)]=bytes(program)
        for offset,tone in [(0x100,0xa0),(0x130,0xc0),(0x160,0xe0)]:
            r[offset]=128;r[offset+1]=tone;r[offset+2]=1;r[offset+3:offset+5]=bytes([0x90,0xde]);r[offset+9]=0x30;r[offset+10]=2;r[offset+11:offset+13]=bytes([0x23,1])
        r[0x90:0x94]=bytes([1,1,1,1]);return r
    vectors=[]
    for opcode in [0xf1,0xf2]:
        for flags,pending in [(128,0),(132,0),(192,0),(128,0x90),(128,0x91),(128,0xac)]:
            vectors.append((f'exit-{opcode:02x}-{flags}-{pending:02x}',initial(0xde80,[opcode],flags,pending),True))
    for value,latch in [(0xe3,0),(0xe3,128),(0xe4,0),(0xe6,0)]:
        vectors.append((f'ownership-{value:02x}-{latch}',initial(0xde80,[0xf3,value,0x81,7],latch=latch),value==0xe3 and latch==0))
    for note in [0x80,0x81,0x82,0x84,0x88,0x90,0xa0,0xbf,0xc0,0xdf]:
        for flags in [128,132]:vectors.append((f'noise-{note:02x}-{flags}',initial(0xde80,[note,7],flags),False))
    for command in COMMANDS:
        operands=[7,7,2,255,128];size=5 if command in [0xe0,0xe9] else 4 if command==0xf0 else 2 if command in [0xea,0xf6] else 1
        if command==0xf6:operands=[0x88,0xde]
        r=initial(0xde80,[command]+operands[:size]+[0x91,7]);r[0x88:0x8c]=bytes([0x91,7,0x81,7])
        vectors.append((f'command-{command:02x}',r,False))
    for address in [0xde80,0xfe80,0xdf80,0xff80]:
        vectors.append((f'mirror-{address:04x}',initial(address,[0xea,128,3,0x81,7]),False))
    mute=bytearray(400);mute[5]=0xb1
    seed=bytearray(400);seed[5]=128;seed[0xd0]=128;seed[0xd1]=0xe0;seed[0xd2]=1;seed[0xd3:0xd5]=bytes([0x80,0xde]);seed[0xda]=1;seed[0x80:0x82]=bytes([0x81,7])
    cases=[]
    for region in ['auto','pal']:
        for name,initial_ram,exits in vectors:
            records={};psg={}
            for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                dll.gaw_timing_reset();result={};sound={};base=0x1e00 if tag=='sms' else symbols['sound_ram']
                writes=[(297,base,bytes(mute)),(298,base,bytes(seed)),(300,base,bytes(initial_ram))]
                if tag=='md':
                    for frame in [297,298,300]:writes.extend([(frame,symbols['sound_request'],bytes(2)),(frame,symbols['sound_effect_request'],bytes(2))])
                def observe(frame,ram):
                    if frame<300:return
                    if tag=='sms':
                        count=dll.gaw_live_envelope_samples();raw=c.string_at(c.addressof(dll.gaw_live_envelope_events().contents)+(count-1)*824,824)
                        result[frame]=(struct.unpack_from('<I',raw,8)[0],raw[424:824])
                    else:
                        def data(a,n):return bytes(ram[(a+i)^1] for i in range(n))
                        result[frame]=(int.from_bytes(data(symbols['sound_source_de'],2),'big'),data(symbols['sound_ram'],400))
                        assert int.from_bytes(data(symbols['sound_unhandled_command'],2),'big')==0,(region,name,frame,'unsupported')
                folder=ROOT/f'validation/production-audio-noise/{name}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):run(rom,302,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,
                    core=core,psg_observer=lambda f,p:sound.update({f:p}),core_options={'genesis_plus_gx_region_detect':region})
                (folder/'de-reader-records.bin').write_bytes(b''.join(struct.pack('<I',de)+state for de,state in result.values()))
                (folder/'psg.json').write_text(json.dumps({f:sound[f] for f in result},indent=2)+'\n');records[tag]=result;psg[tag]=sound
            assert records['sms']==records['md'],(region,name,'DE/state')
            def audible(p):return p[:6]+((p[6] if p[7] else 0),p[7])
            assert all(audible(psg['sms'][f])==audible(psg['md'][f]) for f in [300,301,302]),(region,name,'PSG')
            assert records['md'][300][1][0x10a]==(2 if exits else 1),(region,name,'effect tick')
            cases.append(dict(region=region,name=name,reader_states_exact=3,compared_RAM_bytes=400,audible_PSG_states_exact=3,whole_reader_exit=exits))
            print(region,name,'three IRQ states/DE/audiblePSG exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,
                limits=['Controlled noise/music/effect states and audible PSG seed; real source/native readers on three IRQs.',
                        'F1/F2/F3 reader exits, simultaneous effects, borrowed rests, six selector bits, shared controls andRAM mirrors.',
                        'Muted noise register excluded; E2 GG routing startsneutral. No waveform/hardware/full-progression proof.'])
    (ROOT/'validation/production_audio_noise_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
