"""Observe whether a noise F2 incorrectly lets a following effect tick."""
import argparse,contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);args=parser.parse_args()
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    initial=bytearray(400);initial[5]=128;initial[0xd0]=128;initial[0xd1]=0xe0;initial[0xda]=1;initial[0xd3:0xd5]=bytes([0x80,0xde]);initial[0x80]=0xf2
    initial[0x100]=128;initial[0x101]=0xa0;initial[0x10a]=2;cases=[]
    for region in ['auto','pal']:
        records={}
        for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
            result={};base=0x1e00 if tag=='sms' else symbols['sound_ram'];writes=[(300,base,bytes(initial))]
            if tag=='md':writes.extend([(300,symbols['sound_request'],bytes(2)),(300,symbols['sound_effect_request'],bytes(2))])
            def observe(frame,ram):
                if frame==300:result['state']=(bytes(ram[0x1e00:0x1f90]) if tag=='sms' else bytes(ram[(symbols['sound_ram']+i)^1] for i in range(400)))
            folder=ROOT/f'validation/noise-reader-exit-{args.label}/{region}-{tag}'
            with contextlib.redirect_stdout(io.StringIO()):run(rom,300,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
            (folder/'reader.bin').write_bytes(result['state']);records[tag]=result['state']
        differences=[dict(offset=i,source=a,native=b) for i,(a,b) in enumerate(zip(records['sms'],records['md'])) if a!=b]
        cases.append(dict(region=region,source_effect_counter=records['sms'][0x10a],native_effect_counter=records['md'][0x10a],differences=differences))
        print(region,cases[-1],flush=True)
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),cases=cases,
                controlled_state=True,scope='NoiseF2 must return from the whole8000 reader before the next effect channel.')
    (ROOT/f'analysis/noise_reader_exit_{args.label}_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
