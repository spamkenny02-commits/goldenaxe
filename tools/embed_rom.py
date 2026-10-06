#!/usr/bin/env python3
"""Generate the ignored compatibility input from the exact reference ROM."""
import argparse
import hashlib
from pathlib import Path
import tempfile

REFERENCE_SHA256 = "852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9"

def embed(rom_path, output):
    data = Path(rom_path).read_bytes()
    if len(data) != 0x40000:
        raise ValueError("expected exactly 262144 bytes (unheadered SMS ROM)")
    digest = hashlib.sha256(data).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError(f"unsupported ROM SHA-256: {digest}; expected {REFERENCE_SHA256}")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(", ".join(f"0x{b:02X}" for b in data[i:i+16]) + ",\n"
                   for i in range(0, len(data), 16))
    with tempfile.NamedTemporaryFile(mode="w", dir=output.parent, delete=False) as f:
        temporary = Path(f.name)
        f.write(text)
    try:
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return digest

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", type=Path)
    p.add_argument("--output", type=Path,
                   default=Path(__file__).resolve().parents[1]/"src/original_rom.inc")
    a = p.parse_args()
    try:
        digest = embed(a.rom, a.output)
    except (OSError, ValueError) as exc:
        p.exit(2, f"{exc}\n")
    print(f"Generated {a.output} from verified ROM {digest}")

if __name__ == "__main__":
    main()
