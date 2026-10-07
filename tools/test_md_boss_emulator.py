#!/usr/bin/env python3
"""Real-arena boss integration with a one-time equipped checkpoint fixture.

The production scene loader spawns the full-HP boss and loads graphics. After
fixture preparation only libretro joypad inputs change gameplay; the driver
uses positions for movement and production inventory menus for healing.
Requires private ROM data and a pinned Genesis Plus GX core. Optional SMS
runs check outcomes independently because physical entropy and cadence differ.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ARENAS=json.loads((Path(__file__).resolve().parent.parent/'tests/scenarios/boss_arenas.json').read_text())


def validate(result,arena):
    boss=result['boss']
    assert boss['fixture']['cell']==arena['cell'] and result['world_cell']==arena['cell'], 'Wrong boss arena'
    assert boss['fixture']['type']==arena['type'] and boss['fixture']['index']==arena['index'], 'Wrong boss/progression index'
    initial=boss['phases'][0]
    assert initial['type']==arena['type'] and initial['hp']==arena['hp'], 'Boss did not start at original full HP'
    assert result['player_hp']>0 and result['combat']['attacks'], 'No controller combat/survival'
    hits=boss['hits']
    assert hits and len(boss['deaths'])==1, 'Missing boss damage/death'
    remaining=arena['hp']
    for hit in hits:
        assert hit['before']==remaining and 0<=hit['after']<remaining, 'Broken boss HP sequence'
        assert hit['type'] in (arena['type'],7), 'Unexpected damage target'
        if hit['after']:assert hit['flash'], 'Missing hit invulnerability'
        remaining=hit['after']
    assert remaining==0 and boss['deaths'][0]['after']==0, 'Boss was not defeated'
    assert (7,2) in [(p['type'],p['state']) for p in boss['phases']], 'Missing boss death animation'
    assert boss['final_entities'][16]['type']==0, 'Boss/reward slot not cleared'
    if arena['index']==10:
        assert boss.get('ending_handoff') and result['final_state']=='0E' and boss['progress']==1, 'Missing final-boss ending handoff'
        assert boss['final_item']==1, 'Final boss was not fought with the axe'
    else:
        assert boss['reward_spawned'] and boss['reward_collected'] and boss.get('reward_acknowledged') and boss['progress']==0x80, 'Missing completed reward pickup'
        assert result['final_state']=='0C' and result['player_hp']==128, 'Reward healing did not finish'
    if arena['type']==101:
        assert {p['slot'] for p in boss['satellites_spawned']}==set(range(24,32)), 'Eight satellites were not spawned'
        assert {p['slot'] for p in boss['satellites_killed']}==set(range(24,32)), 'Eight satellites were not killed'
    if arena['type']==103:
        assert {p['slot'] for p in boss['parts_spawned']}==set(range(17,22)), 'Five boss parts were not spawned'
    assert result['audio_peak']>1024, 'No audible game audio'
    if result.get('play_irqs'):assert result['play_irqs']['vblank']>100, 'Hardware interrupts stalled'
    return {'type':arena['type'],'cell':arena['cell'],'index':arena['index'],
            'initial_hp':arena['hp'],'hits':len(hits),'player_hits':len(result['combat']['player_hits']),
            'projectiles':len(boss['projectiles']),'heal_hp':sum(h['after']-h['before'] for h in boss['heals']),
            'reward':boss['reward_collected'],'ending':boss.get('ending_handoff',False),
            'final_hp':result['player_hp'],'physical_frames':result['emulator_frames']}


def validate_wrong_weapon(result):
    boss=result['boss']
    assert boss['fixture']['type']==109 and boss['fixture']['item']==0
    assert len(result['combat']['attacks'])>=5, 'Insufficient sword attempts'
    assert result['player_hp']>0 and result['final_state']=='0C'
    assert not boss['hits'] and not boss['deaths'], 'Sword damaged the axe-gated final boss'
    assert boss['final_entities'][16]['type']==109 and boss['final_entities'][16]['hp']==90
    assert boss['final_item']==0, 'Wrong-weapon probe changed to the axe'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--rom',type=Path,default=Path('md/build/gaw_md.bin'))
    parser.add_argument('--elf',type=Path,default=Path('md/build/gaw_md.elf'))
    parser.add_argument('--nm',default='m68k-elf-nm')
    parser.add_argument('--reference-rom',type=Path)
    parser.add_argument('--bosses',type=int,nargs='+',choices=[a['type'] for a in ARENAS],default=[a['type'] for a in ARENAS])
    parser.add_argument('--output',type=Path,default=Path('md/build/boss-test'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    runner=Path(__file__).resolve().with_name('test_md_emulator.py')
    common=[sys.executable,str(runner),'--core',str(args.core),'--combat']
    runs=[('md',['--rom',str(args.rom),'--elf',str(args.elf),'--nm',args.nm])]
    if args.reference_rom:runs.append(('sms',['--reference-sms','--rom',str(args.reference_rom)]))
    results={}
    for name,extra in runs:
        results[name]=[]
        for arena in ARENAS:
            if arena['type'] not in args.bosses:continue
            output=args.output/name/str(arena['type']);output.mkdir(parents=True,exist_ok=True)
            with (output/'run.log').open('w') as log:
                subprocess.run(common+extra+['--boss-arena',str(arena['type']),'--frames','15000','--output',str(output)],stdout=log,stderr=subprocess.STDOUT,check=True)
            result=validate(json.loads((output/'result.json').read_text()),arena)
            results[name].append(result);print(name+': '+json.dumps(result),flush=True)
        if 109 in args.bosses:
            output=args.output/name/'wrong-weapon';output.mkdir(parents=True,exist_ok=True)
            with (output/'run.log').open('w') as log:
                subprocess.run(common+extra+['--boss-arena','109','--boss-weapon','sword','--boss-weapon-probe','--frames','2200','--output',str(output)],stdout=log,stderr=subprocess.STDOUT,check=True)
            validate_wrong_weapon(json.loads((output/'result.json').read_text()))
            print(name+': final boss rejects sword: OK',flush=True)
    (args.output/'result.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':main()
