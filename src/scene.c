#include <string.h>
#include "include/gaw_assets.h"
#include "include/gaw_ram.h"
#include "include/gaw_video.h"
#include "include/gaw_platform.h"
#include "include/gaw_world_progress.h"

static uint8_t byte(uint8_t bank,uint16_t a){return a>=0xC000u?gaw_ram_read8((uint16_t)(0xC000u+(a&0x1FFFu))):gaw_sms_rom_bank_read(a<0x4000u?0u:a<0x8000u?1u:bank,a);}
static uint16_t word(uint8_t bank,uint16_t a){return (uint16_t)(byte(bank,a)|((uint16_t)byte(bank,(uint16_t)(a+1u))<<8));}
/* $0C00: byte RLE with interleaved destination lanes. */
uint16_t gaw_assets_unpack_ram(uint8_t bank,uint16_t source,uint16_t destination,uint8_t lanes){
    unsigned count_lanes=lanes?lanes:256u;
    for(unsigned lane=0;lane<count_lanes;++lane){
        uint16_t dst=(uint16_t)(destination+lane);
        for(;;){
            uint8_t command=byte(bank,source++);if(!command)break;
            unsigned count=command&0x7Fu;if(!count)count=256u;
            uint8_t value=0;if(!(command&0x80u))value=byte(bank,source++);
            while(count--){
                if(command&0x80u)value=byte(bank,source++);
                gaw_ram_write8((uint16_t)(0xC000u+(dst&0x1FFFu)),value);dst=(uint16_t)(dst+lanes);
            }
        }
    }
    return source;
}
/* $0BD3 expands incrementing runs into D100, then decodes that temporary
   stream as two descriptor lanes into the caller's destination. */
uint16_t gaw_assets_unpack_descriptors(uint8_t bank,uint16_t source,uint16_t destination){
    uint16_t dst=0xD100u;
    for(;;){
        uint8_t command=byte(bank,source++);if(!command)break;
        unsigned count=command&0x7Fu;if(!count)count=256u;
        uint8_t value=0;if(!(command&0x80u))value=byte(bank,source++);
        while(count--){if(command&0x80u)value=byte(bank,source++);gaw_ram_write8((uint16_t)(0xC000u+(dst++&0x1FFFu)),value);if(!(command&0x80u))++value;}
    }
    (void)gaw_assets_unpack_ram(bank,0xD100u,destination,2);return source;
}
/* $1A30 preserves two different eight-byte records when the gate is open. */
static void restore_gate_records(void){
    if(gaw_ram_read8(0xC040u)!=0)return;
    if(gaw_ram_read8(0xC0ACu)==0){
        memcpy(gaw_ram_ptr(0xCAC0),gaw_ram_ptr(0xC998),8);
        memcpy(gaw_ram_ptr(0xCAF0),gaw_ram_ptr(0xC998),8);
    }else{
        memcpy(gaw_ram_ptr(0xCAC0),gaw_ram_ptr(0xC080),8);
        memcpy(gaw_ram_ptr(0xCAF0),gaw_ram_ptr(0xC088),8);
        uint8_t cell=gaw_ram_read8(0xC0B9u);
        if(cell==0x96u||cell==0xAAu||cell==0xCBu){(void)gaw_world_progress_test_and_set();gaw_world_progress_restore_for_current_cell();}
    }
}
/* $BE78: interior palette selection and the C072 encounter marker. */
static void interior_palette(void){
    if(gaw_ram_read8(0xC0BAu)==0)return;
    uint8_t enabled=0,cell=gaw_ram_read8(0xC0B9u);
    for(unsigned i=0;i<0x26u;++i)if(byte(5,(uint16_t)(0xBF68u+i))==cell){enabled=1;break;}
    if(gaw_ram_read8(0xC0ADu))enabled=0;
    gaw_ram_write8(0xC072u,enabled);
    uint8_t offset=enabled?0:(uint8_t)(gaw_ram_read8(0xC037u)<<4);
    for(unsigned i=0;i<16u;++i)gaw_ram_write8((uint16_t)(0xDCA0u+i),byte(5,(uint16_t)(0xBEB8u+offset+i)));
}
/* $81C0: selected metatile records with lane-specific attributes. */
static void auxiliary_metatiles(void){
    uint16_t source=word(2,(uint16_t)(0x8259u+2u*gaw_ram_read8(0xC040u))),dst=0xCD00u;
    uint8_t count=0;
    for(uint8_t tile=byte(2,source++);!(tile&0x80u);tile=byte(2,source++)){
        for(unsigned i=0;i<8u;++i)gaw_ram_write8(dst++,gaw_ram_read8((uint16_t)(0xC900u+tile*8u+i)));
        ++count;
    }
    dst=0xCD01u;count=(uint8_t)(count<<2);
    for(;;){--count;if(count&0x80u)break;gaw_ram_write8(dst,(uint8_t)((gaw_ram_read8(dst)&0x1Fu)|byte(2,source++)));dst=(uint16_t)(dst+2u);}
}
/* $16EF: graphics, metatile tables, palette and SRAM animation workspace. */
void gaw_assets_restore_scene(void){
    uint8_t bank=gaw_ram_read8(0xC066u);
    for(unsigned i=0;i<16u;++i)gaw_ram_write8((uint16_t)(0xDCA0u+i),byte(bank,(uint16_t)(0x8000u+i)));
    uint16_t source=gaw_assets_unpack_tiles(bank,0x8010u,0x4000u);
    (void)gaw_assets_unpack_ram(bank,source,0xC900u,2);
    memcpy(gaw_ram_ptr(0xC080),gaw_ram_ptr(0xCAC0),8);
    memcpy(gaw_ram_ptr(0xC088),gaw_ram_ptr(0xCAF0),8);
    restore_gate_records();interior_palette();auxiliary_metatiles();
    source=word(0,(uint16_t)(0x1759u+2u*gaw_ram_read8(0xC040u)));
    (void)gaw_assets_unpack_ram(11,source,0xD100u,4);
    uint16_t page=(gaw_ram_read8(0xDFFCu)&4u)?0x4000u:0u;
    for(unsigned i=0;i<0x400u;++i)gaw_platform_sram_write((uint16_t)(page+0x1000u+i),gaw_ram_read8((uint16_t)(0xD100u+i)));
}
