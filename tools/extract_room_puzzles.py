"""Extract stationary room transformation/reward scripts from original Z80."""
import hashlib,json
from extract_contact_scripts import ROOT,extract as contacts
from extract_room_clear import extract,extract_rewards,extract_completions,extract_shutters
TARGETS={0x5e29:'redraw',0x5dee:'redraw_remote_flag',0x5e01:'redraw_key',0x5e0d:'redraw_passage',0x5e45:'open_blocked_passages'}
KINDS={0x5e29:1,0x5dee:2,0x5e01:3,0x5e0d:4,0x5e45:5}
def records(r):
    result=contacts(r,targets=TARGETS)
    assert len(result)==31 and len({x['room'] for x in result})==31
    earlier=extract(r)+extract_rewards(r)+extract_completions(r)+extract_shutters(r)+contacts(r)
    for x in result:
        x['stage']=int(any(y['room']==x['room'] and y['call_site']<x['call_site'] for y in earlier))
        x['native_kind']=KINDS[x['target']]
    assert {x['room'] for x in result if x['stage']}=={0x129,0x16c,0x1eb}
    return result

def main():
    original=(ROOT/'input/original.sms').read_bytes();items=records(original)
    lines=['/* Original stationary room transforms: room/kind/coordinate/argument/stage. */','static const u16 world_room_puzzles[31][5] = {']
    for x in items:lines.append('    {'+','.join(str(v) for v in [x['room'],x['native_kind'],x['coordinate'],x['explicit_registers'].get('e',0),x['stage']])+'},')
    lines.append('};');(ROOT/'megadrive/src/room_puzzles.inc').write_text('\n'.join(lines)+'\n')
    (ROOT/'analysis/room_puzzles_reference.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(original).hexdigest(),records=items,item_reward_scripts_5d59_ported=False),indent=2)+'\n')
    print('31 stationary transformation/reward scripts extracted; 10 item-message scripts remain separate.')
if __name__=='__main__':main()
