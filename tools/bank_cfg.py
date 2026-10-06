#!/usr/bin/env python3
from pathlib import Path
from collections import deque, defaultdict, Counter
from dataclasses import dataclass
import csv, json, sys
sys.path.insert(0,str(Path(__file__).parent))
from z80decode import decode

ROM=Path(sys.argv[1]).read_bytes() if len(sys.argv)>1 else Path('/mnt/data/Golden Axe Warrior (USA, Europe)(1).sms').read_bytes()
OUT=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/data/gaw_decomp_phase2')
NB=len(ROM)//0x4000

@dataclass(frozen=True)
class Ctx:
    p0:int=0; p1:int=1; p2:int=2

def phys(ctx, a):
    if not (0<=a<0xC000): return None
    if a<0x400: bank=0; off=a
    elif a<0x4000: bank=ctx.p0; off=a
    elif a<0x8000: bank=ctx.p1; off=a-0x4000
    else: bank=ctx.p2; off=a-0x8000
    if not 0<=bank<NB: return None
    return bank*0x4000+off

def bank_for(ctx,a):
    p=phys(ctx,a); return None if p is None else p//0x4000

def mapped(ctx):
    m=bytearray(0x10000)
    # first 1K fixed bank0
    m[:0x400]=ROM[:0x400]
    m[0x400:0x4000]=ROM[ctx.p0*0x4000+0x400:(ctx.p0+1)*0x4000]
    m[0x4000:0x8000]=ROM[ctx.p1*0x4000:(ctx.p1+1)*0x4000]
    m[0x8000:0xC000]=ROM[ctx.p2*0x4000:(ctx.p2+1)*0x4000]
    return bytes(m)
MCACHE={}
def getmem(ctx):
    if ctx not in MCACHE: MCACHE[ctx]=mapped(ctx)
    return MCACHE[ctx]

def label(ctx,a):
    b=bank_for(ctx,a)
    return f'B{b:02X}:${a:04X}' if b is not None else f'RAM:${a:04X}'

# Seed entry points: hardware vectors + state table targets found in phase 1.
seeds=[0x0000,0x0008,0x0018,0x0028,0x0038,0x0066,0x0089,0x00D2,0x0137,0x03C0,0x0404,0x0444,0x0B95]
state_targets=[0x146D,0x00F4,0x2433,0x246F,0x24B6,0x24C5,0x24F3,0x6EBE,0x70F2,0x1101,0x257D,0x7390]
seeds += state_targets

# queue item: pc, ctx, a_const, hl_const, func_id
q=deque()
functions={}  # id -> dict
entry_to_func={}

def ensure_func(ctx,a,reason='call'):
    if not 0<=a<0xC000: return None
    fid=label(ctx,a)
    if fid not in functions:
        functions[fid]={'entry':a,'bank':bank_for(ctx,a),'ctx':ctx,'reason':reason,'insns':set(),'calls':set(),'jumps':set(),'mapper_writes':[]}
        entry_to_func[(phys(ctx,a),a)]=fid
        q.append((a,ctx,None,None,fid))
    return fid

init=Ctx()
for s in seeds: ensure_func(init,s,'seed')

# Resolve known RST $18 dispatch tables. These were verified from their callers.
def read_word(ctx,a):
    m=getmem(ctx); return m[a] | (m[(a+1)&0xffff]<<8)
def seed_table(ctx, base, indices, reason):
    for i in indices:
        t=read_word(ctx, base + i*2)
        if 0 <= t < 0xC000:
            ensure_func(ctx,t,reason)

seed_table(init,0x00DC,range(12),'dispatch_main_state')
seed_table(init,0x1EAD,range(4),'dispatch_1EAD')
# Entity type 0 is explicitly skipped; the original table has 128 entries.
seed_table(init,0x2B63,range(1,128),'dispatch_entity_type')
seed_table(init,0x2830,range(4),'dispatch_entity_hit')
# $699C skips state 0 and dispatches non-zero C090/C098 state values.
seed_table(init,0x6AF1,range(1,5),'dispatch_effect_state')
seed_table(init,0x73DD,range(4),'dispatch_state_73DD')

# $5B20 selects a per-world-cell callback from bank 2 table $B762.
# Phase 8 proved the table has 512 entries ($B762-$BB61).
ctx2=Ctx(0,1,2)
seed_table(ctx2,0xB762,range(0x200),'dispatch_world_cell')
# Bank-2 entity state tables selected by wrappers $4CDE-$54D3.  Several
# wrappers intentionally point into shifted views of the same table; seed the
# canonical table starts proved from the first code address following each table.
for _base,_count in [
    (0x8D23,20),(0x8F56,18),(0x90DB,8),(0x919B,7),(0x9290,8),
    (0x941A,6),(0x94A8,8),(0x963B,6),(0x96C1,3),(0x9726,5),
    (0x9843,6),(0x98FF,5),(0x9A1B,8),(0x9C02,4),(0xA6C7,4),
    (0xA754,6),(0xA86D,5),(0xA972,12),(0xAB40,8)]:
    seed_table(ctx2,_base,range(_count),'dispatch_entity_bank2_state')

# Bank 6 is the PSG/audio engine. $86DB dispatches E0..FF commands through 32 words.
ctx6=Ctx(0,1,6)
seed_table(ctx6,0x86F3,[i for i in range(32) if i != 15],'dispatch_audio_cmd')
# Entry 15 points at $897F, the start of a dense audio data table, not executable code.
# The command value selecting it appears to be unused; deliberately do not recurse into it.

visited=set()
mapper_events=[]
indirects=[]
rst18_sites=[]
MAX=300000
steps=0

def apply_mapper(ctx, reg, val):
    if val is None or not 0<=val<NB: return ctx
    if reg==0xFFFD: return Ctx(val,ctx.p1,ctx.p2)
    if reg==0xFFFE: return Ctx(ctx.p0,val,ctx.p2)
    if reg==0xFFFF: return Ctx(ctx.p0,ctx.p1,val)
    return ctx

while q and steps<MAX:
    pc,ctx,a_const,hl_const,fid=q.popleft(); steps+=1
    if not 0<=pc<0xC000: continue
    p=phys(ctx,pc)
    if p is None: continue
    # Include abstract constants only when useful; cap loops by not keying on them.
    vk=(p,pc,ctx,fid)
    if vk in visited: continue
    visited.add(vk)
    ins=decode(getmem(ctx),pc)
    functions[fid]['insns'].add((pc,ctx,ins.raw,ins.text))
    raw=ins.raw
    nextpc=(pc+ins.size)&0xffff

    # conservative constant propagation for A / HL, enough for mapper idioms
    na=a_const; nh=hl_const; nctx=ctx
    # A
    if len(raw)>=2 and raw[0]==0x3E: na=raw[1]
    elif raw[0]==0xAF: na=0
    elif raw[0]==0x3C and na is not None: na=(na+1)&0xff
    elif raw[0]==0x3D and na is not None: na=(na-1)&0xff
    elif len(raw)>=2 and raw[0]==0xE6 and na is not None: na &= raw[1]
    elif len(raw)>=2 and raw[0]==0xF6 and na is not None: na |= raw[1]
    elif raw[0] in (0x3A,0x0A,0x1A,0x7E,0x78,0x79,0x7A,0x7B,0x7C,0x7D,0xDB): na=None
    elif 0x80 <= raw[0] <= 0xBF and raw[0] not in (0xA7,0xB7,0xBF): na=None
    # HL
    if len(raw)>=3 and raw[0]==0x21: nh=raw[1]|(raw[2]<<8)
    elif raw[0]==0x23 and nh is not None: nh=(nh+1)&0xffff
    elif raw[0]==0x2B and nh is not None: nh=(nh-1)&0xffff
    elif raw[0] in (0xE1,): nh=None
    # mapper direct LD (nn),A
    reg=None; val=None
    if len(raw)>=3 and raw[0]==0x32:
        nn=raw[1]|(raw[2]<<8)
        if nn in (0xFFFC,0xFFFD,0xFFFE,0xFFFF): reg=nn; val=a_const
    # mapper LD (HL),n
    if len(raw)>=2 and raw[0]==0x36 and hl_const in (0xFFFC,0xFFFD,0xFFFE,0xFFFF):
        reg=hl_const; val=raw[1]
    if reg is not None:
        before=ctx; nctx=apply_mapper(ctx,reg,val)
        ev={'site':label(ctx,pc),'pc':pc,'reg':reg,'value':val,'before':[ctx.p0,ctx.p1,ctx.p2],'after':[nctx.p0,nctx.p1,nctx.p2]}
        mapper_events.append(ev); functions[fid]['mapper_writes'].append(ev)

    # CALL/RST targets become function entries. RST18 is indirect dispatcher helper.
    if ins.kind=='call' and ins.target is not None:
        tf=ensure_func(nctx,ins.target,'call')
        if tf: functions[fid]['calls'].add(tf)
        # continuation assumes mapper restored/preserved across ordinary call
        q.append((nextpc,nctx,na,nh,fid))
        if ins.cond: q.append((nextpc,nctx,na,nh,fid))
        continue
    if ins.kind=='rst':
        if ins.target==0x18:
            rst18_sites.append({'site':label(ctx,pc),'func':fid})
        tf=ensure_func(nctx,ins.target,'rst')
        if tf: functions[fid]['calls'].add(tf)
        q.append((nextpc,nctx,na,nh,fid)); continue
    if ins.kind=='jump':
        if ins.target is not None:
            functions[fid]['jumps'].add(label(nctx,ins.target))
            q.append((ins.target,nctx,na,nh,fid))
        if ins.cond: q.append((nextpc,nctx,na,nh,fid))
        continue
    if ins.kind=='indirect':
        indirects.append({'site':label(ctx,pc),'func':fid,'text':ins.text}); continue
    if ins.kind=='ret':
        if ins.cond: q.append((nextpc,nctx,na,nh,fid))
        continue
    if ins.kind=='stop': continue
    q.append((nextpc,nctx,na,nh,fid))

# Dedup mapper events
uniq=[]; seen=set()
for e in mapper_events:
    k=(e['site'],e['reg'],e['value'],tuple(e['before']),tuple(e['after']))
    if k not in seen: seen.add(k); uniq.append(e)
mapper_events=uniq

# Write per-bank reachable listing, sorted by physical location/context.
bybank=defaultdict(list)
for fid,f in functions.items():
    for pc,ctx,raw,text in f['insns']:
        b=bank_for(ctx,pc)
        if b is not None: bybank[b].append((pc,ctx,raw,text,fid,phys(ctx,pc)))
for b,rows in bybank.items():
    rows.sort(key=lambda r:(r[5],r[0],r[4]))
    with (OUT/'disasm'/f'bank_{b:02X}_reachable.asm').open('w') as fp:
        lastfid=None; seenline=set()
        for pc,ctx,raw,text,fid,ph in rows:
            lk=(ph,pc,text)
            if lk in seenline: continue
            seenline.add(lk)
            if fid!=lastfid:
                fp.write(f'\n; ---- {fid} ({functions[fid]["reason"]}) ----\n'); lastfid=fid
            fp.write(f'{label(ctx,pc):10}  {raw.hex(" "):<14} {text}\n')

# function CSV
with (OUT/'analysis'/'functions.csv').open('w',newline='') as fp:
    w=csv.writer(fp); w.writerow(['function','bank','cpu_entry','reason','reachable_insns','calls','mapper_writes'])
    for fid,f in sorted(functions.items(), key=lambda kv:(kv[1]['bank'] if kv[1]['bank'] is not None else 99,kv[1]['entry'])):
        w.writerow([fid,f['bank'],f'{f["entry"]:04X}',f['reason'],len(f['insns']),len(f['calls']),len(f['mapper_writes'])])

with (OUT/'analysis'/'callgraph.csv').open('w',newline='') as fp:
    w=csv.writer(fp); w.writerow(['caller','callee'])
    for fid,f in sorted(functions.items()):
        for c in sorted(f['calls']): w.writerow([fid,c])

(OUT/'analysis'/'mapper_events.json').write_text(json.dumps(mapper_events,indent=2))
(OUT/'analysis'/'indirect_jumps.json').write_text(json.dumps(indirects,indent=2))

# dot graph
with (OUT/'cfg'/'callgraph.dot').open('w') as fp:
    fp.write('digraph GAW {\n rankdir=LR; node [shape=box,fontname="monospace",fontsize=9];\n')
    for fid,f in functions.items():
        fp.write(' "'+fid+'" [label="'+fid+'\\n'+str(len(f['insns']))+' insns"];\n')
    for fid,f in functions.items():
        for c in f['calls']: fp.write(f' "{fid}" -> "{c}";\n')
    fp.write('}\n')

stats={
 'steps':steps,'visited_states':len(visited),'functions':len(functions),'reachable_instructions':sum(len(f['insns']) for f in functions.values()),
 'banks_with_code':{f'{b:02X}':len({r[5] for r in rows}) for b,rows in sorted(bybank.items())},
 'mapper_events':len(mapper_events),'indirect_jumps':len(indirects),'rst18_sites':len(rst18_sites)
}
(OUT/'analysis'/'stats.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats,indent=2))
