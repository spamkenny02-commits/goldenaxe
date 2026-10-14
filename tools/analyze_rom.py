"""Bank-aware, conservative disassembly. Unproven bytes stay DB, never guessed code."""
import argparse, hashlib, json, re, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'work' / 'z80dis'))
from z80dis import z80

def analyze(source,trace=None):
    rom = Path(source).read_bytes()
    assert len(rom) == 0x40000
    out = ROOT / 'analysis'
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / 'input').mkdir(exist_ok=True)
    (ROOT / 'input' / 'original.sms').write_bytes(rom)
    # Reset + interrupt entry points; dispatcher table proven by 00D2..00D9.
    states = [int.from_bytes(rom[p:p+2], 'little') for p in range(0xdc, 0xf4, 2)]
    pending = [0, 8, 0x18, 0x28, 0x38, 0x66] + states
    code, occupied, unresolved, edges = {}, {}, [], []
    def edge(a, target, kind):
        edges.append({'from': a, 'to': target, 'kind': kind})
        if 0 <= target < 0x8000:
            pending.append(target)
        else:
            unresolved.append({'from': a, 'target': target, 'reason': 'banked ROM or RAM target'})
    while pending:
        p = pending.pop()
        while 0 <= p < 0x8000 and p not in code:
            if p in occupied:
                unresolved.append({'from': p, 'reason': 'overlapping instruction entry'})
                break
            i = z80.decode(rom[p:p+8], p)
            if i.status != z80.DECODE_STATUS.OK or not i.len or p+i.len > 0x8000:
                unresolved.append({'from': p, 'reason': 'invalid opcode or window boundary'})
                break
            text = z80.disasm(i)
            if any(p+k in occupied for k in range(i.len)):
                unresolved.append({'from': p, 'reason': 'overlapping decode'})
                break
            code[p] = {'address': p, 'bytes': rom[p:p+i.len].hex(), 'asm': text, 'op': i.op.name}
            for k in range(i.len): occupied[p+k] = p
            targets = [o[1] for o in i.operands if o[0] == z80.OPER_TYPE.ADDR]
            conditional = any(o[0] == z80.OPER_TYPE.COND for o in i.operands)
            op = i.op.name
            if op in ('JP','JR','CALL','DJNZ'):
                if targets:
                    edge(p, targets[-1], op)
                else:
                    unresolved.append({'from': p, 'reason': 'indirect jump; table or runtime target required'})
                if op in ('JP','JR') and not conditional: break
            elif op == 'RST':
                edge(p, i.operands[0][1], 'RST')
            elif op in ('RET','RETI','RETN') and not conditional:
                break
            p += i.len
    dynamic_count=0
    trace_states={}
    trace_sources=[]
    if trace:
        paths=trace if isinstance(trace,list) else [trace]
        counts=[0]*262144;windows=bytearray(262144);observed_states=[0]*256
        for path in paths:
            folder=Path(path);capture=json.loads((folder/'capture.json').read_text())
            assert capture['rom_sha256']==hashlib.sha256(rom).hexdigest(), 'Trace was recorded for a different ROM'
            values=struct.unpack('<262144I',(folder/'trace_counts.bin').read_bytes())
            masks=(folder/'trace_windows.bin').read_bytes()
            states_seen=struct.unpack('<256I',(folder/'trace_states.bin').read_bytes())
            for n,value in enumerate(values):counts[n]+=value;windows[n]|=masks[n]
            for n,value in enumerate(states_seen):observed_states[n]+=value
            trace_sources.append({'directory':str(folder.resolve()),'frames':capture['frames'],
                                  'core':capture['core'],'rom_sha256':capture['rom_sha256']})
        for physical,count in enumerate(counts):
            if not count: continue
            dynamic_count+=1
            window=(physical>>14) if physical<0x8000 else 2
            assert windows[physical]==1<<window, 'ROM instruction observed in multiple/unexpected CPU windows'
            pc=(window<<14)|(physical&0x3fff)
            i=z80.decode(rom[physical:physical+8],pc)
            assert i.status==z80.DECODE_STATUS.OK and i.len
            # Execution evidence overrides speculative overlapping static decoding.
            old={occupied[p] for p in range(physical,physical+i.len) if p in occupied}
            for start in old:
                if start!=physical:
                    previous=code.pop(start)
                    for p in range(start,start+len(bytes.fromhex(previous['bytes']))): occupied.pop(p,None)
            code[physical]={'address':pc,'rom_offset':physical,'bytes':rom[physical:physical+i.len].hex(),
                            'asm':z80.disasm(i),'op':i.op.name,'executions':count,'evidence':'instrumented execution'}
            for p in range(physical,physical+i.len): occupied[p]=physical
        trace_states={str(n):count for n,count in enumerate(observed_states) if count}
    hardware = []
    for p, row in sorted(code.items()):
        row.setdefault('rom_offset',p)
        row.setdefault('evidence','static reachability')
        if row['op'] in ('IN','OUT','INI','INIR','OUTI','OTIR','IND','INDR','OUTD','OTDR') or re.search(r'0xfff[c-f]', row['asm'], re.I):
            hardware.append(row)
    for bank in range(16):
        start, end = bank*0x4000, (bank+1)*0x4000
        origin = start if bank < 2 else 0x8000
        lines = [f'; ROM bank {bank:02X}; file offset ${start:05X}; CPU window ${origin:04X}',
                 '; Fixed-window static reachability plus optional bank-aware execution observations.',
                 '; DB = unclassified data/code. No claim of complete decompilation.', f'    org ${origin:04X}']
        p = start
        while p < end:
            if p in code and p+len(bytes.fromhex(code[p]['bytes'])) <= end:
                row = code[p]
                asm = re.sub(r'0x([0-9a-fA-F]+)', r'$\1', row['asm'])
                lines.append(f'    {asm:<30} ; ROM {p:05X}: {row["bytes"]}')
                p += len(bytes.fromhex(row['bytes']))
            else:
                q = p+1
                while q < min(p+16,end) and q not in code: q += 1
                lines.append('    db ' + ','.join(f'${b:02X}' for b in rom[p:q]) + f' ; ROM {p:05X}')
                p=q
        (out/f'bank_{bank:02x}.asm').write_text('\n'.join(lines)+'\n', encoding='ascii')
    report = {'sha256': hashlib.sha256(rom).hexdigest(), 'size':len(rom),
              'header_hex':rom[0x7ff0:0x8000].hex(), 'main_state_table':states,
              'provenance':'Static reachability plus optional instrumented instruction starts. Only rows carrying executions have dynamic evidence.',
              'instructions':len(code), 'decoded_bytes':len(occupied),
              'executed_instruction_starts':dynamic_count,'observed_dispatch_states':trace_states,
              'trace_sources':trace_sources,
              'unresolved':unresolved,'hardware':hardware,'edges':edges}
    (out/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (out/'code.json').write_text(json.dumps(list(sorted(code.values(),key=lambda r:r['address'])),indent=2),encoding='utf-8')
    (out/'fixed_listing.txt').write_text('\n'.join(f'{p:04X}  {row["bytes"]:12}  {row["asm"]}' for p,row in sorted(code.items()) if p<0x8000)+'\n')
    (out/'banked_listing.txt').write_text('\n'.join(f'ROM {p:05X} CPU {row["address"]:04X}  {row["bytes"]:12}  {row["asm"]}' for p,row in sorted(code.items()) if p>=0x8000)+'\n')
    print(json.dumps({k:report[k] for k in ('sha256','size','instructions','decoded_bytes','main_state_table')},indent=2))

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('rom'); ap.add_argument('--trace',action='append'); args=ap.parse_args(); analyze(args.rom,args.trace)
