import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'embed_rom', Path(__file__).resolve().parents[1]/'tools/embed_rom.py')
embed_rom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(embed_rom)

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
