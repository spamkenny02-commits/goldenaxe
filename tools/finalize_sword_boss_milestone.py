"""Finalize immutable v0116 evidence; keep intermediate v0115 distinct."""
import hashlib,json,subprocess,sys
from actor_reference import ROOT
data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(data).hexdigest()
assert digest=='e7069055e4dca251b0905e83e9d212e55e991321058edb640ebab5c61f851b15'
assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
assert int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[n:n+2],'big') for n in range(0x200,len(data),2))&65535==0x754e
assert data[0x1a4:0x1a8]==bytes.fromhex('000fffff')
index=ROOT/'versions/index.json';entries=json.loads(index.read_text(encoding='utf-8'))
next(e for e in entries if e['version']==115)['notes']='Intermediaire type6C/projectiles75/76; limite16 sprites rend le boss invisible. Utiliser v0116.'
index.write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
reports=['sword_boss_unit_report.json','sword_boss_gameplay_report.json','sword_boss_entry_report.json','sword_boss_patch_audit.json','burst_boss_unit_report.json','burst_boss_gameplay_report.json','burst_contact_phase_report.json','first_boss_unit_report.json','second_boss_unit_report.json','composite_boss_unit_report.json','charging_boss_unit_report.json','charging_boss_68_entry_report.json','charging_boss_69_entry_report.json','timing_report.json','timing-pal_report.json','inventory_restore_report.json','gem_boss_report.json']
args=[sys.executable,str(ROOT/'tools/version_rom.py'),'--notes','Boss6C54D9, projectile75 retour/rebonds et satellite76 natifs; correction assemblages18 sprites.660 cas et1518 images controlees passent,2 entrees/81 tiles/108 entrees SAT exactes; regressions passent. Horloge/RNG,6D, audio complet, fin et jeu complet inacheves.']
for n in reports:
 assert json.loads((ROOT/'validation'/n).read_text())['md_sha256']==digest,n
 args+=['--report',str(ROOT/'validation'/n)]
subprocess.run(args,check=True)
note='\n\nv0116: native6C54D9 ten states,75 homing/return/bounce and76 animation-driven satellite paths. Removed unsupported16-part actor-renderer cap; type6C uses18 sprites.660 direct cases and1518 clock-aligned production frames pass, including injected surviving/lethal damage. Two actual room01AC entries:47 relative actor frames,81 tiles,108 ordered SAT entries exact; arrival matches in these fixtures. Prior boss/unit/burst/charging-entry/timing/inventory/gem regressions pass. Unaligned NTSC collision phase gap remains. See analysis/sword_boss_milestone.md. v0115 intermediate invisible-boss build superseded. Next:6D55F1, source clock/RNG, full audio, ending/progression/quests/natural playthrough. Port incomplete.\n'
for n in ['README.md','analysis/world_next.md']:
 p=ROOT/n
 if b'v0116: native6C54D9' not in p.read_bytes():
  with p.open('ab') as f:f.write(note.encode('ascii'))
print('v0116 aliases/header/checksum verified;17 reports archived and ASCII progress notes appended')
