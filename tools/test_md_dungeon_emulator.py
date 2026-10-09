#!/usr/bin/env python3
"""Controller-only dungeon entry, traversal, boss/reward, return and ending.

Each run boots normally and prepares one equipped overworld checkpoint.
Afterwards the runner forbids RAM writes. Room crossings, keys, enemies,
inventory/healing, stairs, crystals and the ending execute in production code.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROUTES=json.loads((Path(__file__).resolve().parent.parent/'tests/scenarios/dungeon_routes.json').read_text())


def validate(result,route):
    assert result['dungeon'].get('start_room') is None, 'Room checkpoint is not a full-entry traversal'
    return validate_walk(result,route)


def validate_segment(result,route):
    start=result['dungeon'].get('start_room')
    assert route['index']==10 and start is not None, 'Expected a separate dungeon10 room checkpoint'
    first=next(i for i,e in enumerate(route['outbound']) if e['from']==start)
    suffix=dict(route,outbound=route['outbound'][first:])
    return validate_walk(result,suffix,start)


def validate_walk(result,route,start_room=None):
    dungeon=result['dungeon'];boss=result['boss']
    assert dungeon['index']==route['index']
    visits=dungeon['visits']
    if start_room is None:
        assert visits[0]['cell']==route['outside_cell'] and visits[0]['index']==0
        expected=[route['outside_cell'],route['entrance']]+[e['to'] for e in route['outbound']]
    else:
        assert visits[0]['cell']==start_room and visits[0]['index']==route['index']
        expected=[start_room]+[e['to'] for e in route['outbound']]
    if route['index']!=10:expected += [e['to'] for e in route['return']]+[route['outside_cell']]
    actual=[v['cell'] for v in visits]
    cursor=0
    for cell in actual:
        if cursor<len(expected) and cell==expected[cursor]:cursor+=1
    assert cursor==len(expected), 'Missing/out-of-order room traversal'
    crossings={(e['from'],e['to']) for e in route['outbound']+route['return']}
    crossings |= {(b,a) for a,b in list(crossings)}
    crossings |= {(route['outside_cell'],route['entrance']),(route['entrance'],route['outside_cell'])}
    assert all((a,b) in crossings for a,b in zip(actual,actual[1:])), 'Unexpected room crossing'
    assert all(v['index']==route['index'] for v in visits if v['cell']>=256)
    assert boss['phases'][0]['type']==route['boss']['type'] and boss['phases'][0]['hp']==route['boss']['hp']
    remaining=route['boss']['hp']
    for hit in boss['hits']:
        assert hit['before']==remaining and 0<=hit['after']<remaining
        remaining=hit['after']
    assert remaining==0 and len(boss['deaths'])==1, 'Missing genuine full-HP boss defeat'
    assert result['combat']['attacks'] and result['player_hp']>0
    if route['index']==10:
        end=result['ending']
        assert boss['ending_handoff'] and end['credits_started'] and end['credits_finished'] and end['title_confirmed']
        assert set(end['crystal_slots'])==set(range(16,25)) and len(end['scroll_values'])>150
        assert result['final_state']=='12'
    else:
        assert dungeon['done'] and dungeon['stage']=='exit' and dungeon['events'][-1]=='exited'
        assert visits[-1]['index']==0 and result['world_cell']==route['outside_cell']
        assert boss['reward_collected'] and boss['reward_acknowledged'] and boss['progress']==128
        assert result['final_state']=='0C'
    assert 0<=dungeon['keys_remaining']<=255
    assert result['audio_peak']>1024
    return {'index':route['index'],'start_room':start_room,'rooms':len(visits),'boss_hits':len(boss['hits']),
            'stairs':sum(bool(e.get('stairs')) for e in route['outbound']+([] if route['index']==10 else route['return'])),
            'keys_net_spent':None if route['index']==10 else 20-dungeon['keys_remaining'],'final_hp':result['player_hp'],'frames':result['emulator_frames']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--rom',type=Path,default=Path('md/build/gaw_md.bin'))
    parser.add_argument('--elf',type=Path,default=Path('md/build/gaw_md.elf'))
    parser.add_argument('--nm',default='m68k-elf-nm')
    parser.add_argument('--reference-rom',type=Path)
    parser.add_argument('--dungeons',type=int,nargs='+',choices=range(1,11),default=list(range(1,11)))
    parser.add_argument('--frames',type=int,default=60000)
    parser.add_argument('--output',type=Path,default=Path('md/build/dungeon-test'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    runner=Path(__file__).with_name('test_md_emulator.py')
    runs=[('md',['--rom',str(args.rom),'--elf',str(args.elf),'--nm',args.nm])]
    if args.reference_rom:runs.append(('sms',['--reference-sms','--rom',str(args.reference_rom)]))
    results={}
    for name,extra in runs:
        results[name]=[]
        for route in ROUTES:
            if route['index'] not in args.dungeons:continue
            output=args.output/name/str(route['index']);output.mkdir(parents=True,exist_ok=True)
            with (output/'run.log').open('w') as log:
                subprocess.run([sys.executable,str(runner),'--core',str(args.core),*extra,'--combat','--dungeon',str(route['index']),'--frames',str(args.frames),'--output',str(output)],stdout=log,stderr=subprocess.STDOUT,check=True)
            summary=validate(json.loads((output/'result.json').read_text()),route)
            results[name].append(summary);print(name+': '+json.dumps(summary),flush=True)
    (args.output/'result.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':main()
