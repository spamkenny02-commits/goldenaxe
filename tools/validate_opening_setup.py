"""Verify actual opening palette transfers, font patterns and story-entry frame."""
import hashlib,json,re
from actor_reference import ROOT
from audit_item_reward_visuals import sms_pixels,md_pixels
from extract_title import rle_planes

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    digest=sha(ROOT/'gaw-megadrive.bin');source=ROOT/'input/original.sms';rom=source.read_bytes()
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    reference=bytearray(0x4000);rle_planes(rom,0x1274c,reference,0x1e00,4);font=bytes(reference[0x1e00:0x2000])
    cases=[];levels=[0,3,5,7]
    for suffix in ['', '-pal']:
        p=ROOT/f'validation/opening_setup{suffix}_profile.json';d=json.loads(p.read_bytes());assert d['md_sha256']==digest and d['source_sha256']==sha(source)
        assert not d['ram_injections'] and d['production_roms_unmodified']
        source_start=next(x for x in d['results']['sms']['events'] if x['pc']==0x7444)
        native_start=next(x for x in d['results']['md']['events'] if x['function']=='render_dialogue_text')
        assert source_start['frame']==native_start['frame']==(1489 if suffix else 1490)
        color31=[];checked=0
        for frame in range(1449,1490):
            a=d['results']['sms']['cram'][str(frame)];b=d['results']['md']['cram'][str(frame)]
            for index in range(32):
                color=a[index];expected=levels[color&3]|(levels[(color>>2)&3]<<3)|(levels[(color>>4)&3]<<6)
                if index==31:
                    if b[index]!=expected:color31.append(dict(frame=frame,source=color,native_internal_cram=b[index],expected_internal_cram=expected))
                else:assert b[index]==expected,(d['region'],frame,index);checked+=1
        folders={tag:ROOT/f'validation/opening-setup-{tag}{suffix}' for tag in ['sms','md']}
        for tag,folder in folders.items():assert json.loads((folder/'capture.json').read_bytes())['rom_sha256']==(sha(source) if tag=='sms' else digest)
        sv=(folders['sms']/'vram_01480.bin').read_bytes();mv=(folders['md']/'vram_01480.bin').read_bytes();assert sv[0x1e00:0x2000]==font
        raw=(folders['md']/'ram_01480.bin').read_bytes();a=sy['sms_vram']+0x1e00
        assert bytes(raw[(a+n)^1] for n in range(512))==font
        for tile in range(240,256):assert sms_pixels(sv,tile)==md_pixels(mv,tile+16)
        ev=d['results']['sms']['events'];start=next(x for x in ev if x['pc']==0x11a5);end=next(x for x in ev if x['pc']==0x11a8)
        cost=(end['master_cycles']-start['master_cycles']-(end['irq_master_cycles']-start['irq_master_cycles']))//15
        assert cost==70986
        cases.append(dict(region=d['region'],story_entry_frame=source_start['frame'],story_entry_exact=True,palette_entries_0_to_30_cram_words_exact=checked,palette_frames=41,font_bytes_exact=512,font_tile_pixels_exact=1024,font_source_tstates=cost,color31_remaining_phase_differences=color31,profile=p.name,profile_sha256=sha(p),capture_hashes={tag:{name:sha(folder/name) for name in ['cram_01460.bin','vram_01480.bin','ram_01480.bin']} for tag,folder in folders.items()}))
    report=dict(md_sha256=digest,source_sha256=sha(source),cases=cases,full_game_ported=False,limits=['One natural name A and confirmation frame per region.','Palette color 31 still differs with the global clock phase; all residuals are listed.','First page wait, subsequent dialogue words, initial-room loading and audio waveforms remain incomplete or unverified.'])
    (ROOT/'validation/opening_setup_report.json').write_text(json.dumps(report,indent=2)+'\n');print('Opening setup: story entry, 2542 actual CRAM words and original font verified; color 31 remains phased differently.')

if __name__=='__main__':main()
