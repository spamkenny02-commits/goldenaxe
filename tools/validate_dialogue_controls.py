"""Compare controlled text fixtures through original SMS and native renderers.

Only the opening text resource (and MD checksum) is patched in test copies.
Production ROMs are read-only; argument fixtures are explicit RAM injections.
"""
import contextlib,hashlib,io,json,re,sys
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    baseline='--baseline' in sys.argv
    sms=(ROOT/'input/original.sms').read_bytes();md=(ROOT/'gaw-megadrive.bin').read_bytes()
    symbols={m[2].split('.lto_priv.')[0]:int(m[1],16) for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    original=sms[0xeb68:sms.index(0,0xeb68)+1];assert md[symbols['opening_text']:symbols['opening_text']+len(original)]==original
    fixtures=[('plain',b'A BC. ',None),('toggle',b'\\\xc2\xc3 \\'+b'\xc2\xc3. ',None),('toggle_inside_word',b'\xc2\\\xc3\\\xc2. ',None),('double_toggle',b'\\\\\xc2. ',None),('toggle_wrap',b'\\'+b'\xc2'*20+b' '+b'\xc3'*12+b' \\'+b'\xc2'*6+b'. ',None),('overwide_word',b'\\'+b'\xc2'*27+b' '+b'\xc3'*12+b' \\'+b'\xc2'*6+b'. ',None),('forced_name',b'\\\xc2 % \xc2. ',b'\xc2'),('number_zero',b'Prix #. ',0),('number_65',b'Prix #. ',65),('number_12345',b'Prix #. ',12345),('pause',b'Avant$Apres. ',None),('pause_toggle',b'\\\xc2$\xc3 \\'+b'\xc2. ',None),('newline_toggle',b'\\\xc2\xff\xc3 \\'+b'\xc2. ',None)]
    cases=[]
    for region in ['auto','pal']:
        for name,text,argument in fixtures:
            assert len(text)+1<=len(original)
            folder=ROOT/f'validation/dialogue-controls-{region}-{name}';folder.mkdir(exist_ok=True)
            records={};patched_hashes={};is_pause=b'$' in text
            frames=[1650,1800] if is_pause else [1800]
            for tag,production,offset in [('sms',sms,0xeb68),('md',md,symbols['opening_text'])]:
                data=bytearray(production);data[offset:offset+len(text)+1]=text+b'\0'
                if tag=='md':data[0x18e:0x190]=(sum(int.from_bytes(data[n:n+2],'big') for n in range(512,len(data),2))&65535).to_bytes(2,'big')
                allowed=set(range(offset,offset+len(text)+1))|({0x18e,0x18f} if tag=='md' else set())
                assert all(a==b or n in allowed for n,(a,b) in enumerate(zip(production,data)))
                path=folder/f'fixture.{"sms" if tag=="sms" else "bin"}';path.write_bytes(data);patched_hashes[tag]=sha(data)
                bitmap={};hardware={};writes=[]
                if argument is not None:
                    if isinstance(argument,bytes):
                        value=argument+b'\0'*(9-len(argument));address=0xb0 if tag=='sms' else symbols['character_name']&65535
                        writes=[(1475,address,value)]
                    else:
                        address=0xb0 if tag=='sms' else symbols['dialogue_number']&65535
                        writes=[(1475,address,argument.to_bytes(2,'little' if tag=='sms' else 'big'))]
                def observe(frame,raw):
                    if frame not in frames:return
                    if tag=='sms':value=bytes(raw[0x1100:0x1510])
                    else:
                        a=symbols['scratch']&65535;value=bytes(raw[(a+n)^1] for n in range(1040))
                    bitmap[frame]=value
                def vram(frame,v):
                    if frame not in frames:return
                    if tag=='sms':
                        valid=all(v[0x2000+n*4]==255 and v[0x2002+n*4]==v[0x2003+n*4]==0 for n in range(1040))
                        value=bytes(v[0x2001+n*4] for n in range(1040))
                    else:
                        valid=True;value=bytearray()
                        for row in range(1040):
                            start=(272+row//8)*32+(row%8)*4;bits=0
                            for x in range(8):
                                color=(v[(start+x//2)^1]>>(4 if x%2==0 else 0))&15
                                if color not in [1,3]:valid=False
                                bits|=((color>>1)&1)<<(7-x)
                            value.append(bits)
                    hardware[frame]=(bytes(value),valid)
                inputs=PRESSES[:6]+([(1700,1710,8)] if is_pause else [])
                with contextlib.redirect_stdout(io.StringIO()):run(path,1800,folder/tag,set(),([(200,220,0)] if tag=='sms' else [])+inputs,ram_writes=writes,ram_observer=observe,vram_observer=vram,core_options={'genesis_plus_gx_region_detect':region})
                records[tag]=(bitmap,hardware)
            checks=[]
            for frame in frames:
                a,ha=records['sms'];b,hb=records['md']
                checks.append(dict(frame=frame,software_bitmap_exact=a[frame]==b[frame],hardware_bitmap_exact=ha[frame][0]==hb[frame][0],hardware_colors_valid=ha[frame][1] and hb[frame][1],source_bitmap_sha256=sha(a[frame]),native_bitmap_sha256=sha(b[frame])))
            passed=all(x['software_bitmap_exact'] and x['hardware_bitmap_exact'] and x['hardware_colors_valid'] for x in checks)
            if is_pause:passed=passed and records['sms'][0][1650]!=records['sms'][0][1800] and records['md'][0][1650]!=records['md'][0][1800]
            case=dict(region=region,name=name,text_hex=text.hex(),argument_hex=argument.hex() if isinstance(argument,bytes) else argument,fixture_hashes=patched_hashes,checks=checks,passed=passed,controlled_argument_ram_injection=argument is not None)
            cases.append(case);print(region,name,passed,flush=True)
            if not baseline:assert passed,(region,name,checks)
    report=dict(md_sha256=sha(md),source_sha256=sha(sms),production_roms_unmodified=True,test_rom_text_resources_modified=True,baseline_diagnostic=baseline,cases=cases,full_game_ported=False,limits=['Controlled short opening-text fixtures, not natural quests or full conversations.','Only stable software/hardware bitmap shapes, pause continuation and color indices; no timing, palette, marker or audio equivalence.'])
    (ROOT/f'validation/dialogue_controls{"_baseline" if baseline else ""}_report.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
