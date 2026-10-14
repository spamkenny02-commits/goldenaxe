"""Archive current milestone evidence and append ASCII progress notes."""
import hashlib,json,subprocess,sys
from actor_reference import ROOT
data=(ROOT/'gaw-megadrive.bin').read_bytes();digest=hashlib.sha256(data).hexdigest()
assert digest=='fa9293155842594f13c97566a540bf3940ea0657bd513168a1770e592df16ba5'
assert len(data)==1048576 and data==(ROOT/'gaw-title-megadrive.bin').read_bytes()==(ROOT/'megadrive/out/release/rom.bin').read_bytes()
assert int.from_bytes(data[0x18e:0x190],'big')==sum(int.from_bytes(data[n:n+2],'big') for n in range(0x200,len(data),2))&65535==0x1596
reports=['burst_boss_unit_report.json','burst_boss_gameplay_report.json','burst_boss_6a_entry_report.json','burst_boss_6b_entry_report.json','burst_boss_patch_audit.json','burst_contact_phase_report.json','first_boss_unit_report.json','second_boss_unit_report.json','composite_boss_unit_report.json','charging_boss_unit_report.json','timing_report.json','timing-pal_report.json','inventory_restore_report.json','gem_boss_report.json']
args=[sys.executable,str(ROOT/'tools/version_rom.py'),'--notes','Types6A/6B54D3 et projectile74 natifs;974 cas,1008 images avec horloge alignee,4 entrees de salles et regressions passent. Menu marchands restaure. Ecart collision NTSC1 image sans alignement conserve; RNG, autres boss, fin et jeu complet inacheves.']
for n in reports:
 assert json.loads((ROOT/'validation'/n).read_text())['md_sha256']==digest,n
 args+=['--report',str(ROOT/'validation'/n)]
subprocess.run(args,check=True)
note='\n\nv0114: native burst/disappearance bosses6A/6B54D3 (rooms0180/0196) and projectile74.974 explicit-input cases,1008 clock-aligned production frames,4 actual room-entry cases (47 relative actor frames,46 tiles) pass. Unaligned NTSC projectile contact MD2977/SMS2978 and clock phase delta73 remain unresolved; diagnostic archived. Prior boss routines, ordinary PAL/NTSC timing, six inventory returns and two gem chains pass. Merchant menu fix fromv0096 retained. See analysis/burst_boss_milestone.md. Next:6C54D9,6D55F1, source clock/RNG, complete audio/ending/playthrough. Port incomplete.\n'
for n in ['README.md','analysis/world_next.md']:
 p=ROOT/n
 if b'v0114: native burst/disappearance' not in p.read_bytes():
  with p.open('ab') as f:f.write(note.encode('ascii'))
print('Aliases/checksum verified; v0114 archived with14 reports and ASCII progress notes')
