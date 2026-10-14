"""Audit exact artifact identity and current reports; no full-game completion claim."""
import hashlib,json,re
from PIL import Image
from pathlib import Path
from actor_reference import ROOT

def main():
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    rom=ROOT/'gaw-megadrive.bin';digest=sha(rom);data=rom.read_bytes()
    expected=0
    for n in range(0x200,len(data),2):expected=(expected+int.from_bytes(data[n:n+2],'big'))&65535
    check_data=bytearray(data);check_data[0x18e:0x190]=bytes(2)
    folded=0
    for n in range(0,len(check_data),4):folded^=int.from_bytes(check_data[n:n+4],'big')
    folded=(folded^(folded>>16))&65535
    assert len(data)==524288 and int.from_bytes(data[0x18e:0x190],'big')==folded
    assert int.from_bytes(data[0x1a4:0x1a8],'big')==len(data)-1
    assert all(sha(ROOT/p)==digest for p in ['gaw-title-megadrive.bin','megadrive/out/release/rom.bin'])
    source=ROOT/'input/original.sms';original=Path(r'D:/Cartmod/GoldenAxeWarrior/chat/Golden Axe Warrior (USA, Europe).sms')
    assert sha(source)==sha(original)==sha(ROOT/'validation/reassembled.sms')=='852e068e331dbfb01b9c38a62eecf81ce5b9f0f1bd10fff497117bd885c716c9'
    names=['actor_ai','actor','actor_spawn','actor_sprite','actor_tick','attack_motion','attack','damage','death','drop','enemy_damage','heal','healing_route','inventory','loot','movement','particles','potion','ranged','resume_capacity','resume','shield','transition','vertical','fire','fire_damage','fire_route','intro','music','village_doors','house_dialogue','save','merchant','healer','healer_natural','expanded_doors','door_masks','door_living_mask_80','door_living_mask_01','door_living_mask_55','door_living_mask_aa']
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for l in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',l))}
    raw=(ROOT/'validation/md-village-house-0/ram_03300.bin').read_bytes()
    ram=bytes(v for n in range(0,len(raw),2) for v in(raw[n+1],raw[n]))
    dma_ptr=int.from_bytes(ram[sy['dmaDataBuffer']:sy['dmaDataBuffer']+4],'big')
    assert dma_ptr!=0 and int.from_bytes(ram[sy['dataBufferSize']:sy['dataBufferSize']+2],'big')==1024
    current=[]
    for name in names:
        p=ROOT/f'validation/{name}_report.json';d=json.loads(p.read_text())
        assert d['md_sha256']==digest,(name,'stale report',d['md_sha256'],digest)
        current.append(p.name)
    d=json.loads((ROOT/'validation/report.json').read_text())
    assert d['md_sha256']==digest,('general report stale',d['md_sha256'],digest)
    current.append('report.json')
    visible_save_frames=0
    for slot in range(3):
        folder=ROOT/f'validation/md-save-slot-{slot}'
        for frame in list(range(3340,3451))+list(range(4190,4301)):
            assert (folder/f'vdp_regs_{frame:05}.bin').read_bytes()[1]&0x40
            # HUD remains visible while the service artwork is exchanged.
            assert Image.open(folder/f'frame_{frame:05}.png').convert('RGB').crop((0,176,256,224)).getbbox() is not None,('save HUD black',slot,frame)
            visible_save_frames+=1
    audit=dict(save_service_entry_exit_frames_with_visible_hud=visible_save_frames,md_sha256=digest,md_size=len(data),dma_copy_buffer_allocated=True,dma_copy_buffer_bytes=2048,header_rom_end_correct=True,sgdk_folded_xor_checksum_correct=True,standard_additive_md_checksum_matches=(expected==folded),source_sha256=sha(source),original_file_unchanged=True,sms_roundtrip_exact=True,rom_aliases_exact=True,current_native_reports=current,full_game_ported=False,known_limits=['Other village services, trade/quest scripts and most progression absent','Story-conditioned actor loading and unported progression remain incomplete','Sound effects arbitration absent','Absolute intro/house transition timing incomplete','Original RNG stream absent','Some sprite pixels differ in upper eight scanlines'])
    (ROOT/'validation/full_milestone_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
