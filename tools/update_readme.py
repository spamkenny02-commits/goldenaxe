"""Keep the project README release block aligned with the numbered ROM index."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
START='<!-- ROM-RELEASE:START -->'
END='<!-- ROM-RELEASE:END -->'

def refresh_readme_release(root,entry):
 path=root/'README.md'
 text=path.read_text(encoding='utf-8')
 if START not in text or END not in text:return
 assert text.count(START)==text.count(END)==1,'Ambiguous README release block'
 rom=root/'versions'/entry['rom'];data=rom.read_bytes()
 assert hashlib.sha256(data).hexdigest()==entry['sha256']
 status='Contrôles ciblés réussis ; portage complet encore non validé.' if entry['validation']=='targeted_checks_passed' else 'Compilation disponible ; validation de cette version en attente.'
 block=f'''{START}
**Version courante : v{entry['version']:04d} — {len(data)//1024} Kio.**

[Télécharger la ROM v{entry['version']:04d}](versions/{entry['rom']}) · [Toutes les versions](versions/README.md)

{status}

SHA-256 : `{entry['sha256']}`
Checksum Mega Drive : `{int.from_bytes(data[0x18e:0x190],'big'):04X}`
{END}'''
 begin=text.index(START);end=text.index(END,begin)+len(END)
 updated=text[:begin]+block+text[end:]
 if updated!=text:path.write_text(updated,encoding='utf-8')

def main():
 entries=json.loads((ROOT/'versions/index.json').read_text(encoding='utf-8'))
 digest=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest()
 entry=next(e for e in entries if e['sha256']==digest)
 refresh_readme_release(ROOT,entry)
 print(f'README aligned with ROM v{entry["version"]:04d}')

if __name__=='__main__':main()
