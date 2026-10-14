"""Check current and exact archived-v0082 fire image timing near the top edge."""
import contextlib,hashlib,io,json,re
from PIL import Image
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    base=ROOT.parents[1]/'work/gaw-baseline-v0082/megadrive/out/release'
    archived=ROOT/'versions/v0082-365b546d/gaw-megadrive-v0082.bin'
    assert (base/'rom.bin').read_bytes()==archived.read_bytes()
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (base/'symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    initial=(ROOT/'validation/sms-shield-detail/ram_03740.bin').read_bytes();items=bytearray(17);items[0]=1;items[4]=1
    writes=[(3741,sy['world_actor_state'],bytes(768)),(3741,sy['hero_selected_item'],(4).to_bytes(2,'big')),(3741,sy['hero_items'],bytes(items)),(3741,sy['hero_direction'],bytes(2)),(3741,sy['hero_magic'],(24).to_bytes(2,'big')),(3741,sy['vtimer'],int(initial[0x2f]).to_bytes(4,'big'))]
    frames=[3748,3749,3750,3751,3752,3753];folder=ROOT/'validation/md-fire-up-baseline-v0082'
    with contextlib.redirect_stdout(io.StringIO()):run(archived,3753,folder,set(frames),PRESSES+[(3748,3755,8),(3757,3760,8),(3775,3778,8),(3795,3798,8),(3815,3818,8),(3835,3838,8)],ram_writes=writes)
    source=ROOT/'validation/sms-fire-up';current=ROOT/'validation/md-fire-up';cases=[]
    assert json.loads((source/'capture.json').read_bytes())['rom_sha256']==sha(ROOT/'input/original.sms')
    assert json.loads((current/'capture.json').read_bytes())['rom_sha256']==sha(ROOT/'gaw-megadrive.bin')
    for frame in frames:
        a=Image.open(source/f'frame_{frame:05}.png').convert('RGB');colors=set(a.getdata());differences={}
        for tag,path in [('baseline',folder),('current',current)]:
            b=Image.open(path/f'frame_{frame:05}.png').convert('RGB').crop((0,16,256,208))
            conv={v:min(colors,key=lambda t:sum((x-y)**2 for x,y in zip(v,t))) for v in set(b.getdata())}
            differences[tag]=sum(x!=conv[y] for x,y in zip(a.getdata(),b.getdata()))
        # Verify baseline argument injection and the full actual spell record.
        s=(source/f'ram_{frame:05}.bin').read_bytes();r=(folder/f'ram_{frame:05}.bin').read_bytes()
        a0=sy['world_spell_state'];assert bytes(r[(a0+i)^1] for i in range(48))==s[0x330:0x360]
        cases.append(dict(frame=frame,normalized_pixel_differences=differences,baseline_spell_record_exact=True))
    report=dict(md_sha256=sha(ROOT/'gaw-megadrive.bin'),source_sha256=sha(ROOT/'input/original.sms'),baseline_md_sha256=sha(archived),baseline_rebuild_byte_exact=True,diagnostic_only=True,cases=cases,limits=['One controlled up-fire sequence near the top edge; normalized images, not complete scanline timing accounting.'])
    (ROOT/'validation/fire_beam_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
    print(cases)

if __name__=='__main__':main()
