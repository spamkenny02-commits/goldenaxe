"""Audit native scheduler IRQ entry R/raster directly against source sidecars."""
import hashlib
import json
import struct
from actor_reference import ROOT


def main():
    cases=json.loads((ROOT/'validation/native-source-wait/cases.json').read_text())
    reference=json.loads((ROOT/'analysis/wait_refresh_report.json').read_text())
    archive=ROOT/'analysis/full-irq-refresh-research-v0183';rows=[];offset=0
    for row in reference['rows']:
        base=archive/f"validation/full-irq-refresh-live/{row['town']:02x}-{row['mask']:02x}"
        region=row['region'];raw=(base/f'{region}-full-irq-records.bin').read_bytes()
        meta=(base/f'{region}-full-irq-m1-records.bin').read_bytes();lookup={}
        for n in range(len(raw)//800):
            time=struct.unpack_from('<Q',raw,n*800)[0]
            refresh=struct.unpack_from('<I',meta,n*152+80)[0]
            cpu,line,line_master,lines,*_=struct.unpack_from('<8I',meta,n*152+120)
            delta=((cpu-line_master+0x80000000)&0xffffffff)-0x80000000
            lookup[time]=((line*3420+delta)%(lines*3420),refresh)
        waits=(ROOT/f"validation/wait-refresh/{row['town']:02x}-{row['mask']:02x}/{region}-save-wait-records.bin").read_bytes()
        checked=0
        for n in range(row['cases']):
            start=struct.unpack_from('<Q',waits,n*112)[0];case=cases[offset+n]
            for e in range(0,len(case['events']),6):
                elapsed,raster,refresh,_,_,full=case['events'][e:e+6]
                assert full and lookup[start+elapsed]==(raster,refresh),(row['town'],row['mask'],region,n,'entry R/raster',lookup.get(start+elapsed),(raster,refresh))
                checked+=1
        offset+=row['cases'];rows.append(dict(town=row['town'],mask=row['mask'],region=region,IRQ_entries=checked))
        print(row['town'],row['mask'],region,checked,'native entry R/raster matches source0137 after opcode fetch',flush=True)
    assert offset==len(cases)
    report=dict(IRQ_entries=sum(r['IRQ_entries'] for r in rows),rows=rows,
                clock_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_clock.c').read_bytes()).hexdigest(),
                context_helper_sha256=hashlib.sha256((ROOT/'megadrive/src/source_irq_context.c').read_bytes()).hexdigest(),
                limits=['Entry0137 includes its first opcode fetch in GPG observer. Six vector instruction fetches plus first body fetch match native callback convention.',
                        'Exact retained full-IRQ source sidecars on controlled paid routes; physical acknowledgement R increment not claimed.'])
    (ROOT/'analysis/native_irq_entry_report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
