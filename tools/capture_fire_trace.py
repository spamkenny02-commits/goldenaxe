"""Instruction-hook observation of four controlled exterior fire casts."""
from actor_reference import ROOT
from run_core import run
from validate_actor_tick import PRESSES

def main():
    writes=[(3741,0x600,bytes(768)),(3741,0xdf,b'\x04'),(3741,0xe4,b'\x01')]
    for frame,direction in [(3741,0),(3800,1),(3850,2),(3900,3)]:
        writes.extend([(frame,0x30a,bytes([direction])),(frame,0x310,(0x7000).to_bytes(2,'little')+(0x8800).to_bytes(2,'little'))])
    writes.append((3900,0xe4,b'\x02'))
    run(ROOT/'input/original.sms',3960,ROOT/'validation/sms-fire-trace',{3740,3750,3810,3860,3910,3960},[(200,220,0)]+PRESSES+[(3748,3755,8),(3808,3815,8),(3858,3865,8),(3908,3915,8)],core=ROOT.parents[1]/'work/genesis-plus-gx/genesis_plus_gx_libretro.dll',ram_writes=writes)
if __name__=='__main__':main()
