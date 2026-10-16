"""Observe real SMS reader-return DE and compare native cross-channel DE/state."""
import contextlib,ctypes as c,hashlib,io,json,re,struct
from actor_reference import ROOT
from run_core import run

def main():
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535
             for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
             if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_livereaderrefresh_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_live_envelope_samples.restype=c.c_uint
    dll.gaw_live_envelope_events.restype=c.POINTER(c.c_uint8);results=[]
    scenarios=[(f'music-{command:02x}',command,[]) for command in range(0x81,0x8e)]
    scenarios.extend([('effect-a6',0x84,[(360,8,0xa6)]),
                      ('priority-91',0x84,[(360,9,0x91),(420,8,0x95),(600,9,128)]),
                      ('priority-ac',0x84,[(360,9,0xac),(420,8,0x95),(600,9,128)])])
    for region in ['auto','pal']:
        for name,track,events in scenarios:
            initial=bytearray(400);initial[3]=128 if region=='auto' else 0;initial[5]=128;initial[6]=track;captured={}
            for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                dll.gaw_timing_reset();records={};previous=[0]
                base=0x1e00 if tag=='sms' else symbols['sound_ram'];writes=[(300,base,bytes(initial))]+[(f,base+lane,bytes([value])) for f,lane,value in events]
                if tag=='md':writes.extend([(300,symbols['sound_request'],bytes(2)),(300,symbols['sound_effect_request'],bytes(2))])
                def observe(frame,ram):
                    if frame<301:return
                    if tag=='sms':
                        count=dll.gaw_live_envelope_samples();assert count==previous[0]+1 or previous[0]==0
                        raw=c.string_at(c.addressof(dll.gaw_live_envelope_events().contents)+(count-1)*824,824)
                        de=struct.unpack_from('<I',raw,8)[0];state=raw[424:824];previous[0]=count
                    else:
                        def data(address,length):return bytes(ram[(address+i)^1] for i in range(length))
                        de=int.from_bytes(data(symbols['sound_source_de'],2),'big');state=data(symbols['sound_ram'],400)
                        assert int.from_bytes(data(symbols['sound_unhandled_command'],2),'big')==0
                    records[frame]=(de,state)
                folder=ROOT/f'validation/production-audio-de/{name}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(rom,1000,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,
                        core=core,core_options={'genesis_plus_gx_region_detect':region})
                (folder/'de-reader-records.bin').write_bytes(b''.join(struct.pack('<I',de)+state for de,state in records.values()))
                captured[tag]=records
            bad=[(f,captured['sms'][f][0],captured['md'][f][0]) for f in captured['sms'] if captured['sms'][f][0]!=captured['md'][f][0]]
            assert not bad,(region,name,'DE',len(bad),bad[:12])
            bad=[(f,i,captured['sms'][f][1][i],captured['md'][f][1][i]) for f in captured['sms'] for i in range(400)
                 if i!=0x12 and captured['sms'][f][1][i]!=captured['md'][f][1][i]]
            assert not bad,(region,name,'state',len(bad),bad[:12])
            results.append(dict(region=region,scenario=name,reader_return_DE_exact=len(captured['sms']),compared_RAM_bytes=399))
            print(region,name,'DE+399 reader bytes exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),results=results,
                core_sha256=hashlib.sha256(core.read_bytes()).hexdigest(),
                limits=['Controlled initial reader RAM and requests; real original reader DE observed at IRQ return.',
                        '13 tracks, ordinaryA6 andtwo priority/restore scenarios PAL/NTSC; GG stereo byte excluded.',
                        'Does not cover every DE-dependent command,whole foreground R/clock,hardware or waveforms.'])
    (ROOT/'validation/production_audio_de_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
