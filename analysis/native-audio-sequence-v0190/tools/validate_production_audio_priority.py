"""Priority queue, ordinary-effect interruption and automatic8211 resumption."""
import argparse,contextlib,hashlib,io,json,re
from actor_reference import ROOT
from run_core import run

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--region',choices=['auto','pal','both'],default='both')
    parser.add_argument('--command',type=lambda s:int(s,0));args=parser.parse_args()
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535
             for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines()
             if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    regions=['auto','pal'] if args.region=='both' else [args.region];results=[]
    for region in regions:
        for command in ([args.command] if args.command is not None else range(0x90,0xad)):
            records={};psg={};errors={}
            initial=bytearray(400);initial[3]=128 if region=='auto' else 0;initial[5]=128;initial[6]=0x84
            events=[(360,9,command),(420,8,0x95),(600,9,128),(700,9,command)]
            for tag,rom in [('sms',ROOT/'input/original.sms'),('md',ROOT/'gaw-megadrive.bin')]:
                states={};sound={};unsupported={};base=0x1e00 if tag=='sms' else symbols['sound_ram']
                writes=[(300,base,bytes(initial))]+[(f,base+lane,bytes([value])) for f,lane,value in events]
                if tag=='md':writes.extend([(300,symbols['sound_request'],bytes(2)),(300,symbols['sound_effect_request'],bytes(2))])
                def observe(frame,ram):
                    if frame<301:return
                    states[frame]=(bytes(ram[0x1e00:0x1f90]) if tag=='sms' else
                                   bytes(ram[(symbols['sound_ram']+i)^1] for i in range(400)))
                    if tag=='md':unsupported[frame]=int.from_bytes(bytes(ram[(symbols['sound_unhandled_command']+i)^1] for i in range(2)),'big')
                folder=ROOT/f'validation/production-audio-priority/{command:02x}-{region}-{tag}'
                with contextlib.redirect_stdout(io.StringIO()):
                    run(rom,1000,folder,set(),[],ram_writes=writes,skip_intro=False,ram_observer=observe,
                        psg_observer=lambda f,p:sound.update({f:p}),
                        core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_libretro.dll',
                        core_options={'genesis_plus_gx_region_detect':region})
                (folder/'reader-records.bin').write_bytes(b''.join(states.values()))
                (folder/'psg.json').write_text(json.dumps(sound,separators=(',',':'))+'\n')
                records[tag]=states;psg[tag]=sound;errors[tag]=unsupported
            assert not any(errors['md'].values()),(region,hex(command),'unsupported',set(errors['md'].values()))
            # GG stereo routing has no mono MegaDrive equivalent; all399 other
            # reader bytes and all audible PSG channels must be identical.
            mismatches=[(f,i,records['sms'][f][i],records['md'][f][i]) for f in records['sms'] for i in range(400)
                        if i!=0x12 and records['sms'][f][i]!=records['md'][f][i]]
            assert not mismatches,(region,hex(command),'RAM',len(mismatches),mismatches[:12])
            def audible(p):return p[:6]+((p[6] if p[7] else 0),p[7])
            bad=[(f,psg['sms'][f],psg['md'][f]) for f in records['sms'] if audible(psg['sms'][f])!=audible(psg['md'][f])]
            assert not bad,(region,hex(command),'PSG',bad[:5])
            assert records['sms'][360][14]==command and records['sms'][700][14]==command
            assert records['sms'][600][9]==0 and records['sms'][600][14]==0
            results.append(dict(region=region,command=command,events=events,irq_states_exact=len(records['sms']),
                                compared_RAM_bytes=399,audible_psg_states_exact=len(records['sms'])))
            print(region,hex(command),'priority/interruption/clear/restart RAM+PSG exact',flush=True)
    name=f'production_audio_priority_{args.region}_report.json' if args.command is None else f'production_audio_priority_diagnostic_{args.region}_{args.command:02x}.json'
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),
                original_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),results=results,
                controlled_reader_state_and_commands=True,full_game_ported=False,
                limits=['Initial400-byte reader state and four event requests injected; real source/native readers executed.',
                        'GG stereo state excluded; muted-noise frequency excluded. No waveform,hardware or natural-event-hook proof.'])
    (ROOT/'validation'/name).write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
