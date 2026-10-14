"""Instruction-derived 2279/22E2 work, plus bounded HUD/metadata allowance."""
import json
from run_core import ROOT


def room_map_cost():
    # 2279 saves registers, initializes HL/C, then restores them and returns.
    total=4*11+10+7+4*10+10
    lookup_prefix=sum([11,4,8,4,7,4,4,4,4,4,7,10,11,7,4,11,11,11,10])
    lookup_tail=sum([11,7,6,7,10,10])
    for y in range(20):
        total+=7
        for x in range(32):
            lookup=lookup_prefix+8+(15 if y&1 else 12)+8+(15 if x&1 else 12)+lookup_tail
            total+=17+lookup+sum([7,6,7,6,4,4,7])+(12 if x<31 else 7)
        total+=4+4+7+(12 if y<19 else 7)
    return total


def main():
    cycles=room_map_cost();assert cycles==192686
    # Profiles separately verify the fixed map loop. HUD and 1976 vary with
    # stats/room flags; these rounded allowances are not claimed cycle exact.
    prepare=cycles+32000+5000
    (ROOT/'megadrive/src/key_redraw_cost.inc').write_text(
        '/* Generated from original Z80 map loops; no emulator state. */\n'
        f'#define WORLD_ROOM_REBUILD_TSTATES {cycles}UL\n'
        f'#define WORLD_REDRAW_PREPARE_TSTATES {prepare}UL\n')
    report=dict(map_rebuild_tstates=cycles,hud_allowance_tstates=32000,metadata_allowance_tstates=5000,
                prepare_tstates=prepare,source_map_loop_cycle_exact=True,hud_and_irq_phase_cycle_exact=False)
    (ROOT/'analysis/key_redraw_cost_model.json').write_text(json.dumps(report,indent=2)+'\n')
    print('2279/22E2:',cycles,'T; preparation budget:',prepare,'T')


if __name__=='__main__':main()
