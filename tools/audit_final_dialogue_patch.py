"""Bind the final acknowledgement change to its exact baseline and live evidence."""
import hashlib,json
from actor_reference import ROOT

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    md=ROOT/'gaw-megadrive.bin';raw=md.read_bytes();digest=sha(md)
    assert len(raw)==524288
    assert raw==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(raw[n:n+2],'big') for n in range(512,len(raw),2))&65535
    assert int.from_bytes(raw[0x18e:0x190],'big')==checksum
    old=json.loads((ROOT/'versions/v0063-62366fff/dungeon_bitmaps_patch_audit.json').read_bytes())
    base=ROOT/'analysis/dialogue-waits-baseline-v0063/main.c'
    assert sha(base)==old['source_files']['megadrive/src/main.c']
    text=(ROOT/'megadrive/src/main.c').read_text()
    a=text.index('/* 7447..7451 / 627A..6282:');b=text.index('static void wait_dialog_continue(void)',a)
    restored=(text[:a]+text[b:]).replace('render_dialogue_text(source,overlay);wait_dialog_end();','render_dialogue_text(source,overlay);wait_dialog_continue();')
    assert restored==base.read_text()
    source=(ROOT/'input/original.sms').read_bytes()
    assert source[0x7444:0x7452]==bytes.fromhex('cd9b77cd950b3a21c0e63f28f6c9')
    assert source[0x6277:0x6287]==bytes.fromhex('cd0c05cd950b3a21c0e63f28f6c3e21d')
    evidence=[]
    for name in ['final_dialogue_report.json','house_dialogue_report.json','timing_report.json','timing-pal_report.json']:
        path=ROOT/'validation'/name;d=json.loads(path.read_bytes());assert d['md_sha256']==digest
        if name=='final_dialogue_report.json':
            assert len(d['cases'])==12 and not d['ram_injections']
            assert all(x['stable_final_marker_exact'] and x['held_confirmation_does_not_dismiss_final'] and x['stable_final_bitmap_bytes_exact']==1040 for x in d['cases'])
        elif name=='house_dialogue_report.json':
            assert len(d['cases'])==6 and d['natural_walk_conversation_and_restore_verified']
        else:
            assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences'])
            assert d['enemy']['differing_motion_counter_frames']==0
        evidence.append(dict(file=name,sha256=sha(path)))
    prior=json.loads((ROOT/'versions/v0060-b2742e83/item_rewards_report.json').read_bytes())['source_copies']
    for name,h in prior.items():
        if name!='main.c':assert sha(ROOT/'megadrive/src'/name)==h
    assert sha(ROOT/'megadrive/src/dungeon_animation_data.c')==old['source_files']['megadrive/src/dungeon_animation_data.c']
    files=['megadrive/src/main.c','tools/validate_final_dialogue.py','tools/validate_house_dialogue.py','tools/audit_final_dialogue_patch.py','analysis/dialogue-waits-baseline-v0063/main.c']
    report=dict(md_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest(),checksum=hex(checksum),rom_aliases_verified=True,exact_previous_main_restored_by_removing_final_wait=True,prior_production_assets_unchanged=True,source_files={p:sha(ROOT/p) for p in files},reports=evidence,full_game_ported=False,limits=['This patch fixes final acknowledgement inputs and marker only; inter-page clock/reset/rendering still differs.','Initial room activation remains early by 33 NTSC / 31 PAL frames in the natural opening test.','Village restoration uses controlled positions in six cases plus one natural walking route; timing is not proven exact.','All item abilities, quests, enemy/boss behavior and ending remain incomplete or unverified.'])
    (ROOT/'validation/final_dialogue_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Final dialogue patch audit passed:',digest)

if __name__=='__main__':main()
