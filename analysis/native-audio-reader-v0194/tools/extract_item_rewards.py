"""Original stationary item rewards and 6317 acquisition resources."""
import hashlib,json
from extract_contact_scripts import ROOT,extract
from extract_title import rle_planes

HANDLERS={0x10:(0x5d99,0xe3,1,7),0x12:(0x5da0,0xea,1,14),0x1d:(0x5dc3,0xe1,2,5),0x57:(0x5da7,0xee,1,18),0x9b:(0x5dae,0xeb,1,15),0xa2:(0x5db5,0xec,1,16),0xa9:(0x5dbc,0xef,1,19),0xb6:(0x5dcc,0xe1,1,4),0xd5:(0x5dda,0xf0,1,20),0xf4:(0x5de1,0xed,1,17)}

def records(r):
    items=extract(r,{0x5d59:'stationary_item_reward'})
    assert len(items)==10 and {x['room']&255 for x in items}==set(HANDLERS)
    for x in items:
        room=x['room']&255;p,slot,value,item=HANDLERS[room]
        if room==0x1d:assert r[p:p+7]==bytes.fromhex('3e0232e1c03e05')
        elif room==0xb6:assert r[p:p+12]==bytes.fromhex('3ae1c0b720193c32e1c03e04')
        else:assert r[p:p+5]==bytes([0x21,slot,0xc0,0x3e,item])
        x.update(handler=p,inventory_offset=slot-0xe0,value=value,item=item,requires_weapon_absent=room==0xb6)
    return items

def main():
    r=(ROOT/'input/original.sms').read_bytes();items=records(r)
    lines=['/* Source 5D59: room/coordinate/inventory offset/value/item/weapon guard. */','static const u16 world_item_rewards[10][6] = {']
    labels=bytearray();indices=[]
    for x in items:
        lines.append('    {'+','.join(str(v) for v in [x['room'],x['coordinate'],x['inventory_offset'],x['value'],x['item'],int(x['requires_weapon_absent'])])+'},')
        pointer=int.from_bytes(r[0x63b3+x['item']*2:0x63b5+x['item']*2],'little');p=0xc000+(pointer&0x3fff);end=r.index(0,p)+1
        x['label_pointer']=pointer;x['label_hex']=r[p:end].hex();indices.extend(len(labels).to_bytes(2,'little'));labels.extend(r[p:end])
    lines.append('};');(ROOT/'megadrive/src/item_rewards.inc').write_text('\n'.join(lines)+'\n')
    end=0x12241+1+r[0x12241]*24;pattern_end=0x3e00+r[0x12241]*32;assert r[0x12241]==6
    descriptor=0x304b3;count=r[descriptor]&127;assert count==8
    assets={'reward_labels':labels,'reward_label_index':bytes(indices),'reward_hero_bitmap':r[0x12241:end],'reward_hero_frame':bytes([count])+r[descriptor+3:descriptor+3+count*3]}
    c=['#include <genesis.h>']
    for name,data in assets.items():c+=['const u8 '+name+'[] = {']+['    '+','.join('0x%02x'%b for b in data[p:p+16])+',' for p in range(0,len(data),16)]+['};']
    (ROOT/'megadrive/src/item_rewards_data.c').write_text('\n'.join(c)+'\n')
    (ROOT/'analysis/item_rewards_reference.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(r).hexdigest(),records=items,hero_bitmap_start=0x12241,hero_bitmap_end=end,hero_pattern_end=pattern_end,hero_descriptor=descriptor,source_message_routine='6317..63B2',minimum_wait_frames=180),indent=2)+'\n')
    print('10 source item rewards extracted; hero pattern end',hex(pattern_end))

if __name__=='__main__':main()

