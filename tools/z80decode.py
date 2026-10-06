#!/usr/bin/env python3
"""Small dependency-free Z80 decoder for GAW recursive analysis.
Not an assembler. It prioritizes exact instruction lengths/control-flow and readable listings.
"""
from dataclasses import dataclass

R8=['B','C','D','E','H','L','(HL)','A']
R16=['BC','DE','HL','SP']
R16AF=['BC','DE','HL','AF']
CC=['NZ','Z','NC','C','PO','PE','P','M']
ALU=['ADD A,','ADC A,','SUB ','SBC A,','AND ','XOR ','OR ','CP ']
ROT=['RLC','RRC','RL','RR','SLA','SRA','SLL','SRL']
IM=[0,0,1,2,0,0,1,2]

@dataclass
class Insn:
    addr:int; size:int; raw:bytes; text:str; kind:str='normal'; target:int|None=None; cond:bool=False

def s8(x): return x-256 if x>=128 else x

def hx8(v): return f'${v&0xff:02X}'
def hx16(v): return f'${v&0xffff:04X}'

def decode(mem, pc):
    start=pc; prefix=None
    # tolerate repeated DD/FD; last one wins
    while pc < len(mem) and mem[pc] in (0xDD,0xFD):
        prefix=mem[pc]; pc+=1
    if pc>=len(mem): return Insn(start,1,mem[start:start+1],'.DB '+hx8(mem[start]))
    op=mem[pc]; pc+=1
    idx='IX' if prefix==0xDD else ('IY' if prefix==0xFD else None)
    def b():
        nonlocal pc
        if pc>=len(mem): return 0
        v=mem[pc]; pc+=1; return v
    def w():
        lo=b(); hi=b(); return lo|(hi<<8)
    def disp():
        d=s8(b()); return f'({idx}{d:+d})'
    def r8(n, use_disp=True):
        if idx is None: return R8[n]
        if n==4: return idx+'H'
        if n==5: return idx+'L'
        if n==6: return disp() if use_disp else f'({idx})'
        return R8[n]
    def r16(n):
        if idx is not None and n==2: return idx
        return R16[n]
    def r16af(n):
        if idx is not None and n==2: return idx
        return R16AF[n]
    kind='normal'; target=None; cond=False

    if op==0xCB:
        if idx is not None:
            d=s8(b()); cb=b(); x=cb>>6; y=(cb>>3)&7; z=cb&7; m=f'({idx}{d:+d})'
            if x==0:
                text=f'{ROT[y]} {m}' + (f',{R8[z]}' if z!=6 else '')
            elif x==1: text=f'BIT {y},{m}'
            elif x==2: text=f'RES {y},{m}' + (f',{R8[z]}' if z!=6 else '')
            else: text=f'SET {y},{m}' + (f',{R8[z]}' if z!=6 else '')
        else:
            cb=b(); x=cb>>6; y=(cb>>3)&7; z=cb&7
            if x==0: text=f'{ROT[y]} {R8[z]}'
            elif x==1: text=f'BIT {y},{R8[z]}'
            elif x==2: text=f'RES {y},{R8[z]}'
            else: text=f'SET {y},{R8[z]}'
    elif op==0xED:
        ed=b(); x=ed>>6; y=(ed>>3)&7; z=ed&7; p=y>>1; q=y&1
        if x==1:
            if z==0: text='IN '+(R8[y] if y!=6 else 'F')+',(C)'
            elif z==1: text='OUT (C),'+(R8[y] if y!=6 else '0')
            elif z==2: text=('ADC' if q else 'SBC')+f' HL,{R16[p]}'
            elif z==3:
                nn=w(); text=(f'LD {R16[p]},({hx16(nn)})' if q else f'LD ({hx16(nn)}),{R16[p]}')
            elif z==4: text='NEG'
            elif z==5:
                text='RETI' if y==1 else 'RETN'; kind='ret'
            elif z==6: text=f'IM {IM[y]}'
            else: text=['LD I,A','LD R,A','LD A,I','LD A,R','RRD','RLD','NOP','NOP'][y]
        elif x==2 and y>=4 and z<=3:
            tab=[['LDI','CPI','INI','OUTI'],['LDD','CPD','IND','OUTD'],['LDIR','CPIR','INIR','OTIR'],['LDDR','CPDR','INDR','OTDR']]
            text=tab[y-4][z]
        else: text=f'.DB $ED,{hx8(ed)}'
    else:
        x=op>>6; y=(op>>3)&7; z=op&7; p=y>>1; q=y&1
        if x==0:
            if z==0:
                if y==0: text='NOP'
                elif y==1: text="EX AF,AF'"
                elif y==2:
                    d=s8(b()); target=(pc+d)&0xffff; text=f'DJNZ {hx16(target)}'; kind='jump'; cond=True
                elif y==3:
                    d=s8(b()); target=(pc+d)&0xffff; text=f'JR {hx16(target)}'; kind='jump'
                else:
                    d=s8(b()); target=(pc+d)&0xffff; text=f'JR {CC[y-4]},{hx16(target)}'; kind='jump'; cond=True
            elif z==1:
                if q==0: nn=w(); text=f'LD {r16(p)},{hx16(nn)}'
                else: text=f'ADD {idx or "HL"},{r16(p)}'
            elif z==2:
                if q==0:
                    if p==0: text='LD (BC),A'
                    elif p==1: text='LD (DE),A'
                    elif p==2: nn=w(); text=f'LD ({hx16(nn)}),{idx or "HL"}'
                    else: nn=w(); text=f'LD ({hx16(nn)}),A'
                else:
                    if p==0: text='LD A,(BC)'
                    elif p==1: text='LD A,(DE)'
                    elif p==2: nn=w(); text=f'LD {idx or "HL"},({hx16(nn)})'
                    else: nn=w(); text=f'LD A,({hx16(nn)})'
            elif z==3: text=('INC ' if q==0 else 'DEC ')+r16(p)
            elif z==4: text='INC '+r8(y)
            elif z==5: text='DEC '+r8(y)
            elif z==6: text=f'LD {r8(y)},{hx8(b())}'
            else: text=['RLCA','RRCA','RLA','RRA','DAA','CPL','SCF','CCF'][y]
        elif x==1:
            if y==6 and z==6: text='HALT'; kind='stop'
            else:
                # displacement only once when either operand is indexed memory
                if idx is not None and (y==6 or z==6):
                    d=s8(b()); m=f'({idx}{d:+d})'
                    # Z80 DD/FD exception: when one operand is (IX/IY+d),
                    # H/L stay the ordinary H/L registers.  E.g. DD 6E d is
                    # LD L,(IX+d), not LD IXL,(IX+d); DD 74 d is
                    # LD (IX+d),H.  IXH/IXL are used only in register-only
                    # prefixed forms.
                    dst=m if y==6 else R8[y]
                    src=m if z==6 else R8[z]
                    text=f'LD {dst},{src}'
                else: text=f'LD {r8(y)},{r8(z)}'
        elif x==2:
            if idx is not None and z==6:
                operand=disp()
            else: operand=r8(z)
            text=ALU[y]+operand
        else:
            if z==0: text=f'RET {CC[y]}'; kind='ret'; cond=True
            elif z==1:
                if q==0: text='POP '+r16af(p)
                else:
                    if p==0: text='RET'; kind='ret'
                    elif p==1: text='EXX'
                    elif p==2: text=f'JP ({idx or "HL"})'; kind='indirect'
                    else: text=f'LD SP,{idx or "HL"}'
            elif z==2:
                nn=w(); target=nn; text=f'JP {CC[y]},{hx16(nn)}'; kind='jump'; cond=True
            elif z==3:
                if y==0: nn=w(); target=nn; text=f'JP {hx16(nn)}'; kind='jump'
                elif y==2: text=f'OUT ({hx8(b())}),A'
                elif y==3: text=f'IN A,({hx8(b())})'
                elif y==4: text=f'EX (SP),{idx or "HL"}'
                elif y==5: text='EX DE,HL'
                elif y==6: text='DI'
                elif y==7: text='EI'
                else: text='PREFIX CB' # unreachable because handled
            elif z==4:
                nn=w(); target=nn; text=f'CALL {CC[y]},{hx16(nn)}'; kind='call'; cond=True
            elif z==5:
                if q==0: text='PUSH '+r16af(p)
                else:
                    if p==0:
                        nn=w(); target=nn; text=f'CALL {hx16(nn)}'; kind='call'
                    else: text=f'.DB {hx8(op)}'
            elif z==6: text=ALU[y]+hx8(b())
            else:
                target=y*8; text=f'RST {hx16(target)}'; kind='rst'
    size=max(1,pc-start)
    return Insn(start,size,mem[start:pc],text,kind,target,cond)

if __name__=='__main__':
 import sys
 d=open(sys.argv[1],'rb').read(); pc=int(sys.argv[2],0) if len(sys.argv)>2 else 0
 for _ in range(int(sys.argv[3]) if len(sys.argv)>3 else 32):
  i=decode(d,pc); print(f'{pc:04X}: {i.raw.hex(" "):<16} {i.text}'); pc+=i.size
