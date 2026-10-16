"""Controlled real-reader83/ADSR boundaries, including original return DE."""
import contextlib,ctypes as c,hashlib,io,json,re,struct
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from run_core import run

def main():
    source=(ROOT/'input/original.sms').read_bytes();symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535
        for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
        if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_livereaderrefresh_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_live_envelope_samples.restype=c.c_uint;dll.gaw_live_envelope_events.restype=c.POINTER(c.c_uint8)
    vectors=[];cases=[]
    for transpose in [0,1,2,3,7,15,16,31,63,127]:
        r=bytearray(400);r[5]=128;r[0x40]=128;r[0x41]=0x80;r[0x46]=128;r[0x4a]=2;r[0x4b:0x4d]=bytes([0x20,1]);r[0x54]=2;r[0x65]=transpose
        r[0x70]=128;r[0x71]=0xa0;r[0x77]=9;r[0x7a]=2;r[0x8f]=10
        vectors.append((f'table83-de-{transpose:02x}',r))
    for phase,value,step,limit in [(16,1,2,127),(16,255,0,127),(32,250,20,127),(40,127,1,127),(64,254,1,127),(0,255,1,127)]:
        for borrowed in [0,4]:
            r=bytearray(400);r[5]=128;r[0xd0]=128|borrowed;r[0xd1]=0xe0;r[0xd7]=128;r[0xda]=2
            r[0xed]=phase;r[0xef]=value;r[0xf0:0xf5]=bytes([step,step,limit,step,step])
            vectors.append((f'adsr-{phase}-{value}-{step}-{borrowed}',r))
    # Artificial pitch modes/indices reach81/82 outside the eight known tables.
    # These terminal paths
    # must unwind before touching the following ADSR envelope or PSG pitch.
    bank=source[0x18000:0x1c000];seen=set()
    for mode in range(1,128):
        p=0xa52+(mode-1)*2;table=bank[p]|bank[p+1]<<8
        if not (table<0x7f00 or 0x8000<=table<0xbf00):continue
        for index in range(256):
            address=table+index
            value=source[address] if address<0x8000 else bank[address-0x8000]
            if value not in [0x81,0x82] or value in seen:continue
            seen.add(value);r=bytearray(400);r[5]=128;r[0x40]=128;r[0x41]=0x80
            r[0x46]=mode;r[0x47]=128;r[0x4a]=2;r[0x4b:0x4d]=bytes([0x20,1]);r[0x55]=index
            r[0x5d]=16;r[0x5f]=255;r[0x60]=5
            vectors.append((f'pitch-unwind-{value:02x}',r))
    assert seen=={0x81,0x82},seen
    for region in ['auto','pal']:
        for name,initial in vectors:
            prediction=reader_refresh(source,initial);expected=prediction['state'];returned={}
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
                folder=ROOT/f'validation/production-audio-envelope/{name}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(rom,300,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,core=core,
                        core_options={'genesis_plus_gx_region_detect':region})
                assert (result['de'],result['state'])==(prediction['de'],expected),(region,name,tag,result['de'],prediction['de'])
                (folder/'de-reader.bin').write_bytes(struct.pack('<I',result['de'])+result['state'])
                returned[tag]=hashlib.sha256((folder/'de-reader.bin').read_bytes()).hexdigest()
            cases.append(dict(region=region,name=name,records=returned));print(region,name,'DE/all400 bytes exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,
                original_sha256=hashlib.sha256(source).hexdigest(),synthetic_state_injection=True,
                limits=['Single aligned real source/native IRQ; model/all400 bytes/returnedDE compared.',
                        'Table83 after another channel produces ten different low-ROM DE inputs; six ADSR boundaries with/without borrowed noise; two synthetic pitch81/82 unwinds outside eight known pitch tables.',
                        'Other RAM mirrors/uncaptured memory and waveform/full-game timing remain outside this check.'])
    (ROOT/'validation/production_audio_envelope_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
