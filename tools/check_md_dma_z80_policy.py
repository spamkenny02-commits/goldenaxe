"""Pin the current SDK and playable DMA bus policy without executing DMA."""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    folder=ROOT/'validation/md-z80-video-policy';folder.mkdir(exist_ok=True)
    rom=(ROOT/'gaw-megadrive.bin').read_bytes()
    assert sha(rom)=='7660a4b5949d0f3362c4795ed5eb238f86c289708b51d1dda6eec669b4d3ecb7'
    code={0x26e66:'207c00a11100',0x26e76:'30bc0100',0x26e82:'32af000e',0x26e86:'30bc0000'}
    for address,expected in code.items():assert rom[address:address+len(expected)//2].hex()==expected
    # Bind A1 to VDP control, then A0 to BUSREQ. The code path writes BUSREQ
    # before the second DMA command word and clears it immediately afterwards.
    assert rom[0x26e5c:0x26e62].hex()=='227c00c00004'
    (folder/'v0203-dma-fast-window.bin').write_bytes(rom[0x26e5c:0x26e90])
    sources={}
    for relative,label in [('sgdk/inc/config.h','sgdk-config.h'),('sgdk/src/dma.c','sgdk-dma.c'),
                           ('genesis-plus-gx/core/memz80.c','core-memz80.c'),('genesis-plus-gx/core/vdp_ctrl.c','core-vdp_ctrl.c')]:
        raw=(ROOT.parents[1]/'work'/relative).read_bytes();(folder/label).write_bytes(raw);sources[label]=sha(raw)
    config=(folder/'sgdk-config.h').read_text()
    assert re.search(r'^#define\s+HALT_Z80_ON_DMA\s+1\s*$',config,re.M)
    report=dict(playable_sha256=sha(rom),source_snapshots=sources,
        dma_fast_vdp_control_binding=hex(0x26e5c),dma_fast_busreq_binding=hex(0x26e66),
        dma_fast_bus_acquire=hex(0x26e76),dma_fast_trigger=hex(0x26e82),dma_fast_bus_release=hex(0x26e86),
        code_hex={hex(k):v for k,v in code.items()},sdk_halt_z80_on_dma=1,
        dma_runtime_tested=False,limits=[
            'Static proof for the identified VRAM DMA_doDmaFast path in the unchanged v0203 binary, plus current SDK source configuration. Other DMA call paths and actual DMA timing still need dedicated runtime tests.',
            'The source snapshots also show the emulator models Z80 waiting when DMA occupies the68k bus. No emulator modification or hardware measurement is made here.',
            'The experimental PSG clock requires sample gaps under17100master ticks and grant-safe bounded BUSREQ. Existing playable DMA calls do not establish that experimental contract; integration needs scheduling/coordination proof.'])
    (ROOT/'analysis/md_dma_z80_policy_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('v0203 DMA fast path BUSREQ/trigger/release and SDK HALT_Z80_ON_DMA=1 verified; static evidence only')


if __name__=='__main__':main()
