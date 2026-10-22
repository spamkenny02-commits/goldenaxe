"""Replay a real axe acquisition, equip it, close inventory, attack normally."""
import argparse,contextlib,io,json
from run_core import ROOT,run
from validate_playable_sprite_limit import symbols
from archive_lossless_evidence import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--sms',action='store_true');p.add_argument('--tag',required=True);args=p.parse_args()
    tag='sms' if args.sms else 'md';folder=ROOT/f'validation/natural-dungeon-combat/{tag}-auto-27'
    c=json.loads((folder/'capture.json').read_bytes());prior=json.loads((folder/'report.json').read_bytes());controls=json.loads((folder/'controls.json').read_bytes());end=c['frames']
    rom=ROOT/('input/original.sms' if args.sms else 'gaw-megadrive.bin');assert sha(rom.read_bytes())==c['rom_sha256'] and prior['room_cleared'] and not prior['failure']
    assert not c['test_ram_writes'] and c['sram_input'] is None
    timeline=[()]*(end+1)
    for n,x in enumerate(controls):
        stop=controls[n+1]['frame']-1 if n+1<len(controls) else end
        timeline[x['frame']:stop+1]=[tuple(x['buttons'])]*(stop-x['frame']+1)
    sy=symbols(ROOT/'megadrive/out/release/symbol.txt');rows=[]
    def observe(f,r):
        if f<end:return
        word=lambda n:int.from_bytes(bytes(r[(sy[n]+i)^1] for i in range(2)),'big')
        row=dict(frame=f-end,game=r[0x1d] if args.sms else word('game_state'),slot=r[0xa0] if args.sms else word('inventory_slot'),selected=r[0xdf] if args.sms else word('hero_selected_item'),weapon=r[0xe1] if args.sms else word('hero_weapon_level'),hero=r[0x301] if args.sms else word('hero_state'),health=r[0x318] if args.sms else word('hero_health'))
        rows.append(row)
    nav=[(end+5,end+6,0),(end+45,end+46,7),(end+60,end+61,8),(end+90,end+91,0),(end+150,end+151,8)]
    out=ROOT/f'validation/natural-axe-{args.tag}-{tag}';assert not out.exists()
    with contextlib.redirect_stdout(io.StringIO()):run(rom,end+210,out,{end,end+55,end+80,end+140,end+165,end+210},c['presses']+nav,input_provider=lambda f:timeline[f] if f<=end else (),ram_observer=observe)
    at=lambda f:next(x for x in rows if x['frame']==f)
    assert at(0)['game']==12 and at(0)['weapon']==1 and at(0)['selected']==0
    assert at(55)['game']==16 and at(55)['slot']==1
    assert at(80)['game']==16 and at(80)['selected']==1
    assert at(140)['game']==12 and at(140)['selected']==1
    attacks=[x for x in rows if 150<=x['frame']<=190 and x['hero'] in [4,5]];assert attacks
    assert at(210)['game']==12 and at(210)['selected']==1 and at(210)['weapon']==1 and at(210)['health']>0
    (out/'states.json').write_text(json.dumps(rows,indent=2)+'\n')
    result=dict(rom_sha256=c['rom_sha256'],passed=True,normal_boot_and_buttons=True,ram_writes=False,sram_input=None,acquisition_case=str(folder.relative_to(ROOT)),prefix_deaths=prior['deaths'],equipped_slot=1,attack_frames=len(attacks),final=at(210))
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)

if __name__=='__main__':main()
