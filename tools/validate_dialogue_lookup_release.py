"""Check actual C lookup semantics and bind the playable v0224 evidence."""
import ctypes, json, os, re, subprocess
from run_core import ROOT
from archive_lossless_evidence import sha
from generate_dialogue_glyph_lookup import lookup

def main():
    charset, _ = lookup()
    current = (ROOT/'megadrive/src/main.c').read_text()
    previous = subprocess.check_output(['git','show','f8dc1a8:megadrive/src/main.c'], cwd=ROOT).decode().replace('\r\n','\n')
    def function(text):
        start=text.index('static u16 dialog_glyph(u8 value,bool small)')
        return text[start:text.index('\nstatic void upload_dialog_bitmap',start)]
    folder=ROOT/'validation/dialogue-lookup-v0224';folder.mkdir(exist_ok=True)
    code='typedef unsigned char u8; typedef unsigned short u16; typedef short s16; typedef unsigned char bool;\n'
    code+='static const u8 dialog_charset[] = {'+','.join(str(x) for x in charset)+'};\n'
    code+=function(previous).replace('dialog_glyph','reference_glyph')+function(current)
    code+='\nunsigned check(void) { unsigned v,s; for(v=0;v<256;v++) for(s=0;s<2;s++) if(reference_glyph(v,s)!=dialog_glyph(v,s)) return 0; return 512; }\n'
    source=folder/'lookup.c';source.write_text(code)
    env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    built=subprocess.run(['C:/msys64/ucrt64/bin/gcc.exe','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-I',str(ROOT/'megadrive/src'),str(source),'-o',str(folder/'lookup.dll')],env=env,capture_output=True,text=True)
    (folder/'compile.log').write_text(built.stdout+built.stderr);assert built.returncode==0,built.stderr
    assert ctypes.CDLL(str(folder/'lookup.dll')).check()==512
    digest=sha((ROOT/'gaw-megadrive.bin').read_bytes());cases=[];evidence={}
    for suffix in ['', '-pal']:
        names=[f'analysis/dialogue_preparation_v{v}{suffix}_profile.json' for v in ['0223','0224']]
        old,new=[json.loads((ROOT/name).read_bytes()) for name in names]
        assert new['md_sha256']==digest
        assert old['md_sha256']=='39e6995514a87d170d4d1fc713938a3645905842fe93a340415c80e996057a31'
        assert old['results']['sms']==new['results']['sms']
        page=lambda p:next(e['frame'] for e in p['results']['md']['events'] if e['function']=='wait_dialog_continue')
        start=lambda p:next(e['frame'] for e in p['results']['md']['events'] if e['function']=='render_dialogue_text')
        assert start(old)==start(new)
        sms=new['results']['sms'];md=new['results']['md'];source_page=next(e['frame'] for e in sms['events'] if e['pc']==0x7f4)
        events=[e for e in sms['events'] if e['pc']==0x7b3 and e['frame']<=source_page]
        shapes=set();position=0
        for e in events:
            h=sms['hardware_bitmap_sha256'][str(e['frame'])];assert sms['hardware_bitmap_colors_valid'][str(e['frame'])];shapes.add(h)
            matches=[int(f) for f,v in md['hardware_bitmap_sha256'].items() if v==h and md['hardware_bitmap_colors_valid'][f] and int(f)>=position]
            assert matches,(suffix,e['frame'],h)
            position=min(matches)
        assert len(events)==37 and len(shapes)==29
        gain=page(old)-page(new);assert gain==(0 if suffix else 3)
        cases.append(dict(region=new['region'],source_page_wait_frame=source_page,previous_page_wait_frame=page(old),current_page_wait_frame=page(new),frames_gained=gain,remaining_delay_frames=page(new)-source_page,completed_source_uploads_preserved=37,distinct_source_bitmaps_preserved_in_order=29))
        for name in names:evidence[name]=sha((ROOT/name).read_bytes())
    names=['validation/dialogue_controls_report.json','validation/dialogue_scroll_report.json','analysis/dialogue_vblank_v0224_report.json','analysis/dialogue_page_buttons_v0224_report.json']
    for name in names:
        raw=(ROOT/name).read_bytes();r=json.loads(raw);assert r['md_sha256']==digest
        if name.endswith('dialogue_controls_report.json'):assert len(r['cases'])==26 and all(c['passed'] for c in r['cases'])
        else:assert r['passed']
        evidence[name]=sha(raw)
    result=dict(md_sha256=digest,passed=True,host_exact_c_lookup_cases=512,reference_commit='f8dc1a8',cases=cases,evidence=evidence,source_files={name:sha((ROOT/name).read_bytes()) for name in ['megadrive/src/main.c','megadrive/src/dialogue_glyph_lookup.inc','tools/generate_dialogue_glyph_lookup.py','build.ps1']},scope='Exact old/new compiled C lookup for every input byte and both font modes; actual SMS/68000 text fixtures and natural first-page presentation. No complete dialogue cadence, full campaign, RNG or hardware fidelity claim.',full_game_validated=False,complete_dialogue_timing_exact=False)
    (ROOT/'analysis/dialogue_lookup_v0224_report.json').write_text(json.dumps(result,indent=2)+'\n');print(result['cases'])

if __name__=='__main__':main()
