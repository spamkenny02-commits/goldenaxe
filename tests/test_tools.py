import importlib.util
import copy
import sys
import json
import re
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'embed_rom', Path(__file__).resolve().parents[1]/'tools/embed_rom.py')
embed_rom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(embed_rom)
capture_spec = importlib.util.spec_from_file_location(
    'compare_game_viewports', Path(__file__).resolve().parents[1]/'tools/compare_game_viewports.py')
captures = importlib.util.module_from_spec(capture_spec)
capture_spec.loader.exec_module(captures)


class EmulatorConsoleReportTest(unittest.TestCase):
    def test_large_trace_stays_in_file_report_without_changing_data(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
        from emulator_report import console_summary
        result = {'emulator_frames': 61782, 'world_cell': 0x18A,
                  'player_hp': 0, 'final_state': '0C',
                  'dungeon': {'index': 10, 'stage': 'outbound', 'edge': 16,
                              'done': False, 'visits': [{}]*25},
                  'boss': {'hits': [{}]*5000, 'deaths': [], 'reward_collected': False},
                  'combat': {'attacks': [{}]*10000},
                  'ending': {'credits_started': False}}
        before = copy.deepcopy(result)
        summary = console_summary(result, Path('run/result.json'))
        self.assertEqual(result, before)
        self.assertEqual(summary['boss']['hits'], 5000)
        self.assertEqual(summary['dungeon']['visits'], 25)
        self.assertFalse(summary['ending']['title_confirmed'])
        self.assertEqual(summary['report'], 'run/result.json')
        self.assertNotIn('combat', summary)
        self.assertLess(len(json.dumps(summary)), 600)

    def test_plain_run_needs_no_combat_or_dungeon(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
        from emulator_report import console_summary
        result = {'emulator_frames': 2000, 'world_cell': 137,
                  'player_hp': 128, 'final_state': '0C'}
        self.assertEqual(console_summary(result, 'result.json'),
                         dict(result, report='result.json'))


class BossArenaMetadataTest(unittest.TestCase):
    def test_real_full_hp_boss_rooms(self):
        root=Path(__file__).resolve().parents[1]
        arenas=json.loads((root/'tests/scenarios/boss_arenas.json').read_text())
        numbers=lambda name:[int(x,16) for x in re.findall(r'0x([0-9A-Fa-f]+)',(root/'src'/name).read_text())]
        types=numbers('world_entity_types.inc');stats=numbers('map_entity_stats.inc')
        self.assertEqual(len(numbers('death_drop_rules.inc')),(max(numbers('death_drop_classes.inc'))+1)*16)
        bosses={i+32 for i in range(96) if stats[i*4+3]&0x40}-{102}
        self.assertEqual({a['type'] for a in arenas},bosses)
        self.assertEqual({a['index'] for a in arenas},set(range(1,11)))
        for arena in arenas:
            self.assertEqual(types[arena['cell']*8],arena['type'])
            self.assertEqual(stats[(arena['type']-32)*4],arena['hp'])


class DungeonRouteTest(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / 'tools'))
        from test_md_dungeon_emulator import ROUTES, validate
        self.routes, self.validate = ROUTES, validate

    def test_routes_are_continuous_and_reach_real_bosses(self):
        self.assertEqual([r['index'] for r in self.routes], list(range(1, 11)))
        for route in self.routes:
            for key, start, finish in [('outbound', route['entrance'], route['boss']['cell']),
                                       ('return', route['boss']['cell'], route['entrance'])]:
                cell = start
                for edge in route[key]:
                    self.assertEqual(edge['from'], cell)
                    self.assertIn(edge['to'], route['rooms'])
                    self.assertEqual(len(edge['target']), 2)
                    cell = edge['to']
                self.assertEqual(cell, finish)

    def test_dungeon8_activates_remote_switch_before_western_gate(self):
        route = self.routes[7]
        edges = route['outbound']
        gate = next(i for i,e in enumerate(edges)
                    if (e['from'],e['to']) == (0x1D8,0x1D7))
        self.assertIn(0x19A, [e['to'] for e in edges[:gate]])
        self.assertEqual(route['actions'][str(0x19A)], [72,40])

    def test_dungeon10_reenters_partitioned_room_from_west(self):
        edges = self.routes[9]['outbound']
        gate = next(i for i,e in enumerate(edges)
                    if (e['from'],e['to']) == (0x16C,0x15C))
        self.assertEqual((edges[gate-1]['from'],edges[gate-1]['to']),
                         (0x16B,0x16C))
        self.assertTrue(any(e.get('stairs') and e['from']==0x16C
                            for e in edges[:gate]))

    def test_dungeon10_activates_remote_switch_before_17b_stairs(self):
        route = self.routes[9]
        edges = route['outbound']
        stairs = next(i for i,e in enumerate(edges)
                      if (e['from'],e['to']) == (0x17B,0x13C))
        prefix = [route['entrance']] + [e['to'] for e in edges[:stairs]]
        first = prefix.index(0x17B)
        self.assertEqual(prefix[first-1], 0x18B)
        self.assertIn(0x17C, prefix[first+1:])
        self.assertEqual((edges[stairs-1]['from'],edges[stairs-1]['to']),
                         (0x17A,0x17B))
        switch_return = next(i for i,e in enumerate(edges) if (e['from'],e['to'])==(0x17C,0x17B))
        self.assertEqual([(e['from'],e['to']) for e in edges[switch_return+1:stairs]],
                         [(0x17B,0x18B),(0x18B,0x18A),(0x18A,0x17A),(0x17A,0x17B)])
        self.assertEqual(route['actions'][str(0x17C)], [184,40])

    def test_dungeon10_returns_to_14b_from_west_after_switch(self):
        route = self.routes[9]
        edges = route['outbound']
        stairs = next(i for i,e in enumerate(edges)
                      if (e['from'],e['to']) == (0x14B,0x15A))
        self.assertEqual([(e['from'],e['to']) for e in edges[stairs-4:stairs]],
                         [(0x14B,0x13B),(0x13B,0x13A),(0x13A,0x14A),(0x14A,0x14B)])
        self.assertEqual(route['actions'][str(0x14B)], [184,40])

    def test_room_checkpoint_cannot_be_reported_as_full_entry(self):
        report = self.complete_run()
        report['dungeon']['start_room'] = 0x13C
        with self.assertRaisesRegex(AssertionError, 'not a full-entry'):
            self.validate(report, self.routes[0])

    def test_suffix_requires_entire_walk_full_boss_and_complete_ending(self):
        from test_md_dungeon_emulator import validate_segment
        route = self.routes[9]
        first = next(i for i,e in enumerate(route['outbound']) if e['from']==0x13C)
        cells = [0x13C]+[e['to'] for e in route['outbound'][first:]]
        result = {'dungeon': {'index':10,'start_room':0x13C,'keys_remaining':0,
                  'visits':[{'cell':c,'index':10} for c in cells]},
                  'boss': {'phases':[route['boss']],
                           'hits':[{'before':90,'after':0}],'deaths':[{}],
                           'ending_handoff':True},
                  'ending': {'credits_started':True,'credits_finished':True,
                             'title_confirmed':True,'crystal_slots':list(range(16,25)),
                             'scroll_values':list(range(151))},
                  'combat':{'attacks':[{}]},'player_hp':62,
                  'final_state':'12','audio_peak':2048,'emulator_frames':56382}
        self.assertEqual(validate_segment(result,route)['start_room'],0x13C)
        self.assertIsNone(validate_segment(result,route)['keys_net_spent'])
        missing = copy.deepcopy(result)
        del missing['dungeon']['visits'][2]
        with self.assertRaises(AssertionError):validate_segment(missing,route)
        missing = copy.deepcopy(result)
        missing['ending']['crystal_slots'].pop()
        with self.assertRaises(AssertionError):validate_segment(missing,route)
        with self.assertRaises(AssertionError):self.validate(result,route)

    def test_dungeon9_uses_upper_gate_after_room_clear(self):
        edge = next(e for e in self.routes[8]['outbound'] if e['from']==0x1BE)
        self.assertEqual(edge['to'], 0x1AE)
        self.assertEqual(edge['direction'], 'up')

    def test_dungeon9_opens_boss_gate_from_neighbor_switch(self):
        edges = self.routes[8]['outbound']
        gate = next(i for i,e in enumerate(edges)
                    if (e['from'],e['to']) == (0x1BC,0x1AC))
        self.assertEqual([(e['from'],e['to']) for e in edges[gate-2:gate]],
                         [(0x1BC,0x1BD),(0x1BD,0x1BC)])
        self.assertEqual(self.routes[8]['actions'][str(0x1BD)], [184,40])

    def complete_run(self):
        route = self.routes[0]
        cells = [route['outside_cell'], route['entrance']]
        cells += [e['to'] for e in route['outbound'] + route['return']]
        cells += [route['outside_cell']]
        return {'dungeon': {'index': 1, 'done': True, 'stage': 'exit',
                'events': ['exited'], 'keys_remaining': 18,
                'visits': [{'cell': c, 'index': 1 if c >= 256 else 0} for c in cells]},
                'boss': {'phases': [route['boss']],
                'hits': [{'before': route['boss']['hp'], 'after': 0}],
                'deaths': [{}], 'reward_collected': True,
                'reward_acknowledged': True, 'progress': 128},
                'combat': {'attacks': [{}]}, 'player_hp': 128,
                'world_cell': route['outside_cell'], 'final_state': '0C',
                'audio_peak': 2048, 'emulator_frames': 10000}

    def test_complete_run_and_real_retreat(self):
        report = self.complete_run()
        self.validate(report, self.routes[0])
        visits = report['dungeon']['visits']
        visits[3:3] = [copy.deepcopy(visits[1]), copy.deepcopy(visits[2])]
        self.validate(report, self.routes[0])

    def test_incomplete_or_fabricated_success_is_rejected(self):
        base = self.complete_run()
        reports = []
        missing = copy.deepcopy(base)
        del missing['dungeon']['visits'][2]
        reports.append(missing)
        wrong_hp = copy.deepcopy(base)
        wrong_hp['boss']['phases'][0] = dict(wrong_hp['boss']['phases'][0], hp=1)
        reports.append(wrong_hp)
        skipped_hits = copy.deepcopy(base)
        skipped_hits['boss']['hits'] = []
        reports.append(skipped_hits)
        no_reward = copy.deepcopy(base)
        no_reward['boss']['reward_acknowledged'] = False
        reports.append(no_reward)
        for report in reports:
            with self.assertRaises(AssertionError):
                self.validate(report, self.routes[0])


class CombatGeometryTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
        from combat_geometry import rect, overlaps, axe_openings
        self.rect,self.overlaps,self.openings=rect,overlaps,axe_openings

    def test_axes_and_signed_offsets_follow_original_order(self):
        self.assertEqual(self.rect((128,80),5),(121,65,13,13))

    def test_original_collision_accepts_only_one_touching_endpoint(self):
        self.assertTrue(self.overlaps((10,10,8,8),(2,10,8,8)))
        self.assertFalse(self.overlaps((10,10,8,8),(18,10,8,8)))

    def test_same_distance_has_different_safe_weapon_reach(self):
        self.assertIn(3,self.openings((100,80),(128,80),44,44))
        self.assertEqual(self.openings((156,80),(128,80),44,44),())
        self.assertEqual(self.openings((128,52),(128,80),44,44),())

    def test_inactive_hitbox_has_no_opening(self):
        self.assertEqual(self.openings((100,80),(128,80),0,44),())


class DungeonNavigationTest(unittest.TestCase):
    def driver(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        from dungeon_driver import DungeonDriver
        self.ram = bytearray(8192)
        for address, value in [(0xC0BA, 1), (0xC0B9, 0x25),
                               (0xC313, 88), (0xC311, 80), (0xC0DB, 16)]:
            self.ram[address - 0xC000] = value
        return DungeonDriver({'avoid': {}}, lambda a: self.ram[a - 0xC000],
                             {'up': 0, 'down': 1, 'left': 2, 'right': 3,
                              'button1': 4, 'button2': 5})

    def loop_driver(self, destinations):
        driver = self.driver()
        cells = [0x138] + destinations
        driver.route = {'outbound': [
            {'from': a, 'to': b, 'target': [128, 8]}
            for a, b in zip(cells, cells[1:])], 'index': 6}
        driver.stage = 'outbound'
        driver.navigate = lambda target: 0
        self.arrive(driver, 0x138)
        return driver

    def arrive(self, driver, cell):
        self.ram[0xB9] = cell & 255
        self.ram[0xBA] = cell >> 8
        driver.drive(0x0C, False)

    def test_waits_for_actual_death_loot_before_exit(self):
        driver = self.loop_driver([0x139])
        driver.route.update(index=10, collect_before_exit=True)
        self.ram[0x600],self.ram[0x607] = 1,90
        driver.navigate = lambda target: self.fail('Left before the corpse resolved')
        self.assertEqual(driver.drive(0x0C,False),0)

    def test_navigation_avoids_cycling_pit_even_in_open_phase(self):
        driver=self.driver()
        self.ram[0xB9]=0x4A
        self.ram[0x1C46]=0x41
        driver.navigate((120,80))
        self.assertIn((104,80),driver.path)
        driver.route['damage_terrain_cells']=(0x14A,)
        driver.target=None
        driver.navigate((120,80))
        self.assertNotIn((104,80),driver.path)
        self.assertEqual(driver.path[-1],(120,80))

    def test_damage_terrain_probe_does_not_change_another_room(self):
        driver=self.driver()
        self.ram[0x1C46]=0x4F
        driver.route['damage_terrain_cells']=(0x14A,)
        driver.navigate((120,80))
        self.assertIn((104,80),driver.path)

    def test_contact_navigation_avoids_body_and_refreshes_when_hitbox_deactivates(self):
        from combat_geometry import rect, overlaps
        driver=self.driver()
        self.ram[0xB9]=0x4B
        self.ram[0x600],self.ram[0x603]=73,3
        self.ram[0x613],self.ram[0x611],self.ram[0x61C]=104,112,40
        body=rect((104,112),40)
        def danger(point):
            x,y,w,h=rect(point,5)
            return overlaps((x-4,y-4,w+8,h+8),body)
        driver.navigate((136,80))
        original=driver.path[:]
        self.assertTrue(any(danger(point) for point in original))
        driver.route['contact_cells']=(0x14B,)
        driver.target=None
        driver.navigate((136,80))
        self.assertFalse(any(danger(point) for point in driver.path))
        self.assertEqual(driver.path[-1],(136,80))
        self.ram[0x61C]=0
        driver.target=None
        driver.navigate((136,80))
        self.assertEqual(driver.path,original)

    def test_final_dungeon_turret_is_not_a_melee_target(self):
        driver = self.loop_driver([0x139])
        driver.route.update(index=10)
        driver.route['outbound'][0]['from']=0x15B
        self.ram[0xB9],self.ram[0xA8]=0x5B,1
        self.ram[0x600],self.ram[0x613],self.ram[0x611]=45,88,56
        self.ram[0x630],self.ram[0x648]=80,18
        self.ram[0x643],self.ram[0x641]=168,112
        calls=[]
        def navigate(target,attack=False):
            calls.append((target,attack))
            return 7
        driver.navigate=navigate
        self.assertEqual(driver.drive(0x0C,False),7)
        self.assertEqual(calls[-1],([168,112],True))

    def test_combat_boundary_does_not_cache_a_closed_exit(self):
        driver=self.driver()
        driver.route.update(index=10)
        self.ram[0xB9]=0x5B
        driver.navigate([8,80],attack=True)
        self.assertEqual(driver.path[-1],(24,80))
        driver.navigate([8,80])
        self.assertEqual(driver.path[-1],(8,80))

    def test_late_retreat_before_hero_invulnerability_expires(self):
        driver = self.loop_driver([0x139])
        driver.route.update(index=10, late_retreat=True, late_retreat_window=8)
        driver.route['outbound'][0]['from']=0x13C
        self.ram[0xB9]=0x3C
        self.ram[0x600],self.ram[0x618]=96,24
        self.ram[0x613],self.ram[0x611]=112,80
        self.ram[0x605],self.ram[0x305]=20,8
        driver.evade=lambda threats: 9
        self.assertEqual(driver.drive(0x0C,False),9)

    def test_caster_room_retreat_uses_matching_flashing_enemy(self):
        driver = self.loop_driver([0x139])
        driver.route.update(index=10, caster_room_retreat=True)
        driver.route['outbound'][0]['from']=0x14A
        self.ram[0xB9]=0x4A
        self.ram[0x600],self.ram[0x618]=86,18
        self.ram[0x613],self.ram[0x611]=112,80
        self.ram[0x605],self.ram[0x305]=20,8
        driver.evade=lambda threats: 9 if threats==[(112,80)] else 0
        self.assertEqual(driver.drive(0x0C,False),9)


    def test_unplaced_drainer_does_not_override_real_route_target(self):
        driver = self.loop_driver([0x139])
        driver.route.update(index=10, live_targets=True)
        self.ram[0x600],self.ram[0x618],self.ram[0xA8] = 82,8,1
        calls=[]
        def navigate(target,attack=False):
            calls.append((target,attack))
            return 7
        driver.navigate=navigate
        self.assertEqual(driver.drive(0x0C,False),7)
        self.assertEqual(calls,[([128,8],False)])

    def test_planned_return_to_previous_room_is_not_a_retreat(self):
        driver = self.loop_driver([0x139, 0x138, 0x128])
        self.arrive(driver, 0x139)
        self.arrive(driver, 0x138)
        self.assertEqual(driver.edge, 2)
        self.assertFalse(any('retreated_to' in event for event in driver.events
                             if isinstance(event, dict)))

    def test_unplanned_backtrack_retries_previous_edge(self):
        driver = self.loop_driver([0x139, 0x129])
        self.arrive(driver, 0x139)
        self.arrive(driver, 0x138)
        self.assertEqual(driver.edge, 0)
        self.assertIn({'retreated_to': 0x138}, driver.events)

    def test_room_entry_records_resources_once_per_crossing(self):
        driver = self.loop_driver([0x139, 0x129])
        self.ram[0x318],self.ram[0xDB],self.ram[0xE8],self.ram[0xBF] = 86,8,0,1
        self.arrive(driver, 0x139)
        entry = dict(driver.visits[-1])
        self.assertEqual((entry['hp'],entry['mp'],entry['potion'],entry['curse']), (86,8,0,1))
        self.ram[0x318] = 78
        self.arrive(driver, 0x139)
        self.assertEqual(driver.visits[-1], entry)

    def test_grab_release_retreats_before_using_sword(self):
        driver = self.driver()
        driver.route = {'index': 5, 'outbound': [
            {'from': 0x125, 'to': 0x115, 'target': [128, 8]}]}
        driver.stage = 'outbound'
        self.ram[0x301] = 12
        self.ram[0x600] = 91
        self.ram[0x618] = 18
        self.ram[0x613] = 88
        self.ram[0x611] = 88
        driver.drive(0x0C, False)
        self.ram[0x301] = 1
        pad = driver.drive(0x0C, False)
        self.assertEqual(pad, 1 << driver.buttons['up'])
        self.assertFalse(pad & (1 << driver.buttons['button2']))

    def terrain(self, x, y, high):
        offset = ((y & 248) << 3) + ((x >> 2) & 62) + 1
        self.ram[0x1600 + offset] = high

    def test_escape_chooses_reachable_side_when_wall_blocks_retreat(self):
        driver = self.driver()
        for x in range(0, 256, 8):
            self.terrain(x, 64, 0x80)
        pad = driver.evade([(88, 88)])
        self.assertIn(pad, (driver.pad('left'), driver.pad('right')))
        self.assertTrue(driver.path)
        self.assertIsNone(driver.breaking)

    def test_escape_replans_between_grid_nodes_instead_of_following_old_target(self):
        driver = self.driver()
        self.ram[0x313] = 89
        driver.target = (96,80)
        driver.path = [(96,80)]
        pad = driver.evade([(120,80)])
        self.assertTrue(pad)
        self.assertNotEqual(pad, driver.pad('right'))
        self.assertTrue(driver.path)
        self.assertNotEqual(driver.path[-1], (96,80))

    def test_consumed_antidote_does_not_reopen_inventory_for_missing_item(self):
        driver = self.driver()
        driver.item = 2
        self.ram[0xBF] = self.ram[0xE2] = 1
        self.assertEqual(driver.desired_item(), 2)
        self.ram[0xBF] = self.ram[0xE2] = 0
        self.assertEqual(driver.desired_item(), 0)

    def test_empty_magic_reserve_fights_instead_of_repeated_failed_casts(self):
        driver = self.driver()
        driver.route = {'index': 9, 'outbound': [
            {'from': 0x125, 'to': 0x115, 'target': [128,8]}],
            'puzzles': {str(0x125): {'target': [88,80]}}}
        driver.stage = 'outbound'
        self.ram[0xDB] = 0
        self.ram[0xDF] = 1
        self.ram[0xA8] = self.ram[0x301] = 1
        self.ram[0x30A] = 3
        self.ram[0x600] = 32
        self.ram[0x603] = 3
        self.ram[0x618] = 6
        self.ram[0x613] = 96
        self.ram[0x611] = 80
        self.assertEqual(driver.drive(0x0C,False), driver.pad('button2'))
        self.assertEqual(driver.item, 1)

    def test_curse_enemy_can_be_defeated_in_melee_when_magic_is_empty(self):
        driver = self.driver()
        driver.route = {'index': 10, 'outbound': [
            {'from': 0x125, 'to': 0x115, 'target': [128,8]}]}
        driver.stage = 'outbound'
        self.ram[0xDB] = 0
        self.ram[0xDF] = 1
        self.ram[0xA8] = self.ram[0x301] = 1
        self.ram[0x30A] = 3
        self.ram[0x600] = 83
        self.ram[0x603] = 3
        self.ram[0x618] = 18
        self.ram[0x613] = 96
        self.ram[0x611] = 80
        self.assertEqual(driver.drive(0x0C,False), driver.pad('button2'))

    def test_dungeon10_caster_is_hit_at_safe_reach_then_evaded(self):
        driver = self.driver()
        driver.route = {'index':10,'outbound':[
            {'from':0x125,'to':0x115,'target':[128,8]}]}
        driver.stage = 'outbound'
        self.ram[0xDB],self.ram[0x318],self.ram[0xDF] = 8,40,1
        self.ram[0xA8] = self.ram[0x301] = 1
        self.ram[0x30A] = 3
        self.ram[0x600],self.ram[0x618] = 83,18
        self.ram[0x613],self.ram[0x611] = 108,80
        self.ram[0x61B] = self.ram[0x61C] = 5
        self.assertEqual(driver.drive(0x0C,False),driver.pad('button2'))
        self.assertEqual(driver.item,1)
        self.ram[0x605] = 8
        pad = driver.drive(0x0C,False)
        self.assertTrue(pad)
        self.assertFalse(pad & driver.pad('button2'))

    def test_low_health_magic_drainer_can_be_shot_with_one_cast_remaining(self):
        driver = self.driver()
        driver.route = {'index': 9, 'outbound': [
            {'from': 0x125, 'to': 0x115, 'target': [128,8]}]}
        driver.stage = 'outbound'
        self.ram[0xDB],self.ram[0xDF],self.ram[0x318] = 8,4,72
        self.ram[0xA8] = self.ram[0x301] = 1
        self.ram[0x30A] = 3
        self.ram[0x600],self.ram[0x618] = 78,8
        self.ram[0x613],self.ram[0x611] = 128,80
        self.assertEqual(driver.drive(0x0C,False), driver.pad('button2'))
        self.assertEqual(driver.item, 4)
        self.ram[0x318] = 80
        self.assertFalse(driver.drive(0x0C,False) & driver.pad('button2'))
        self.assertNotEqual(driver.item, 4)

    def test_late_dungeon_keeps_axe_between_approaches(self):
        driver = self.driver()
        driver.route['index'] = 9
        driver.navigate([128,80], attack=True)
        self.assertEqual(driver.desired_item(), 1)
        driver.escaping = True
        self.assertEqual(driver.desired_item(), 0)

    def test_axe_swing_tracks_shield_direction(self):
        driver = self.driver()
        driver.route = {'index': 9, 'outbound': [
            {'from': 0x125, 'to': 0x115, 'target': [128,8]}]}
        driver.stage = 'outbound'
        self.ram[0x301] = 5
        self.ram[0x600] = 93
        self.ram[0x618] = 36
        self.ram[0x613] = 96
        self.ram[0x611] = 80
        self.ram[0x60A] = 2
        self.ram[0x30A] = 0
        self.assertEqual(driver.drive(0x0C,False), driver.pad('right'))

    def test_large_boss_attack_stays_on_axis(self):
        driver = self.driver()
        self.ram[0x613] = 88
        self.ram[0x611] = 48
        self.ram[0x61B] = self.ram[0x61C] = 44
        self.ram[0x30A] = 0
        self.assertEqual(driver.boss_melee(), driver.pad('button2'))
        self.ram[0x613] = 104
        driver.boss_melee()
        self.assertTrue(driver.path)
        self.assertNotEqual(driver.path[-1], (104,48))

    def test_large_boss_recedes_during_hit_invulnerability(self):
        driver = self.driver()
        self.ram[0x613] = 88
        self.ram[0x611] = 112
        self.ram[0x605] = 24
        pad = driver.boss_melee()
        self.assertTrue(pad)
        self.assertFalse(pad & driver.pad('button2'))
        self.assertGreater(abs(driver.path[-1][0]-88)+abs(driver.path[-1][1]-112),32)

    def test_large_boss_does_not_approach_inactive_damage_box(self):
        driver = self.driver()
        self.ram[0x613] = 88
        self.ram[0x611] = 112
        self.ram[0x61B] = 0
        self.ram[0x61C] = 40
        driver.boss_melee()
        self.assertGreater(abs(driver.path[-1][0]-88)+abs(driver.path[-1][1]-112),32)

    def test_patient_boss_probe_waits_for_moving_phase_except_when_invulnerable(self):
        driver = self.driver()
        driver.route['patient_boss'] = True
        self.ram[0x613],self.ram[0x611] = 88,48
        self.ram[0x61B] = self.ram[0x61C] = 44
        self.ram[0x601],self.ram[0x30A] = 8,0
        self.assertFalse(driver.boss_melee() & driver.pad('button2'))
        self.ram[0x305] = 40
        self.assertEqual(driver.boss_melee(), driver.pad('button2'))

    def test_large_boss_finishes_swing_before_repositioning(self):
        driver = self.driver()
        self.ram[0x301] = 5
        self.ram[0x613] = 88
        self.ram[0x611] = 112
        self.ram[0x605] = 24
        self.assertEqual(driver.boss_melee(), 0)

    def test_large_boss_avoids_nearby_projectile_before_swing(self):
        driver = self.driver()
        self.ram[0x613],self.ram[0x611] = 88,48
        self.ram[0x61B] = self.ram[0x61C] = 44
        self.ram[0x30A] = 0
        self.ram[0x780],self.ram[0x783] = 117,2
        self.ram[0x793],self.ram[0x791] = 88,96
        pad = driver.boss_melee()
        self.assertTrue(pad)
        self.assertFalse(pad & driver.pad('button2'))
        self.assertTrue(driver.path)

    def test_short_projectile_distance_preserves_attack_until_threat_is_close(self):
        driver = self.driver()
        driver.route.update(boss_projectile_window=8, boss_projectile_distance=32)
        self.ram[0x613],self.ram[0x611] = 88,48
        self.ram[0x61B] = self.ram[0x61C] = 44
        self.ram[0x30A],self.ram[0x305] = 0,8
        self.ram[0x780],self.ram[0x783] = 117,2
        self.ram[0x793],self.ram[0x791] = 128,80
        self.assertEqual(driver.boss_melee(), driver.pad('button2'))
        self.ram[0x793] = 112
        self.assertFalse(driver.boss_melee() & driver.pad('button2'))
        self.assertTrue(driver.path)

    def test_large_boss_keeps_attacking_during_player_invulnerability(self):
        driver = self.driver()
        self.ram[0x613],self.ram[0x611] = 88,48
        self.ram[0x61B] = self.ram[0x61C] = 44
        self.ram[0x30A] = 0
        self.ram[0x780],self.ram[0x783] = 117,2
        self.ram[0x793],self.ram[0x791] = 88,96
        self.ram[0x305] = 20
        self.assertEqual(driver.boss_melee(), driver.pad('button2'))

    def test_inactive_projectile_does_not_interrupt_safe_swing(self):
        driver = self.driver()
        self.ram[0x613],self.ram[0x611] = 88,48
        self.ram[0x61B] = self.ram[0x61C] = 44
        self.ram[0x30A] = 0
        self.ram[0x780],self.ram[0x783] = 117,0
        self.ram[0x793],self.ram[0x791] = 88,96
        self.assertEqual(driver.boss_melee(), driver.pad('button2'))

    def test_miniboss_flash_triggers_retreat_between_hits(self):
        driver = self.driver()
        driver.route = {'index': 10, 'outbound': [
            {'from': 0x125, 'to': 0x115, 'target': [128,8]}]}
        driver.stage = 'outbound'
        self.ram[0x301] = self.ram[0xA8] = 1
        self.ram[0x600] = 121
        self.ram[0x618] = 20
        self.ram[0x605] = 24
        self.ram[0x613] = 104
        self.ram[0x611] = 80
        pad = driver.drive(0x0C,False)
        self.assertTrue(pad)
        self.assertFalse(pad & driver.pad('button2'))
        self.assertGreater(abs(driver.path[-1][0]-104)+abs(driver.path[-1][1]-80), 16)

    def test_late_cure_waits_until_last_caster_is_dead(self):
        driver = self.driver()
        driver.route = {'index': 10, 'outbound': [
            {'from': 0x125, 'to': 0x115, 'target': [128,8]}]}
        driver.stage = 'outbound'
        self.ram[0xBF] = self.ram[0xE2] = self.ram[0x301] = 1
        self.ram[0x600] = 83
        self.ram[0x618] = 18
        driver.drive(0x0C,False)
        self.assertNotEqual(driver.item, 2)
        self.ram[0x618] = 0
        self.ram[0xDF] = 2
        self.assertEqual(driver.drive(0x0C,False), driver.pad('button2'))

    def test_fire_reaches_partitioned_enemy_below_normal_reserve(self):
        driver = self.driver()
        driver.route = {'index': 6, 'return': [
            {'from': 0x125, 'to': 0x115, 'target': [128,8]}]}
        driver.stage = 'return'
        self.ram[0xDB] = 80
        self.ram[0xA8] = self.ram[0x301] = 1
        self.ram[0x30A] = 3
        self.ram[0xDF] = 4
        self.ram[0x600] = 79
        self.ram[0x603] = 3
        self.ram[0x618] = 10
        self.ram[0x613] = 120
        self.ram[0x611] = 80
        for y in range(0,176,8):
            self.terrain(104,y,0xE0)
        self.assertEqual(driver.drive(0x0C,False), driver.pad('button2'))
        self.assertEqual(driver.item, 4)

    def test_break_cost_uses_collision_probe_not_player_center(self):
        driver = self.driver()
        self.ram[0x1C00 + 4 * 16 + 4] = 0x0B
        for x in (64, 72):
            for y in (64, 72):
                self.terrain(x, y, 0x80)
        driver.navigate([56, 80])
        self.assertEqual(driver.path[0], (88, 88))
        self.assertEqual(driver.path[-1], (56, 80))
        self.assertIsNone(driver.breaking)

    def test_terrain_permission_change_invalidates_cached_path(self):
        driver = self.driver()
        self.ram[0xEC] = 1
        for x in (64, 72):
            for y in range(0, 176, 8):
                self.terrain(x, y, 0x20)
        driver.navigate([56, 80])
        self.assertEqual(driver.path[-1], (56, 80))
        previous_key = driver.path_key
        self.ram[0xEC] = 0
        driver.navigate([56, 80])
        self.assertNotEqual(driver.path_key, previous_key)
        self.assertTrue(not driver.path or driver.path[-1] != (56, 80))

    def test_travel_avoids_enemy_but_melee_can_approach_it(self):
        driver = self.driver()
        self.ram[0x600] = 83
        self.ram[0x603] = 3
        self.ram[0x613] = 104
        self.ram[0x611] = 80
        driver.navigate([136, 80])
        self.assertNotIn((104, 80), driver.path)
        previous_key = driver.path_key
        driver.navigate([104, 80], attack=True)
        self.assertEqual(driver.path, [(96, 80), (104, 80)])
        self.assertNotEqual(driver.path_key, previous_key)

    def test_moving_enemy_invalidates_travel_path(self):
        driver = self.driver()
        self.ram[0x600] = 83
        self.ram[0x603] = 3
        self.ram[0x613] = 104
        self.ram[0x611] = 80
        driver.navigate([136, 80])
        previous_key = driver.path_key
        self.ram[0x611] = 136
        driver.navigate([136, 80])
        self.assertNotEqual(driver.path_key, previous_key)
        self.assertIn((104, 80), driver.path)


class ViewportComparisonTest(unittest.TestCase):
    def test_fixed_dac_conversion(self):
        sms = bytes((82, 85, 255))*49152
        md = bytes((65, 68, 238))*49152
        self.assertEqual(captures.differences(md, sms), [])

    def test_one_wrong_pixel_is_rejected(self):
        sms = bytes((82, 85, 255))*49152
        md = bytearray(bytes((65, 68, 238))*49152)
        md[3] = 0
        self.assertEqual(captures.differences(md, sms), [(1, 0)])

    def test_unknown_dac_levels_are_rejected(self):
        with self.assertRaises(ValueError):
            captures.differences(bytes(49152*3), bytes((1, 0, 0))*49152)

class EmbedRomTest(unittest.TestCase):
    def reject(self, size):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            rom = directory/'input.sms'
            output = directory/'original_rom.inc'
            rom.write_bytes(bytes(size))
            output.write_text('preserve existing verified data')
            with self.assertRaises(ValueError):
                embed_rom.embed(rom, output)
            self.assertEqual(output.read_text(), 'preserve existing verified data')
            self.assertEqual(set(p.name for p in directory.iterdir()),
                             {'input.sms', 'original_rom.inc'})

    def test_truncated_rom(self): self.reject(0x3FFFF)
    def test_headered_rom(self): self.reject(0x40200)
    def test_other_revision(self): self.reject(0x40000)

    def test_missing_rom_preserves_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'original_rom.inc'
            output.write_text('preserve')
            with self.assertRaises(FileNotFoundError):
                embed_rom.embed(Path(directory)/'missing.sms', output)
            self.assertEqual(output.read_text(), 'preserve')

if __name__ == '__main__': unittest.main()
