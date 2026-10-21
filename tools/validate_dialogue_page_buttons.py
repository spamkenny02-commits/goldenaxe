"""Source07EE ignores directions even in native indoor-dialogue context."""
import contextlib,io,json,re,sys
from run_core import ROOT,run
from validate_actor_tick import PRESSES
from validate_playable_sprite_limit import symbols
from validate_service_wait_markers import baseline_symbols
from archive_lossless_evidence import sha

def main():
    baseline='--baseline' in sys.argv;rom=ROOT/'versions/v0222-13edb546/gaw-megadrive-v0222.bin' if baseline else ROOT/'gaw-megadrive.bin'
    sy=baseline_symbols() if baseline else symbols(ROOT/'megadrive/out/release/symbol.txt');syfile=ROOT/('validation/v0222-symbols.txt' if baseline else 'megadrive/out/release/symbol.txt')
    text_address=next(int(m[1],16) for line in syfile.read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line)) and m[2].split('.lto_priv.')[0]=='opening_text')
    digest=sha(rom.read_bytes());version=next(e['version'] for e in json.loads((ROOT/'versions/index.json').read_bytes()) if e['sha256']==digest);cases=[]
    for region in ['auto','pal']:
        bitmaps={};fixtures={}
        for tag,path,offset in [('sms',ROOT/'input/original.sms',0xeb68),('md',rom,text_address)]:
            production=path.read_bytes();image=bytearray(production);text=b'Avant$Apres.\0';image[offset:offset+len(text)]=text
            if tag=='md':image[0x18e:0x190]=(sum(int.from_bytes(image[n:n+2],'big') for n in range(512,len(image),2))&65535).to_bytes(2,'big')
            allowed=set(range(offset,offset+len(text)))|({0x18e,0x18f} if tag=='md' else set());assert all(a==b or n in allowed for n,(a,b) in enumerate(zip(image,production)))
            folder=ROOT/f'validation/dialogue-page-buttons-v{version:04d}/{region}-{tag}';folder.mkdir(parents=True,exist_ok=True);fixture=folder/('fixture.sms' if tag=='sms' else 'fixture.bin');fixture.write_bytes(image);rows={}
            def observe(f,r):
                if f not in [1650,1750,1900]:return
                rows[f]=bytes(r[0x1100:0x1510]) if tag=='sms' else bytes(r[(sy['scratch']+n)^1] for n in range(1040))
            inputs=PRESSES[:6]+[(1700,1700,4),(1800,1800,8)]
            writes=[] if tag=='sms' else [(1400,sy['house_dialogue_active'],b'\0\1')]
            with contextlib.redirect_stdout(io.StringIO()):run(fixture,1900,folder,{1650,1750,1900},([(200,220,0)] if tag=='sms' else [])+inputs,ram_writes=writes,ram_observer=observe,core_options={'genesis_plus_gx_region_detect':region})
            bitmaps[tag]=rows;fixtures[tag]=sha(image)
        assert bitmaps['sms'][1650]==bitmaps['sms'][1750] and bitmaps['sms'][1750]!=bitmaps['sms'][1900]
        passed=bitmaps['sms']==bitmaps['md'];cases.append(dict(region=region,source_ignores_up=True,native_ignores_up=bitmaps['md'][1650]==bitmaps['md'][1750],action_continues_afterward=bitmaps['md'][1750]!=bitmaps['md'][1900],all_three_1040_byte_bitmaps_source_exact=passed,fixture_sha256=fixtures,passed=passed));print(region,'indoor intermediate page rejects Up',passed,flush=True)
    report=dict(md_sha256=digest,source_sha256=sha((ROOT/'input/original.sms').read_bytes()),passed=all(c['passed'] for c in cases),diagnostic_only=baseline,cases=cases,scope='Test copies replace only opening text with Avant$Apres and native checksum. Native indoor flag is an explicit test-only RAM injection; original07EE uses no such flag. Up at1700 must retain the pause, action at1800 must advance. Three settled1040-byte software bitmaps compared per region; no natural indoor route or full framebuffer/timing claim.')
    (ROOT/f'analysis/dialogue_page_buttons_v{version:04d}_report.json').write_text(json.dumps(report,indent=2)+'\n')
    if not baseline:assert report['passed']

if __name__=='__main__':main()
