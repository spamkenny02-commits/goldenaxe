"""Prove an intermediate DMA changes VRAM; final alternating parity is insufficient."""
import argparse
import contextlib
import gzip
import ctypes as c
import hashlib
import io
import json
import re
from pathlib import Path
from run_core import run
from md_z80_video_fixture import expected_pattern

ROOT=Path(__file__).resolve().parents[1]


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variant',default='video-dma-snapshot-bare');parser.add_argument('--archive',default='md-z80-dma-window-v0203');args=parser.parse_args()
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',args.variant) and re.fullmatch(r'[a-z0-9-]+',args.archive)
    suffix='' if args.variant=='video-dma-snapshot-bare' else '-'+args.variant
    folder=ROOT/('validation/md-z80-dma-intermediate'+suffix);folder.mkdir(exist_ok=True)
    kernel_root=ROOT/('validation/md-z80-psg-'+args.variant)
    archive=ROOT/'analysis'/args.archive;manifest=None
    def artifact(path):
        nonlocal manifest
        if path.exists():return path.read_bytes()
        if manifest is None:manifest=json.loads((archive/'manifest.json').read_bytes())
        name=path.relative_to(ROOT).as_posix()
        if name in manifest['files']:
            raw=(archive/name).read_bytes();assert sha(raw)==manifest['files'][name];return raw
        item=manifest['compressed'][name];encoded=(archive/item['stored']).read_bytes();assert sha(encoded)==item['stored_sha256']
        raw=gzip.decompress(encoded);assert sha(raw)==item['raw_sha256'] and len(raw)==item['raw_bytes'];return raw
    report=json.loads(artifact(ROOT/('analysis/md_z80_psg_'+args.variant.replace('-','_')+'_report.json')))
    original_rom=kernel_root/'out/release/rom.bin';raw=artifact(original_rom);assert sha(raw)==report['kernel_sha256']
    rom=original_rom
    if not rom.exists():rom=folder/'input-kernel.bin';rom.write_bytes(raw)
    symbols={m[2]:int(m[1],16) for line in artifact(kernel_root/'out/release/symbol.txt').decode().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_z80_psg_io_libretro.dll'
    dll=c.CDLL(str(core));dll.gaw_io_reset.argtypes=[c.c_uint];dll.gaw_io_size.restype=dll.gaw_io_errors.restype=c.c_uint;dll.gaw_io_data.restype=c.POINTER(c.c_uint)
    dll.retro_serialize_size.restype=c.c_size_t;dll.retro_serialize.argtypes=[c.c_void_p,c.c_size_t];dll.retro_serialize.restype=c.c_bool
    results=[]
    for rr in report['results']:
        region=rr['region'];period=(262 if region=='ntsc' else 313)*3420
        captured={};events=[];dll.gaw_io_reset(0)
        def read(ram,name):return int.from_bytes(bytes(ram[(((symbols[name]&65535)+i)&65535)^1] for i in range(4)),'big')
        def observe(frame,ram):
            size=dll.gaw_io_size();assert not dll.gaw_io_errors();ptr=dll.gaw_io_data()
            events.extend([[int(ptr[n*4]),(frame-1)*period+int(ptr[n*4+1]),int(ptr[n*4+2]),int(ptr[n*4+3])] for n in range(size)]);dll.gaw_io_reset(1)
            updates=read(ram,'gaw_video_updates')
            if updates>1 and not updates&1:
                state=c.create_string_buffer(dll.retro_serialize_size());assert dll.retro_serialize(state,len(state))
                base=16+0x10000+0x2000+5+16+0x400
                vram=state.raw[base:base+65536];regs=state.raw[base+0x10100:base+0x10120]
                actual=bytes(vram[(32+n)^1] for n in range(32))
                assert actual==expected_pattern(updates) and actual!=expected_pattern(1)
                assert regs[1]&0x10 and regs[19:21]==b'\0\0'
                (folder/(region+'-vram.bin')).write_bytes(vram);(folder/(region+'-regs.bin')).write_bytes(regs)
                captured.update(frame=frame,updates=updates,ram_sha256=sha(bytes(ram)),vram_sha256=sha(vram),registers_sha256=sha(regs))
        with contextlib.redirect_stdout(io.StringIO()):run(rom,2000,folder/region,set(),[],skip_intro=False,ram_observer=observe,core=core,core_options={'genesis_plus_gx_region_detect':region},stop_when=lambda:bool(captured))
        assert captured
        original_raw=artifact(kernel_root/(region+'-events.json'));assert sha(original_raw)==rr['events_sha256']
        original=json.loads(original_raw)['events'];assert events and events==original[:len(events)]
        prefix=json.dumps(events,separators=(',',':')).encode();(folder/(region+'-prefix-events.json')).write_bytes(prefix)
        plain={};target=captured['frame']
        def plain_observe(frame,ram):
            if frame==target:plain.update(frame=frame,updates=read(ram,'gaw_video_updates'),ram_sha256=sha(bytes(ram)))
        with contextlib.redirect_stdout(io.StringIO()):run(rom,target,folder/(region+'-plain'),{target},[],skip_intro=False,ram_observer=plain_observe,core_options={'genesis_plus_gx_region_detect':region})
        assert plain=={k:captured[k] for k in plain}
        path=folder/(region+'-plain');assert sha((path/f'vram_{target:05d}.bin').read_bytes())==captured['vram_sha256']
        results.append(dict(region=region,**captured,prefix_events=len(events),prefix_sha256=sha(prefix),original_events_sha256=rr['events_sha256'],image_sha256=sha((path/f'frame_{target:05d}.png').read_bytes())))
        print(results[-1],flush=True)
    (ROOT/('analysis/md_z80_dma_intermediate'+('' if not suffix else '_'+args.variant.replace('-','_'))+'_report.json')).write_text(json.dumps(dict(kernel_sha256=report['kernel_sha256'],results=results,limits=['A readonly intermediate snapshot after an even-numbered upload proves tile data differs from initialization and equals the requested DMA pattern. DMA enable/zero remaining length checked; observed IO trace is exactly the original full-run prefix.', 'Same frame RAM/VRAM agree with the plain core. This is a targeted positive transfer witness, not every-job payload or renderer/frame-deadline proof.']),indent=2)+'\n')


if __name__=='__main__':main()
