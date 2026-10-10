#!/usr/bin/env python3
"""Compare physical frame cadence at a pinned SMS/MD video standard.

This is a timing diagnostic, not a full-game equivalence validator. Reports
must come from the same controller scenario; random enemy paths may differ.
"""
import argparse
import json
from pathlib import Path


def metrics(report):
    fps=report['video_timing']['fps']
    assert fps>0
    stages=report['stages']
    first_play=next((s['emulator_frame'] for s in stages if s['state']=='0C'),None)
    transitions=[]
    for i,s in enumerate(stages):
        if s['state']!='0A':continue
        end=next((e['emulator_frame'] for e in stages[i+1:] if e['state']=='0C'),None)
        if end is not None:transitions.append(end-s['emulator_frame'])
    first_line=next((x['frame'] for x in report.get('timing_trace',[])
                     if x['intro_line']==1 and x['intro_text_pointer']==0xB9ED),None)
    return {'fps':fps,'play_frames':report['play_frames'],'play_ticks':report['play_ticks'],
            'updates_per_physical_frame':report['play_ticks']/report['play_frames'] if report['play_frames'] else None,
            'first_gameplay_frame':first_play,'first_gameplay_seconds':first_play/fps if first_play is not None else None,
            'transition_frames':transitions,'transition_seconds':[n/fps for n in transitions],
            'first_intro_line_frame':first_line,'first_intro_line_seconds':first_line/fps if first_line is not None else None}


def compare(md,sms):
    assert not md.get('cheats',{}).get('enabled') and not sms.get('cheats',{}).get('enabled'), 'Cheat reports cannot measure normal cadence'
    assert md['video_timing']['region_requested']==sms['video_timing']['region_requested'] and md['video_timing']['region_requested'] in ('ntsc','pal'), 'Pin the same region on both runs'
    a,b=metrics(md),metrics(sms)
    assert abs(a['fps']-b['fps'])<0.001, 'Different video standards'
    ratio=a['updates_per_physical_frame']/b['updates_per_physical_frame'] if a['play_frames'] and b['play_frames'] else None
    return {'md':a,'sms':b,'md_gameplay_cadence_relative_to_sms':ratio,
            'scope':'Timing diagnostic; use the same controller scenario, not proof of gameplay or visual equivalence'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--md',type=Path,required=True)
    parser.add_argument('--sms',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=compare(json.loads(args.md.read_text()),json.loads(args.sms.read_text()))
    text=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    print(text,end='')


if __name__=='__main__':main()
