"""Small console reports; full emulator observations remain in result.json."""


def console_summary(result, report_path):
    summary = {key: result[key] for key in
               ('emulator_frames', 'world_cell', 'player_hp', 'final_state')}
    summary['report'] = str(report_path)
    if result.get('cheats',{}).get('enabled'):
        summary['validation_mode']='assisted'
        summary['cheat_interventions']=len(result['cheats']['events'])
    if 'dungeon' in result:
        dungeon = result['dungeon']
        summary['dungeon'] = {key: dungeon[key] for key in ('index', 'stage', 'edge', 'done')}
        summary['dungeon']['visits'] = len(dungeon['visits'])
    if 'boss' in result:
        boss = result['boss']
        summary['boss'] = {key: len(boss[key]) for key in ('hits', 'deaths')}
        summary['boss']['reward_collected'] = boss['reward_collected']
    if 'ending' in result:
        summary['ending'] = {key: result['ending'].get(key, False) for key in
                             ('credits_started', 'credits_finished', 'title_confirmed')}
    return summary
