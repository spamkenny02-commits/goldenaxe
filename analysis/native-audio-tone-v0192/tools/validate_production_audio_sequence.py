"""Natural source driver vs production8357 for EA, extended loops/calls and mirrors."""
import contextlib,ctypes as c,hashlib,io,json,re,struct
from actor_reference import ROOT
from run_core import run

def main():
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_livereaderrefresh_libretro.dll';dll=c.CDLL(str(core))
    dll.gaw_live_envelope_samples.restype=c.c_uint;dll.gaw_live_envelope_events.restype=c.POINTER(c.c_uint8)
    vectors=[];cases=[]
    def initial(address,program):
        r=bytearray(400);r[5]=128;r[0x40]=128;r[0x41]=0x80;r[0x42]=1;r[0x43:0x45]=address.to_bytes(2,'little');r[0x49]=0x30;r[0x4a]=1
        offset=(address&0x1fff)-0x1e00;r[offset:offset+len(program)]=bytes(program);return r
    for address in [0xde80,0xfe80,0xdf80,0xff80]:
        for value in [0,127,128,255]:vectors.append((f'ea-{address:04x}-{value}',initial(address,[0xea,value,3,0x81,7]),'tone'))
    for index in [9,255]:vectors.append((f'extended-loop-{index}',initial(0xde80,[0xf7,index,1,0,0,0x81,7]),'tone'))
    # Five nested calls take the source stack below2A, which the old native
    # parser incorrectly refused. A following return chain restores30.
    program=[]
    for n in range(5):
        target=0xde84+n*4;program.extend([0xf8,target&255,target>>8,2 if n==0 else 0xf9])
    program.extend([0x81,1,0xf9]);vectors.append(('nested-calls-and-returns',initial(0xde80,program),'tone'))
    for opcode in [0xf1,0xf2]:
        for command in [0x90,0x91,0xac]:
            r=initial(0xde80,[opcode]);r[14]=command;vectors.append((f'terminate-{opcode:02x}-restore-{command:02x}',r,'mute'))
    for region in ['auto','pal']:
        for name,initial_ram,psg_kind in vectors:
            observed={};psg={}
            for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                dll.gaw_timing_reset();result={};sound={};base=0x1e00 if tag=='sms' else symbols['sound_ram'];writes=[(300,base,bytes(initial_ram))]
                if tag=='md':writes.extend([(300,symbols['sound_request'],bytes(2)),(300,symbols['sound_effect_request'],bytes(2))])
                def observe(frame,ram):
                    if frame<300:return
                    if tag=='sms':
                        count=dll.gaw_live_envelope_samples();raw=c.string_at(c.addressof(dll.gaw_live_envelope_events().contents)+(count-1)*824,824)
                        result[frame]=(struct.unpack_from('<I',raw,8)[0],raw[424:824])
                    else:
                        def data(address,length):return bytes(ram[(address+i)^1] for i in range(length))
                        result[frame]=(int.from_bytes(data(symbols['sound_source_de'],2),'big'),data(symbols['sound_ram'],400))
                        assert int.from_bytes(data(symbols['sound_unhandled_command'],2),'big')==0,(region,name,frame,'unsupported')
                folder=ROOT/f'validation/production-audio-sequence/{name}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):run(rom,301,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,
                    core=core,psg_observer=lambda f,p:sound.update({f:p}),core_options={'genesis_plus_gx_region_detect':region})
                (folder/'de-reader-records.bin').write_bytes(b''.join(struct.pack('<I',de)+state for de,state in result.values()))
                observed[tag]=result;psg[tag]=sound
            assert observed['sms']==observed['md'],(region,name,'DE/state')
            for frame in [300,301]:
                indices=[0,1] if psg_kind=='tone' else [1]
                assert all(psg['sms'][frame][i]==psg['md'][frame][i] for i in indices),(region,name,frame,'PSG')
            if name=='nested-calls-and-returns':
                assert observed['md'][300][1][0x49]==0x26 and observed['md'][301][1][0x49]==0x30
            cases.append(dict(region=region,name=name,reader_states_exact=2,compared_RAM_bytes=400,PSG_voice0_period_checked=psg_kind=='tone',PSG_voice0_volume_checked=True))
            print(region,name,'two IRQ states/DE andPSG voice0 exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,
                limits=['Controlled audio RAM/programs; unmodified source driver vs native ROM. 400 bytes andDE aftertwo IRQs.',
                        'EA enable/disable, RAM mirrors, F7 extended/wrapped index, five calls/returns andF1/F2 restoration.',
                        'PSG voice0 only (volume only for termination); other channels covered in separate music/effect regressions. No full game/clock/waveform proof.'])
    (ROOT/'validation/production_audio_sequence_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
