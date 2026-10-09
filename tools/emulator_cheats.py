"""Explicit diagnostic assistance, separate from controller-only proofs."""


class FinalBossHpCheat:
    """Refill living hero HP only while the real final boss is present."""

    def __init__(self, enabled=False):
        self.report={'enabled':enabled,'kind':'final_boss_hp_refill',
                     'scope_cell':0x14C,'address':'C318','events':[]}

    def apply(self, frame, read, restore_hp):
        if not self.report['enabled']:return False
        cell=read(0xC0B9)|(read(0xC0BA)<<8)
        hp,maximum=read(0xC318),read(0xC0DA)
        if read(0xC01D)!=0x0C or cell!=0x14C or read(0xC600)!=109 or not 0<hp<maximum:
            return False
        restore_hp(maximum)
        self.report['events'].append({'emulator_frame':frame,'cell':cell,
                                     'before':hp,'after':maximum})
        return True
