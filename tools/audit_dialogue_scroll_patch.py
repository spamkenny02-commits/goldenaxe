"""Bind staged dialogue bitmap rendering, marker transfer and free-night timing."""
import hashlib,json,re
from actor_reference import ROOT

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert len(data)==524288 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
    checksum=sum(int.from_bytes(data[n:n+2],'big') for n in range(512,len(data),2))&65535
    assert int.from_bytes(data[0x18e:0x190],'big')==checksum
    base=ROOT/'analysis/dialogue-scroll-baseline-v0064/main.c'
    old=json.loads((ROOT/'versions/v0064-065f1446/final_dialogue_patch_audit.json').read_bytes())
    assert sha(base)==old['source_files']['megadrive/src/main.c']
    s=(ROOT/'megadrive/src/main.c').read_text();original=base.read_text()
    a=s.index('static void upload_dialog_bitmap(void)');b=s.index('static void draw_dialog_glyph',a)
    oa=original.index('static void upload_dialog_bitmap(void)');ob=original.index('static void draw_dialog_glyph',oa)
    s=s[:a]+original[oa:ob]+s[b:]
    a=s.index('/* 0805 writes only');b=s.index('/* Intermediate pages',a);s=s[:a]+s[b:]
    s=s.replace('set_dialog_marker((blink++&8)?0xfc:0xfd);','sms_vram[0x3cde]=(blink++&8)?0xfc:0xfd;\n        draw_map();').replace('set_dialog_marker(0xfc);','sms_vram[0x3cde]=0xfc;\n    draw_map();')
    s=s.replace('u16 n,out=0,x=0,y=0,line=0;','u16 n,p,out=0,x=0,y=0,line=0;')
    old_shift='''                for(n=0;n<26;n++)
                {
                    for(p=0;p<30;p++) scratch[n*40+p]=scratch[n*40+p+10];
                    memset(scratch+n*40+30,0,10);
                }'''
    s=s.replace('                scroll_dialog_bitmap();',old_shift,1)
    s=s.replace('                scroll_dialog_bitmap();','                /* $068A: four scroll increments (2,3,3,2) totaling ten pixels. */\n'+old_shift,1)
    assert s==original
    prior=json.loads((ROOT/'versions/v0060-b2742e83/item_rewards_report.json').read_bytes())['source_copies']
    for name,h in prior.items():
        if name not in ['main.c','healer.inc']:assert sha(ROOT/'megadrive/src'/name)==h
    healer_base=ROOT/'analysis/dialogue-scroll-baseline-v0064/healer.inc'
    assert sha(healer_base)==prior['healer.inc']
    h=(ROOT/'megadrive/src/healer.inc').read_text()
    h=h.replace('        u32 fade_started=vtimer,night_started;\n','')
    a=h.index('        fade_world_palette(black,FALSE);');b=h.index('        for(n=0;n<60;',a)
    h=h[:a]+'        fade_world_palette(black,FALSE);VDP_setEnable(FALSE);\n'+h[b:]
    a=h.index('        /* 60 IRQs plus');b=h.index('        VDP_setEnable(TRUE);',a);h=h[:a]+h[b:]
    assert h==healer_base.read_text()
    table=(ROOT/'megadrive/src/dialogue_packed_pixels.inc').read_text()
    values=[int(x,16) for x in re.findall(r'0x([0-9a-f]{8})UL',table)];assert len(values)==256
    for bitmap,word in enumerate(values):
        for x in range(8):assert (word>>(28-x*4))&15==1+2*((bitmap>>(7-x))&1)
    source=(ROOT/'input/original.sms').read_bytes();assert source[0x6b8:0x6bd]==bytes([2,3,3,2,0])
    names=['dialogue_scroll_report.json','final_dialogue_report.json','house_dialogue_report.json','all_merchants_report.json','save_report.json','healer_report.json','healer-pal_report.json','timing_report.json','timing-pal_report.json']
    reports=[]
    for name in names:
        p=ROOT/'validation'/name;d=json.loads(p.read_bytes());assert d['md_sha256']==digest,name
        if name=='dialogue_scroll_report.json':assert len(d['cases'])==2 and all(x['first_presentation_frames_exact'] and x['all_pattern_pixel_colors_verified'] for x in d['cases'])
        elif name=='final_dialogue_report.json':assert len(d['cases'])==12 and all(x['stable_final_marker_exact'] and x['held_confirmation_does_not_dismiss_final'] for x in d['cases'])
        elif name=='house_dialogue_report.json':assert len(d['cases'])==6 and d['natural_walk_conversation_and_restore_verified']
        elif name.startswith('healer'):assert len(d['cases'])==5 and all(x['night_display_interval_source_exact'] for x in d['cases'])
        elif name=='all_merchants_report.json':assert len(d['cases'])>=40
        elif name=='save_report.json':assert len(d['cases'])==3 and d['death_continue_saved_checkpoint_verified']
        elif name.startswith('timing'):assert all(x['differing_state_frames']==0 for x in d['natural_input_sequences']) and d['enemy']['differing_motion_counter_frames']==0
        reports.append(dict(file=name,sha256=sha(p)))
    nights=[];source_timing=[]
    for suffix in ['', '-pal']:
        d=json.loads((ROOT/f'validation/healer{suffix}_report.json').read_bytes())
        for case in d['cases']:
            states={};hashes={}
            for tag in ['sms','md']:
                folder=ROOT/f"validation/{tag}-healer-{case['name']}{suffix}"
                assert json.loads((folder/'capture.json').read_bytes())['rom_sha256']==(hashlib.sha256(source).hexdigest() if tag=='sms' else digest)
                flags=bytes((folder/f'vdp_regs_{frame:05}.bin').read_bytes()[1] for frame in range(3680,3881))
                states[tag]=[3680+n for n,v in enumerate(flags) if not v&64];hashes[tag]=hashlib.sha256(flags).hexdigest()
            assert states['sms']==states['md']
            nights.append(dict(region=d['region'],case=case['name'],disabled_frames=states['sms'],vdp_register_sequence_hashes=hashes))
        p=ROOT/f'analysis/dialogue-scroll-baseline-v0064/healer_fade{suffix}_profile.json';d=json.loads(p.read_bytes())
        assert d['source_sha256']==hashlib.sha256(source).hexdigest()
        start=next(x for x in d['events']['sms'] if x['pc']==0x0b12)
        end=next(x for x in d['events']['sms'] if x['pc']==0x0b24 and x['frame']>start['frame'])
        assert start['frame']==3700 and end['frame']==(3718 if suffix else 3719)
        source_timing.append(dict(file=str(p.relative_to(ROOT)),sha256=sha(p),source_fade_start=start,source_display_disable=end))
    paths=['megadrive/src/main.c','megadrive/src/healer.inc','megadrive/src/dialogue_packed_pixels.inc','tools/validate_dialogue_scroll.py','tools/validate_healer.py','tools/profile_healer_fade.py','tools/audit_dialogue_scroll_patch.py','analysis/dialogue-scroll-baseline-v0064/main.c','analysis/dialogue-scroll-baseline-v0064/healer.inc']
    report=dict(md_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest(),checksum=hex(checksum),aliases_verified=True,production_changes_confined_to_dialogue_rendering_and_free_night_budget=True,packed_pixel_rows_checked=256,source_files={p:sha(ROOT/p) for p in paths},reports=reports,night_intervals_checked=nights,source_free_fade_timing=source_timing,full_game_ported=False,limits=['Four first-scroll poses start on the same frames in this natural opening sequence; the last pose duration and whole-dialogue timing still differ.','Free-night budget checked in five controlled cases per region; paid-night absolute timing remains unverified.','Inter-page global clock reset, initial loading, natural progression, all abilities, full enemy/boss behavior and ending remain unfinished.'])
    (ROOT/'validation/dialogue_scroll_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Dialogue scroll patch audit passed:',digest)

if __name__=='__main__':main()
