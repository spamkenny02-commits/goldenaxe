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
