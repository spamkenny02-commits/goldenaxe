"""Add read-only key-redraw PC markers to the existing research timing hook."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT.parents[1]/'work/genesis-plus-gx/core/z80/z80.c'
source=path.read_text()
assert 'GAW_RESEARCH_TIMING' in source,'Install the base instrument_timing hook first.'
if 'pc==0x5e90' not in source:
    markers=[0x5c4e,0x5e90,0x5e93,0x5e96,0x1de2,0x1de5,0x1de8,0x1deb,0x1e1f,
             0x1976,0x2279,0x1e4e,0x229c,0x0b95,0x0bb3,0x22bf]
    condition=' || '.join('pc==0x%04x'%pc for pc in markers)
    source=source.replace('if(pc==0x24c5','if('+condition+' || pc==0x24c5')
    path.write_text(source)
print(path)
