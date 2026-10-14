"""Original 3A92..3B06 velocity, terrain records and probe offsets."""
import hashlib,json
from actor_reference import ROOT

def main():
    source=ROOT/'input/original.sms';rom=source.read_bytes()
    arrays={'world_second_spell_velocity':rom[0x3a92:0x3a9a], 'world_second_spell_terrain':rom[0x3ad9:0x3af7], 'world_second_spell_probes':rom[0x3af7:0x3b07]}
    lines=['#include <genesis.h>']
    for name,data in arrays.items():lines+=['const u8 '+name+'[] = {','    '+','.join(f'0x{x:02x}' for x in data),'};']
    output=ROOT/'megadrive/src/second_spell_data.c';output.write_text('\n'.join(lines)+'\n')
    report=dict(source_sha256=hashlib.sha256(rom).hexdigest(),resource_offsets={'world_second_spell_velocity':[0x3a92,0x3a9a],'world_second_spell_terrain':[0x3ad9,0x3af7],'world_second_spell_probes':[0x3af7,0x3b07]},resource_bytes={k:len(v) for k,v in arrays.items()},high_level_table_includes_low_level_records_by_fallthrough=True,generated_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    (ROOT/'analysis/second_spell_resources.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
