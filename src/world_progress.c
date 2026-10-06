#include <stddef.h>
#include "include/gaw_world_progress.h"
#include "include/gaw_ram.h"

#define R8(a) gaw_ram_read8((a))
#define W8(a,v) gaw_ram_write8((a),(v))

typedef struct {
    uint8_t key;
    uint8_t trigger_cell; /* -> C06E */
    uint8_t target_cell;  /* -> C06F */
    uint8_t patch_type;   /* -> C070 */
} GawWorldEventRecord;

static const GawWorldEventRecord world_events_overworld[] = {
#include "world_events_overworld.inc"
};
static const GawWorldEventRecord world_events_interior[] = {
#include "world_events_interior.inc"
};

static uint8_t progress_mask(uint8_t bit) {
    return bit < 8u ? (uint8_t)(1u << bit) : 0u;
}

/* $1951: choose the persistent byte and the C040-selected bit. */
static uint16_t progress_addr_for_current_layer(void) {
    uint16_t id=gaw_ram_read16le(RAM_WORLD_CELL_ID);
    if (R8(0xC040)==1u) id=gaw_ram_read16le(0xC0BB);
    return (uint16_t)(0xC100u+(uint8_t)id);
}

static bool progress_current_is_set(void) {
    uint8_t mask=progress_mask(R8(0xC040));
    return (R8(progress_addr_for_current_layer()) & mask) != 0;
}

bool gaw_world_progress_is_set(void) { return progress_current_is_set(); }

bool gaw_world_progress_test_and_set(void) {
    uint16_t addr=progress_addr_for_current_layer();
    uint8_t mask=progress_mask(R8(0xC040));
    uint8_t old=R8(addr);
    W8(addr,(uint8_t)(old|mask));
    return (old&mask)!=0;
}

/* Shared body of original $35D4/$1B0E without the $DC00 byte write. */
void gaw_world_commit_metatile(uint8_t cell, uint8_t tile_id) {
    uint16_t src=(uint16_t)(0xC900u+(uint16_t)tile_id*8u);
    uint16_t dst=(uint16_t)(0xD600u+((uint16_t)(cell&0xF0u)<<3)+((uint16_t)(cell&0x0Fu)<<2));
    uint16_t q=gaw_ram_read16le(0xC034);
    if (q>=GAW_RAM_BASE && q<=0xDFFBu) {
        W8(q++,2); W8(q++,2); W8(q++,2); W8(q++,(uint8_t)dst); W8(q++,(uint8_t)(dst>>8));
        gaw_ram_write16le(0xC034,q);
    }
    for (unsigned i=0;i<4;++i) W8((uint16_t)(dst+i),R8((uint16_t)(src+i)));
    for (unsigned i=0;i<4;++i) W8((uint16_t)(dst+0x40u+i),R8((uint16_t)(src+4u+i)));
}

void gaw_world_set_tile(uint8_t cell, uint8_t tile_id) {
    W8((uint16_t)(0xDC00u+cell),tile_id);
    gaw_world_commit_metatile(cell,tile_id);
}

static void patch_vertical_followup(uint8_t target) {
    uint8_t below=(uint8_t)(target+0x10u);
    uint8_t old=R8((uint16_t)(0xDC00u+below));
    static const uint8_t from[4]={0x27,0x28,0x29,0x39};
    static const uint8_t to[4]  ={0x01,0x03,0x00,0x3A};
    for (unsigned i=0;i<4;++i) if (old==from[i]) { gaw_world_set_tile(below,to[i]); return; }
}

/* $1A7C dispatch table ($1A8A), patch types 0..20. */
void gaw_world_progress_apply_patch(uint8_t patch_type, uint8_t target) {
    uint8_t trigger=R8(0xC06E);
    switch (patch_type) {
        case 0:
            gaw_world_set_tile(target,0x00); patch_vertical_followup(target); break;
        case 1:
            gaw_world_set_tile(trigger,target); patch_vertical_followup(trigger); break;
        case 2:
            gaw_world_set_tile(target,0x15); patch_vertical_followup(target); break;
        case 3:
            gaw_world_set_tile(target,0x03); patch_vertical_followup(target); break;
        case 4:
            gaw_world_set_tile(target,0x04); patch_vertical_followup(target); break;
        case 5:
            gaw_world_set_tile(target,0x01); gaw_world_set_tile((uint8_t)(target+0x10u),0x01); break;
        case 6:
            W8(0xDC30,0x30); W8(0xDC40,0x31); W8(0xDC50,0x1F); break;
        case 7:
            gaw_world_set_tile(target,0x04); gaw_world_set_tile((uint8_t)(target+0x10u),0x01); break;
        case 8:
            gaw_world_set_tile(target,0x08); gaw_world_set_tile((uint8_t)(target+1u),0x08); break;
        case 9:
            gaw_world_set_tile(target,0x4D); break;
        case 10:
            gaw_world_set_tile(target,0x4C); break;
        case 11:
            gaw_world_set_tile(target,0x09);
            gaw_world_set_tile((uint8_t)(target+0x10u),0x06);
            gaw_world_set_tile(0x1B,0x4D);
            break;
        case 12:
            for (unsigned i=0;i<4;++i) gaw_world_set_tile((uint8_t)(target+i),0x00);
            break;
        case 13:
            gaw_world_set_tile(target,0x0C); break;
        case 14:
            gaw_world_set_tile(target,0x00); break;
        case 15:
            gaw_world_set_tile(target,0x09); gaw_world_set_tile(trigger,0x09); break;
        case 16:
            gaw_world_set_tile(target,0x00); gaw_world_set_tile((uint8_t)(target+1u),0x00);
            gaw_world_set_tile((uint8_t)(target+0x10u),0x00); gaw_world_set_tile((uint8_t)(target+0x11u),0x00);
            gaw_world_set_tile(trigger,0x4D);
            break;
        case 17:
            gaw_world_set_tile(target,0x08); gaw_world_set_tile((uint8_t)(target+1u),0x08);
            gaw_world_set_tile(trigger,0x4D);
            break;
        case 18:
            gaw_world_set_tile(target,0x08); gaw_world_set_tile((uint8_t)(target+1u),0x08);
            gaw_world_set_tile(trigger,0x00);
            break;
        case 19:
            gaw_world_set_tile(target,0x09); gaw_world_set_tile(trigger,0x4D); break;
        case 20:
            W8(0xDC4A,0x0A); W8(0xDC5A,0x6B); break;
        default:
            break;
    }
}

void gaw_world_progress_apply_loaded_patch(void) {
    gaw_world_progress_apply_patch(R8(0xC070),R8(0xC06F));
}

bool gaw_world_progress_load_event_record(void) {
    uint16_t id=gaw_ram_read16le(RAM_WORLD_CELL_ID);
    const GawWorldEventRecord *tab=(id>>8)==0 ? world_events_overworld : world_events_interior;
    uint8_t key=(uint8_t)id;
    for (size_t i=0;tab[i].key!=0;++i) {
        if (tab[i].key==key) {
            W8(0xC06E,tab[i].trigger_cell); W8(0xC06F,tab[i].target_cell); W8(0xC070,tab[i].patch_type);
            return true;
        }
    }
    W8(0xC06E,0xFF); W8(0xC06F,0xFF); W8(0xC070,0x00);
    return false;
}

/* $194C/$1947 helpers used by $1BCD operate on C100 + low(C0B9) and an
   explicit bit number, independent of C040. */
static bool explicit_progress_is_set(uint8_t bit) {
    uint16_t addr=(uint16_t)(0xC100u+(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID));
    return (R8(addr)&progress_mask(bit))!=0;
}
static void explicit_progress_set(uint8_t bit) {
    uint16_t addr=(uint16_t)(0xC100u+(uint8_t)gaw_ram_read16le(RAM_WORLD_CELL_ID));
    W8(addr,(uint8_t)(R8(addr)|progress_mask(bit)));
}

static void restore_auxiliary_bits_1bcd(void) {
    if (R8(0xC0BA)==0) return;
    explicit_progress_set(4);
    if (explicit_progress_is_set(5)) { W8(0xDC17,0); W8(0xDC18,0); }
    if (explicit_progress_is_set(6)) { W8(0xDC31,0x18); W8(0xDC41,0); W8(0xDC51,0x19); }
    if (explicit_progress_is_set(7)) { W8(0xDC3E,0x22); W8(0xDC4E,0); W8(0xDC5E,0x23); }
}

/* Native gameplay-visible portion of $1976. It restores already-earned
   persistent changes when entering/rebuilding a world cell. */
void gaw_world_progress_restore_for_current_cell(void) {
    restore_auxiliary_bits_1bcd();
    (void)gaw_world_progress_load_event_record();
    if (progress_current_is_set()) gaw_world_progress_apply_loaded_patch();
    W8(0xDD00,0);

    /* $19C6-$1A01: environment-5 chain restoration. */
    if (R8(0xC0BA)==0 && R8(RAM_PLAYER_ENV_MODE)==5) {
        uint8_t row=(uint8_t)(R8(0xC313)&0xF0u);
        uint8_t cell=(uint8_t)(row>>4);
        uint8_t dir=R8(0xC30A);
        if (dir==0) {
            cell=(uint8_t)(cell+0x90u);
            while (R8((uint16_t)(0xDC00u+cell))==0x0C) {
                W8((uint16_t)(0xDC00u+cell),0x6C);
                cell=(uint8_t)(cell-0x10u);
            }
        } else {
            while (R8((uint16_t)(0xDC00u+cell))==0x0C) {
                W8((uint16_t)(0xDC00u+cell),0x6C);
                cell=(uint8_t)(cell+0x10u);
            }
            W8((uint16_t)(0xDC00u+cell),0x6D);
        }
    }
}
