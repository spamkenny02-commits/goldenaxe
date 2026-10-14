import hashlib,json
from actor_reference import ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=ROOT/'versions/v0174-911973c5';s=(ROOT/'megadrive/src/paid_passage.inc').read_text()
 s=s.replace('u16 black[32]={0},n;','u16 black[32]={0};')
 block='''        load_house_room(paid_passage_target,0);
        /* State8 ->1DE2 falls through1DEB and restores all sprite colors. */
        for(n=0;n<16;n++) sms_palette[16+n]=menu_palette[n];
        prepare_hero_armor_palette();sms_palette[31]=(world_clock()&2)?2:1;
        reveal_world();return TRUE;'''
 assert block in s;s=s.replace(block,'        load_house_room(paid_passage_target,0);reveal_world();return TRUE;')
 assert s==(base/'paid_passage.inc').read_text()
 for name in ['main.c','actors.c','paid_passage_data.c','fairy.inc','fairy_data.c','minigame.inc','minigame_core.inc','minigame_data.c','save.inc']:assert (ROOT/'megadrive/src'/name).read_bytes()==(base/name).read_bytes()
 evidence={}
 for name in ['paid_passage_unit_report.json','paid_passage_gameplay_report.json']:
  p=ROOT/'validation'/name;d=json.loads(p.read_text());assert d['md_sha256']==sha(ROOT/'gaw-megadrive.bin');evidence[name]=sha(p)
 assert json.loads((ROOT/'validation/paid_passage_unit_report.json').read_text())['cases']==18528
 d=json.loads((ROOT/'validation/paid_passage_gameplay_report.json').read_text());assert len(d['cases'])==20 and all(c['final_foreground_colors_exact']==15 for c in d['cases'])
 old=json.loads((base/'paid_passage_patch_audit.json').read_text());assert old['md_sha256']==sha(base/'gaw-megadrive-v0174.bin')
 for name,digest in old['evidence_sha256'].items():assert sha(base/name)==digest
 rom=(ROOT/'gaw-megadrive.bin').read_bytes();assert len(rom)==1048576 and rom==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
 checksum=sum(int.from_bytes(rom[i:i+2],'big') for i in range(512,len(rom),2))&65535
 assert int.from_bytes(rom[0x18e:0x190],'big')==checksum and rom[0x1a4:0x1a8]==bytes.fromhex('000fffff') and rom[0x1b0:0x1b4]==bytes.fromhex('5241f820')
 report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),change_only_original1DEB_foreground_palette_restore_after_paid_exit=True,prior_main_actors_fairy_minigame_save_unchanged=True,baseline_v0174_archived_evidence_verified=True,evidence_sha256=evidence,rom_bytes=len(rom),checksum=checksum,aliases_header_verified=True,full_game_ported=False,limits=['18528 rules and20 controlled PAL/NTSC passage integrations repeated for current ROM;15 static foreground CRAM colors match original in every case, animated31 excluded. Destination enemies cleared in these isolated frontend tests.','v0174 minigame/fairy regressions remain archived baseline evidence, not claimed rerun for current ROM. Their source plus main/actors is byte-identical.','Uncontrolled destination combat still differs. Native foreground loading resumes earlier and clocks/spawn coordinates differ; read-only profiles retain this. Original RNG, global timing, full progression and hardware fidelity remain open.'])
 (ROOT/'validation/paid_passage_palette_patch_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Palette-only change,15 original foreground colors, current passage checks and immutable baseline verified.')
if __name__=='__main__':main()
