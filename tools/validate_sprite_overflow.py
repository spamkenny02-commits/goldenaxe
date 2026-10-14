"""Measure source SAT preparation, hardware display and overflow-status latency."""
import contextlib
import hashlib
import io
import json
import re
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES


def overflow(ys):
    lines=[0]*192
    for raw in ys:
        if raw==208: break
        top=raw+1 if raw<208 else raw-255
        for line in range(max(0,top),min(192,top+8)):
            lines[line]+=1
    return max(lines)>8, max(lines)


def main():
    template=bytearray((ROOT/'validation/sms-vertical-check/ram_03120.bin').read_bytes()[0x600:0x630])
    writes=[]
    fixtures=[]
    for frame,count,x,y in [(3127,0,80,64),(3135,5,80,64),(3147,0,80,64),
                             (3159,4,80,64),(3171,5,255,64),(3183,0,80,64),
                             (3195,5,80,0),(3207,5,80,248),(3219,5,80,200),
                             (3231,5,80,220),(3243,0,80,64)]:
        actors=bytearray(768)
        for slot in range(count):
            e=bytearray(template);e[3]=1;e[4]=120;e[5]=0;e[6]=255
            e[0x10:0x18]=bytes(8);e[0x11]=y;e[0x13]=x
            actors[slot*48:(slot+1)*48]=e
        writes.append((frame,0x600,bytes(actors)))
        fixtures.append(dict(frame=frame,actors=count,x=x,y=y))
    sy={m[2].split('.lto_priv.')[0]:int(m[1],16)&65535 for line in (ROOT/'megadrive/out/release/symbol.txt').read_text().splitlines() if (m:=re.match(r'([0-9a-fA-F]+)\s+\w\s+(\S+)',line))}
    regions={}
    for pal in (False,True):
        rows=[];current=None
        def ram(frame,d):
            nonlocal current
            if frame<3127:return
            ys=d[0x1d40:0x1d80]
            active,maximum=overflow(ys)
            current=dict(frame=frame,prepared_overflow=active,prepared_maximum=maximum,
                         irq_status_overflow=bool(d[0x1b]&64),clock=d[0x2f])
            rows.append(current)
        def vram(frame,v):
            if frame<3127:return
            active,maximum=overflow(v[0x3f00:0x3f40])
            current.update(hardware_overflow=active,hardware_maximum=maximum)
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/'input/original.sms',3255,ROOT/('validation/sms-overflow-profile'+('-pal' if pal else '')),
                set(),[(200,220,0)]+PRESSES,ram_writes=writes,ram_observer=ram,vram_observer=vram,
                core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
        native=[]
        def md_ram(frame,raw):
            if frame<3127:return
            d=bytearray(raw);d[::2],d[1::2]=raw[1::2],raw[::2]
            def val(name):
                p=sy[name];return int.from_bytes(d[p:p+2],'big')
            native.append(dict(frame=frame,prepared_overflow=bool(val('world_sms_sprite_prepared_overflow')),irq_status_overflow=bool(val('world_sms_sprite_overflow')),display_overflow=bool(val('world_sms_sprite_display_overflow'))))
        md_writes=[(f,sy['world_actor_state'],data) for f,addr,data in writes]
        with contextlib.redirect_stdout(io.StringIO()):
            run(ROOT/'gaw-megadrive.bin',3255,ROOT/('validation/md-overflow-profile'+('-pal' if pal else '')),
                set(),[(200,220,0)]+PRESSES,ram_writes=md_writes,ram_observer=md_ram,
                core_options={'genesis_plus_gx_region_detect':'pal' if pal else 'auto'})
        differences=[]
        for a,b in zip(rows,native):
            if any(a[k]!=b[k] for k in ['prepared_overflow','irq_status_overflow']): differences.append(dict(source=a,native=b))
        assert not differences, differences[:5]
        regions['pal' if pal else 'ntsc']=dict(source=rows,native=native,comparison_frames=len(rows),differences=differences)
        previous=None
        for r in rows:
            key=tuple(r[k] for k in ['prepared_overflow','hardware_overflow','irq_status_overflow'])
            if key!=previous: print('pal' if pal else 'ntsc',r);previous=key
    report=dict(md_sha256=hashlib.sha256((ROOT/'gaw-megadrive.bin').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'input/original.sms').read_bytes()).hexdigest(),
                fixtures=fixtures,regions=regions,test_only_actor_ram_writes=True,
                status_or_vram_mutations=False)
    (ROOT/'validation/sprite_overflow_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
