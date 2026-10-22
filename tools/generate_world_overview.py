"""Export original world overview colors, marker frames and packed marker tiles."""
import hashlib,json
from pathlib import Path
from ram_plane_loading_cost import ram_plane_cost
ROOT=Path(__file__).resolve().parents[1]

def main():
    rom=(ROOT/'input/original.sms').read_bytes();end=ram_plane_cost(rom,0x17d71,0x3f40,4)['source_end']
    arrays=dict(overview_colors=rom[0x84de:0x855e],overview_palette=rom[0x83e8:0x83ec],overview_hero_frame=rom[0x8445:0x8449],overview_treasure_frame=rom[0x8449:0x844d],overview_markers_rle=rom[0x17d71:end])
    lines=['/* Original SMS overview resources: bank2 83E8/8445/84DE, bank5 BD71. */']
    for name,data in arrays.items():lines+=['static const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%b for b in data[n:n+16])+',' for n in range(0,len(data),16)]+['};']
    raw=('\r\n'.join(lines)+'\r\n').encode();path=ROOT/'megadrive/src/world_overview_assets.inc'
    if not path.exists() or path.read_bytes()!=raw:path.write_bytes(raw)
    report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),marker_rle_start=0x17d71,marker_rle_end=end,arrays={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in arrays.items()},captured_states_used=False)
    (ROOT/'analysis/world_overview_assets.json').write_text(json.dumps(report,indent=2)+'\n');print('Original overview resources exported')

if __name__=='__main__':main()
