#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "gaw_entity.h"
#include "gaw_host.h"
#include "gaw_player.h"
#include "gaw_ram.h"

static void reset_all(void){ memset(gaw_ram,0,sizeof gaw_ram); gaw_host_set_entropy(0x5A); }

static void test_native_low_entity_handlers(void){
 for(uint8_t t=1;t<=34;++t){ reset_all(); GawEntity *e=gaw_entity(16); e->raw[ENT_TYPE]=t; e->raw[0x11]=0x50;e->raw[0x13]=0x60;gaw_entity(0)->raw[0x11]=0x80;gaw_entity(0)->raw[0x13]=0x80;gaw_ram_write8(0xC037,1);assert(gaw_entity_native_handler(e,t)==1); }
}
static void test_native_hit_recoil(void){
 reset_all(); GawEntity *e=gaw_entity(16),*o=gaw_entity(17); e->raw[ENT_TYPE]=20;e->raw[ENT_FLAGS]=0x28;e->raw[ENT_HP]=20;e->raw[ENT_DEFENSE]=0;e->raw[ENT_PENDING_DAMAGE]=2;e->raw[0x11]=0x50;e->raw[0x13]=0x60;o->raw[ENT_TYPE]=5;o->raw[ENT_DIRECTION]=1;gaw_entity_set16(e,ENT_RELATED_PTR,gaw_entity_addr(o));
 gaw_entity_apply_pending_damage(e); assert(e->raw[ENT_HP]==18); assert(e->raw[0x11]==0x58); assert(e->raw[ENT_HIT_FLASH_TIMER]==0x20);
}
static void test_player_full_heal_action(void){
 reset_all(); GawEntity *p=gaw_entity(0);p->raw[ENT_TYPE]=2;p->raw[ENT_STATE]=1;p->raw[ENT_HP]=5;gaw_ram_write8(0xC0DA,40);gaw_ram_write8(0xC0DF,8);gaw_ram_write8(0xC021,0x20);gaw_player_handler(p);assert(p->raw[ENT_HP]==40);assert(gaw_ram_read8(0xC0DF)==0);
}
static void test_player_transform_action(void){
 reset_all(); GawEntity *p=gaw_entity(0);p->raw[ENT_TYPE]=2;p->raw[ENT_STATE]=1;p->raw[ENT_HP]=10;gaw_ram_write8(0xC0DF,10);gaw_ram_write8(0xC021,0x20);gaw_ram_write8(0xDC12,0x3F);GawEntity *x=gaw_entity(16);x->raw[ENT_TYPE]=20;x->raw[ENT_FLAGS]=0;
 gaw_player_handler(p);assert(gaw_ram_read8(0xDC12)==0x3A);assert(x->raw[ENT_TYPE]==0);assert(gaw_ram_read8(0xC0AC)==1);
}
int main(void){test_native_low_entity_handlers();test_native_hit_recoil();test_player_full_heal_action();test_player_transform_action();puts("phase12 tests: OK");return 0;}
