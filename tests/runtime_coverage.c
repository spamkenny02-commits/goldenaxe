#include <stdio.h>
#include <string.h>
#include "gaw_core.h"
#include "gaw_entity.h"
#include "gaw_platform.h"
#include "gaw_ram.h"
#include "gaw_sms_compat.h"
#include "gaw_tables.h"

/* Registration probe, not an equivalence proof. Use inert, valid states so
   classification cannot start an interactive script or a room transition. */
static void reset_probe(void) {
    memset(gaw_ram,0,sizeof gaw_ram);
    gaw_sms_compat_reset();
    gaw_ram_write16le(0xC060,0xFFFF);
    gaw_ram_write8(0xC073,1); /* inert card-selection phase */
}
int main(void) {
    gaw_platform_init();
    printf("{\"native_entity_types\":[");
    unsigned count=0;
    for(unsigned t=1;t<128u;++t) {
        reset_probe();
        GawEntity *e=gaw_entity(16);
        e->raw[ENT_TYPE]=(uint8_t)t;e->raw[ENT_MOTION_PHASE]=1;
        e->raw[0x11]=0x60;e->raw[0x13]=0x70;
        gaw_ram_write8(RAM_ENTITY_SLOT_INDEX,16);
        if(gaw_entity_native_handler(e,(uint8_t)t))printf("%s%u",count++?",":"",t);
    }
    printf("],\"native_world_targets\":[");count=0;
    for(unsigned i=0;i<512u;++i) {
        uint16_t target=gaw_world_callback_targets[i];
        unsigned j;for(j=0;j<i;++j)if(gaw_world_callback_targets[j]==target)break;
        if(j<i)continue;
        reset_probe();
        if(gaw_world_native_callback(target))printf("%s%u",count++?",":"",target);
    }
    printf("]}\n");
    return 0;
}
