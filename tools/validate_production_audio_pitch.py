"""Real source/native IRQ comparison for modulation and mirrored pitch83 reads."""
import contextlib,ctypes as c,hashlib,io,json,re,struct
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from run_core import run

def main():
    source=(ROOT/'input/original.sms').read_bytes();bank=source[0x18000:0x1c000]
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535
        for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_livereaderrefresh_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_live_envelope_samples.restype=c.c_uint;dll.gaw_live_envelope_events.restype=c.POINTER(c.c_uint8)
    vectors=[];cases=[]
    for offset,tone in [(0x40,0x80),(0x70,0xa0),(0xa0,0xc0),(0x100,0xa0),(0x130,0xc0),(0x160,0xe0)]:
        for pointer in [0x8ac0,0xdf70,0xff70]:
            for rate,phase,step in [(1,1,128),(2,2,255),(0,0,127)]:
                r=bytearray(400);r[5]=128;r[offset]=128;r[offset+1]=tone;r[offset+6]=128;r[offset+10]=2
                r[offset+11:offset+13]=bytes([0x23,1]);r[offset+0x10:offset+0x12]=pointer.to_bytes(2,'little')
                r[offset+0x12:offset+0x14]=bytes([0x80,0xfe]);r[offset+0x14:offset+0x18]=bytes([1,rate,step,phase])
                vectors.append((f'vibrato-{offset:03x}-{pointer:04x}-{rate}-{phase}-{step}',r))
    stop=None
    for mode in range(1,9):
        p=0xa52+(mode-1)*2;table=(bank[p]|bank[p+1]<<8)-0x8000
        for index in range(256):
            if bank[table+index]==0x83:stop=(mode,index);break
        if stop:break
    assert stop is not None
    for base,jump in zip([0xde80,0xfe80,0xdf80,0xff80],[0,1,2,3]):
        r=bytearray(400);r[5]=128;r[0x40]=128;r[0x41]=0x80;r[0x46]=stop[0];r[0x4a]=2
        r[0x4b:0x4d]=base.to_bytes(2,'little');r[0x55]=stop[1];r[((base+1)&0x1fff)-0x1e00]=jump
        vectors.append((f'pitch83-mirror-{base:04x}',r))
    for region in ['auto','pal']:
        for name,initial in vectors:
            prediction=reader_refresh(source,initial);returned={}
            for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                dll.gaw_timing_reset();result={};base=0x1e00 if tag=='sms' else symbols['sound_ram']
                writes=[(300,base,bytes(initial))]
                if tag=='md':writes.extend([(300,symbols['sound_request'],bytes(2)),(300,symbols['sound_effect_request'],bytes(2))])
                def observe(frame,ram):
                    if frame!=300:return
                    if tag=='sms':
                        n=dll.gaw_live_envelope_samples();raw=c.string_at(c.addressof(dll.gaw_live_envelope_events().contents)+(n-1)*824,824)
                        result.update(de=struct.unpack_from('<I',raw,8)[0],state=raw[424:824])
                    else:
                        def data(a,n):return bytes(ram[(a+i)^1] for i in range(n))
                        result.update(de=int.from_bytes(data(symbols['sound_source_de'],2),'big'),state=data(symbols['sound_ram'],400))
                        assert int.from_bytes(data(symbols['sound_unhandled_command'],2),'big')==0
                folder=ROOT/f'validation/production-audio-pitch/{name}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(rom,300,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,core=core,
                        core_options={'genesis_plus_gx_region_detect':region})
                assert (result['de'],result['state'])==(prediction['de'],prediction['state']),(region,name,tag,'DE/state')
                (folder/'de-reader.bin').write_bytes(struct.pack('<I',result['de'])+result['state'])
                returned[tag]=hashlib.sha256((folder/'de-reader.bin').read_bytes()).hexdigest()
            cases.append(dict(region=region,name=name,records=returned));print(region,name,'DE/all400 bytes exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,
                original_sha256=hashlib.sha256(source).hexdigest(),synthetic_state_injection=True,
                limits=['One aligned source/native IRQ and independent model; full400 bytes andreturnedDE.',
                        'Six tone slots, signed modulation/counters, originalROM andmirrored modulation RAM, pitch83 through DE/FE/DF/FF aliases.',
                        'Controlled states; no new waveform,hardware,allmemory orwhole-game timing proof.'])
    (ROOT/'validation/production_audio_pitch_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
