"""Actual SMS/MD single-reader IRQ state checks for dispatch controls and limits."""
import contextlib,hashlib,io,json,re
from actor_reference import ROOT
from audio_reader_refresh import reader_refresh
from run_core import run

def main():
    source=(ROOT/'input/original.sms').read_bytes()
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535
             for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
             if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    vectors=[];cases=[]
    for command in [0x7f,0x80,0x81,0x8d,0x90,0xac,0xb0,0xb1,0xb2,0xb5,0xff]:
        vectors.append((command,0))
    for latch in [0,1,64,127,128,255]:vectors.append((0xb3,latch))
    for region in ['auto','pal']:
        for command,latch in vectors:
            initial=bytearray(400);initial[5]=command;initial[15]=latch
            initial[1:3]=bytes([3,7]);initial[0x131]=0xc0;initial[0x161]=0xe0
            # Track8D immediately uses noise F2, outside the timing model's scope.
            # Compare its actual two runtimes directly instead of inventing a cost.
            initial[0x22]=77;expected=None if command==0x8d else reader_refresh(source,initial)['state'];records={}
            for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                folder=ROOT/f'validation/production-audio-dispatch/{command:02x}-{latch:02x}-{region}-{tag}'
                writes=([(300,0x1e00,bytes(initial))] if tag=='sms' else
                        [(300,symbols['sound_ram'],bytes(initial)),(300,symbols['sound_request'],bytes(2)),(300,symbols['sound_effect_request'],bytes(2))])
                result={}
                def observe(frame,ram):
                    if frame==300:result['state']=(bytes(ram[0x1e00:0x1f90]) if tag=='sms' else
                                                  bytes(ram[(symbols['sound_ram']+i)^1] for i in range(400)))
                with contextlib.redirect_stdout(io.StringIO()):
                    run(rom,300,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,
                        core_options={'genesis_plus_gx_region_detect':region})
                if expected is None:expected=result['state'];model_available=False
                else:
                    assert result['state']==expected,(region,hex(command),latch,tag,[(i,a,b) for i,(a,b) in enumerate(zip(expected,result['state'])) if a!=b][:10])
                (folder/'reader.bin').write_bytes(result['state']);records[tag]=hashlib.sha256(result['state']).hexdigest()
            cases.append(dict(region=region,command=command,latch=latch,records=records,model_checked=command!=0x8d))
            print(region,hex(command),latch,'SMS/native400 bytes exact',flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                original_sha256=hashlib.sha256(source).hexdigest(),cases=cases,
                synthetic_state_injection=True,dispatch_integrated=True,full_clock_integrated=False,
                limits=['One aligned IRQ from controlled reader RAM; full400 bytes checked against actual source. Model also checked except track8D noise F2.',
                        'No whole-game or waveform claim; six unaudited command paths remain at legacy fallback.'])
    (ROOT/'validation/production_audio_dispatch_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
