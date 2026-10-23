"""Export original world overview colors, marker frames and packed marker tiles."""
import hashlib,json
from pathlib import Path
from ram_plane_loading_cost import ram_plane_cost
from world_overview_cost import room_decode_cost,projection_cost,restore_cells_cost
ROOT=Path(__file__).resolve().parents[1]

def main():
    rom=(ROOT/'input/original.sms').read_bytes();end=ram_plane_cost(rom,0x17d71,0x3f40,4)['source_end']
    arrays=dict(overview_colors=rom[0x84de:0x855e],overview_palette=rom[0x83e8:0x83ec],overview_hero_frame=rom[0x8445:0x8449],overview_treasure_frame=rom[0x8449:0x844d],overview_markers_rle=rom[0x17d71:end])
    lines=['/* Original SMS overview resources: bank2 83E8/8445/84DE, bank5 BD71. */']
    for name,data in arrays.items():lines+=['static const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%b for b in data[n:n+16])+',' for n in range(0,len(data),16)]+['};']
    costs=[0]*1024
    for room in range(16,256):
        if room&15==15:continue
        for ice in [0,1]:
            for flag in [0,1]:costs[room*4+ice*2+flag]=room_decode_cost(rom,room,flag,ice)[0]
    assert max(costs)<65536
    pixel=[17+projection_cost(bytes([1])*160,arrays['overview_colors'],0,col) for col in range(8)]
    lines+=['static const u16 overview_decode_tstates[] = {']+['    '+','.join(map(str,costs[n:n+16]))+',' for n in range(0,len(costs),16)]+['};']
    lines+=['static const u16 overview_pixel_tstates[] = {'+','.join(map(str,pixel))+'};']
    lines+=['static const u16 overview_restore_tstates='+str(restore_cells_cost())+';']
    raw=('\r\n'.join(lines)+'\r\n').encode();path=ROOT/'megadrive/src/world_overview_assets.inc'
    if not path.exists() or path.read_bytes()!=raw:path.write_bytes(raw)
    report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),marker_rle_start=0x17d71,marker_rle_end=end,arrays={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in arrays.items()},captured_states_used=False,room_decode_cost_entries=1024,room_decode_cost_max=max(costs),projection_pixel_costs=pixel,source_instructions_used=True,restore_cells_tstates=restore_cells_cost())
    (ROOT/'analysis/world_overview_assets.json').write_text(json.dumps(report,indent=2)+'\n');print('Original overview resources exported')

if __name__=='__main__':main()
