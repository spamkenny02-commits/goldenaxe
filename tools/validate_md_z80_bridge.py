"""Host publisher model: atomic rejection, ring pressure and rolling dates."""
import argparse
import ctypes as c
import hashlib
import json
import os
import random
import re
import subprocess
from actor_reference import ROOT


class Stamp(c.Structure):
    _fields_=[(n,c.c_uint8) for n in ['sequence','v','counter_hi','counter_lo','ready','error']]


class Mailbox(c.Structure):
    _fields_=[('stamp',Stamp)]+[(n,c.c_uint8) for n in ['head','tail','grant','busy']]


class Clock(c.Structure):
    _fields_=[('stamp',c.POINTER(Stamp))]+[(n,c.c_uint32) for n in ['base','reads','retries']]+[(n,c.c_uint16) for n in ['counter','lines','error']]


class Producer(c.Structure):
    _fields_=[('mailbox',c.POINTER(Mailbox)),('clock',c.POINTER(Clock))]+[(n,c.c_uint32) for n in ['last_due','published']]+[(n,c.c_uint16) for n in ['physical_line','counter','error']]


class Block(c.Structure):
    _fields_=[('due',c.c_uint32)]+[(n,c.c_uint16) for n in ['skip','count','spacing','target_hv']]+[('values',c.c_uint8*16)]


STUB=r'''
#include "md_z80_psg.h"
u8 test_slots[32][22],test_mode,test_clock_mode;
u32 test_now_line,test_epoch,test_transfers,test_refreshes;
u8 md_z80_psg_transfer(MdZ80PsgMailbox *m,const u8 *bytes,u8 index,u8 head) {
 u16 n;if(test_mode) return test_mode;
 for(n=0;n<22;n++) {test_slots[index][n]=bytes[n];}
 m->head=head;m->grant=0;test_transfers++;return 0;
}
u8 md_service_clock_now(MdServiceClock *clock,SourceMdPsgReplayClock *out) {
 test_refreshes++;if(test_clock_mode) return test_clock_mode;
 clock->base=test_epoch+(test_now_line-100)*3420;clock->counter=test_now_line;clock->reads++;
 out->master=clock->base;out->vertical=out->horizontal=out->error=0;out->lines=clock->lines;return 0;
}
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variant',default='');parser.add_argument('--native-prep',action='store_true');options=parser.parse_args();assert not options.native_prep or options.variant
    assert not options.variant or re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',options.variant)
    suffix='-'+options.variant if options.variant else ''
    folder=ROOT/('validation/md-z80-bridge'+suffix);folder.mkdir(parents=True,exist_ok=True);(folder/'stub.c').write_text(STUB)
    sdk=ROOT.parents[1]/'work/sgdk';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH']
    args=['C:/msys64/ucrt64/bin/gcc.exe','-O3','-Wall','-Wextra','-Werror','-shared','-I',str(sdk/'inc'),'-I',str(ROOT/'megadrive/src'),str(folder/'stub.c'),str(ROOT/'megadrive/src/md_z80_psg.c'),'-o',str(folder/'bridge.dll')]
    args.insert(1,'-DMD_PSG_NATIVE_PREP='+str(int(options.native_prep)))
    built=subprocess.run(args,env=env,capture_output=True,text=True);(folder/'build.log').write_text(built.stdout+built.stderr);assert not built.returncode,built.stderr
    dll=c.CDLL(str(folder/'bridge.dll'));init=dll.md_z80_psg_init;init.argtypes=[c.POINTER(Producer),c.POINTER(Mailbox),c.POINTER(Clock)];init.restype=c.c_uint8
    push=dll.md_z80_psg_push;push.argtypes=[c.POINTER(Producer),c.POINTER(Block),c.c_uint16];push.restype=c.c_uint8
    refresh=dll.md_z80_psg_refresh;refresh.argtypes=[c.POINTER(Producer)];refresh.restype=c.c_uint8
    slots=((c.c_uint8*22)*32).in_dll(dll,'test_slots');mode=c.c_uint8.in_dll(dll,'test_mode');clock_mode=c.c_uint8.in_dll(dll,'test_clock_mode');now=c.c_uint32.in_dll(dll,'test_now_line');epoch_var=c.c_uint32.in_dll(dll,'test_epoch');transfers=c.c_uint32.in_dll(dll,'test_transfers');refreshes=c.c_uint32.in_dll(dll,'test_refreshes')
    core=ROOT.parents[1]/'work/genesis-plus-gx/core';hvc=(core/'hvc.h').read_bytes();ctrl=(core/'vdp_ctrl.c').read_bytes()
    h=[int(x,16)for x in re.findall(r'0x([0-9a-fA-F]+)',hvc.decode().split('static const uint8 cycle2hc32[3420] =')[1].split('};')[0])];assert len(h)==3420
    checks=0;rows=[]
    for lines in [262,313]:
        epoch=0xffff0000;epoch_var.value=epoch;mb=Mailbox();clock=Clock(c.pointer(mb.stamp),epoch,0,0,100,lines,0);p=Producer();mode.value=clock_mode.value=0;now.value=100;mb.grant=1
        assert init(c.byref(p),c.byref(mb),c.byref(clock))==0
        rng=random.Random(lines);pending=[];absolute=100;cursor_wraps=0;old_head=0;full=0
        for i in range(6000):
            n=rng.randrange(1,17);spacing=rng.choice([0,315,630])
            if not spacing:n=1
            if spacing==630:n=min(n,8)
            absolute+=rng.randrange(4,120);phase=rng.randrange(3420);offset=(absolute-100)*3420+phase
            b=Block((epoch+offset)&0xffffffff,(16-n)*18 if spacing==315 else (8-n)*40 if spacing==630 else 0,n,spacing,0,(c.c_uint8*16)(*(rng.randrange(256)for _ in range(16))))
            before=(bytes(slots),mb.head,p.published,p.last_due,transfers.value)
            status=push(c.byref(p),c.byref(b),1)
            if status==2:
                full+=1;assert before==(bytes(slots),mb.head,p.published,p.last_due,transfers.value)
                while len(pending)>8:
                    line,_=pending.pop(0);now.value=max(now.value,line);mb.tail=(mb.tail+1)&255
                mb.grant=1;assert push(c.byref(p),c.byref(b),1)==0
            else:assert status==0,(lines,i,status)
            rounded=(phase+19)//20;target_line=absolute+(rounded==171);rounded%=171;physical=target_line%lines;raw_v=(physical if physical<=(258 if lines==313 else 234) else physical-lines)&255
            expected=[target_line&255,(target_line>>8)&255,raw_v,h[rounded*20],2 if spacing==630 else 1 if spacing==315 else 0,n]+list(b.values)
            assert list(slots[(mb.head-1)&31])==expected,(lines,i,list(slots[(mb.head-1)&31]),expected)
            assert p.last_due==(b.due+(n-1)*spacing)&0xffffffff and p.published==i+1
            cursor_wraps+=mb.head<old_head;old_head=mb.head;pending.append((target_line,expected));mb.grant=1;checks+=1
        rows.append(dict(lines=lines,descriptors=6000,cursor_wraps=cursor_wraps,full_rejections=full,physical_lines=absolute-100,refreshes=clock.reads))
    # Isolated error tests use a fresh cold session.
    mb=Mailbox();mb.grant=1;clock=Clock(c.pointer(mb.stamp),epoch,0,0,100,262,0);p=Producer();now.value=100;assert init(c.byref(p),c.byref(mb),c.byref(clock))==0
    good=Block((epoch+68400)&0xffffffff,0,1,0,0,(c.c_uint8*16)(*range(16)))
    def reject(b,count,wanted):
        nonlocal checks
        before=(bytes(slots),mb.head,p.published,p.last_due,transfers.value)
        assert push(c.byref(p),c.byref(b)if b else None,count)==wanted
        assert before==(bytes(slots),mb.head,p.published,p.last_due,transfers.value);checks+=1
    for count in [0,17]:
        bad=Block.from_buffer_copy(good);bad.count=count;reject(bad,1,1)
    for spacing in [1,314,316,629,631]:
        bad=Block.from_buffer_copy(good);bad.spacing=spacing;reject(bad,1,1)
    bad=Block.from_buffer_copy(good);bad.skip=1;reject(bad,1,1);reject(good,2,1);reject(None,1,1)
    bad=Block.from_buffer_copy(good);bad.due=epoch-1;reject(bad,1,3)
    bad.due=(epoch+32760*3420)&0xffffffff;reject(bad,1,3)
    mode.value=5;reject(good,1,5);mode.value=0
    assert push(c.byref(p),c.byref(good),1)==0
    bad=Block.from_buffer_copy(good);bad.due-=1;reject(bad,1,3)
    mb.stamp.error=1;reject(good,1,4);mb.stamp.error=0
    mb.head=33;mb.tail=0;reject(good,1,4);assert p.error
    mb=Mailbox();clock=Clock(c.pointer(mb.stamp),epoch,0,0,100,262,0);p=Producer();assert init(c.byref(p),c.byref(mb),c.byref(clock))==0
    clock_mode.value=3;assert refresh(c.byref(p))==4 and p.error;clock_mode.value=0;assert refresh(c.byref(p))==4
    report=dict(native_prep=options.native_prep,checks=checks,rows=rows,sources={n:hashlib.sha256((ROOT/'megadrive/src'/n).read_bytes()).hexdigest()for n in ['md_z80_psg.c','md_z80_psg.h']},reference_sha256={'hvc.h':hashlib.sha256(hvc).hexdigest(),'vdp_ctrl.c':hashlib.sha256(ctrl).hexdigest()},limits=['Host-only C publisher/clock/transport model; no BUSREQ safety or Z80 execution claim.12000ordered descriptors cross ring/full/u8/u16/u32 boundaries; targets checked against independent physical HV tables. Atomic rejected format/order/horizon/FULL/WAIT/fault preserves payload/head/count/lastdue. Native CPU/bus/cadence verified separately.'])
    (ROOT/('analysis/md_z80_bridge'+('_'+options.variant.replace('-','_') if options.variant else '')+'_report.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
