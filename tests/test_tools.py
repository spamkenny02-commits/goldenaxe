import importlib.util
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
