"""Archive v0118 evidence and preserve explicit remaining dispatch gaps."""
import hashlib,json,subprocess,sys
from actor_reference import ROOT
data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(data).hexdigest()
assert digest=='a72eb3e83e49733761e285e3639ef6c4a344995fd8fd45f7372b3be8d2c60405'
assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
assert int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[n:n+2],'big') for n in range(0x200,len(data),2))&65535==0xd029
assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff')
index=ROOT/'versions/index.json';entries=json.loads(index.read_text(encoding='utf-8'))
next(e for e in entries if e['version']==117)['notes']='Intermediaire6D55F1 seul. Utiliser v0118 avec63 et rapports complets du jalon.'
index.write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
reports=['final_boss_unit_report.json','final_boss_gameplay_report.json','final_boss_entry_report.json','final_boss_patch_audit.json','early_boss_unit_report.json','early_boss_gameplay_report.json','early_boss_entry_report.json','pending_actor_types_report.json','first_boss_unit_report.json','first_boss_gameplay_report.json','second_boss_unit_report.json','composite_boss_unit_report.json','charging_boss_unit_report.json','sword_boss_unit_report.json','sword_boss_gameplay_report.json','sword_boss_entry_report.json','burst_boss_unit_report.json','burst_boss_gameplay_report.json','burst_contact_phase_report.json','timing_report.json','timing-pal_report.json','inventory_restore_report.json','gem_boss_report.json']
args=[sys.executable,str(ROOT/'tools/version_rom.py'),'--notes','Boss6D55F1/filtre objet1 niveau2 et63/506B natifs;2271 cas,2034 images controlees,4 entrees et198 entrees SAT exactes. Regressions passent. Audit:29 types46..62 sans comportement natif; horloge/RNG/audio complet/fin/jeu complet inacheves.']
for n in reports:
 assert json.loads((ROOT/'validation'/n).read_text())['md_sha256']==digest,n
 args+=['--report',str(ROOT/'validation'/n)]
subprocess.run(args,check=True)
note='\n\nv0118: native6D55F1 ten states, byte-wrapped heroY-16 pursuit, three-shot cycle, shared satellites and post-state item1/level2 damage filter. Added63 shared506B/A754 dispatch with three aimed shots only; extra choice sampled only for64.482+1789 direct cases,1790+244 controlled production frames, four actual entries and198 ordered SAT entries pass. Entry still up to1 frame late; global contact phase gap persists. Prior AI/menu/timing/gem regressions pass. Audit confirms29 loaded types46..62 have no native behavior; next priority. See analysis/final_boss_milestone.md and analysis/pending_actor_types.md. v0117 intermediate superseded. Remaining dungeon AI, clock/RNG, full audio/ending/quests/saves/natural playthrough. Port incomplete.\n'
for n in ['README.md','analysis/world_next.md']:
 p=ROOT/n
 if b'v0118: native6D55F1' not in p.read_bytes():
  with p.open('ab') as f:f.write(note.encode('ascii'))
print(f'v0118 aliases/header/checksum verified;{len(reports)} reports archived and ASCII progress notes appended')
