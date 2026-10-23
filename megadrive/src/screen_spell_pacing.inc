/* Foreground work from6B33/6C65,6E3F/044E and0938; IRQs remain separate. */
#include "source_sprite_scene_cost.h"
#include "source_irq.h"
static inline u16 screen_spell_product(u16 a,u16 b)
{
#ifdef SGDK_GCC
    u32 result=a;__asm__("mulu.w %1,%0" : "+d"(result) : "d"(b) : "cc");return result;
#else
    return (u16)(a*b);
#endif
}
static u32 screen_spell_map_cost(u8 *work,u16 level)
{
    u32 total=16;u16 n;
    if(level==1) for(n=0;n<22;n++)
    {
        u8 *e=work+n*32;
        if(!e[0]) {total+=94;continue;}
        total+=624+(e[1]<14?58:0);
        if(e[1]==21) total+=e[4]==2?89:75;
    }
    else for(n=0;n<4;n++)
    {
        u8 *e=work+n*32;const u8 *b=screen_spell_blocks+e[2]*6;
        u16 address=(b[0]|((u16)b[1]<<8))+e[1];
        total+=253+screen_spell_product(b[4],75+48*b[5])-5+133+48;
        total-=((address&255)+b[4]*64)>>8;
        if(e[2]==9) total+=37;
    }
    return total;
}
static u16 screen_spell_multiply_cost(s16 sample,u16 amplitude,bool cosine)
{
    return screen_spell_multiply_tstates[amplitude-16]+(cosine?7:0)-(sample<0?1:0);
}
static u16 screen_spell_orbit_cost(u16 phase,u16 clock)
{
    u16 amplitude=16+((clock&8)?8-(clock&7):clock&7);
    u16 index=(amplitude-16)<<8;
    s16 sx=(s8)screen_spell_offsets[index+((phase+64)&255)],sy=(s8)screen_spell_offsets[index+phase];
    s16 dx=sx,x=(hero_x>>8)+dx;
    u16 total=19+4+5+10+7+7+12+((clock&8)?22:12)+7+4+23+19+17;
    total+=screen_spell_multiply_cost(sx,amplitude,TRUE)+13+4+19+8+(dx<0?11:12);
    if(x<0 || x>=256) total+=12;
    else
    {
        total+=7+7+7;
        if(x<4 || x>=252) total+=12;
        else total+=7+19+17+screen_spell_multiply_cost(sy,amplitude,FALSE)+13+4+7+19+23;
    }
    return total+19+7+19+13+7+7+19+10;
}
static u32 screen_spell_irq_cost(void)
{
    u16 index=(SYS_isPAL()?2:0)+(sound_ram[3]?1:0);
    return screen_spell_irq_empty_fixed[index]+sound_source_work.tstates;
}
static u32 screen_spell_sprite_cost(u8 *phases,bool particles,u16 level)
{
    /* Converted effect patterns are already in MD VRAM. Reuse their8KiB
     * software area as private source RAM; preserve its upper4KiB in the
     * modal union until the class background is reloaded. */
    u8 *ram=sms_vram,*hero=ram+0x300;u16 n,clock=screen_spell_clock;
    SourceSpriteSceneOutput scene;u32 scene_tstates,total=16+10;
    if(!screen_spell_iteration) {memset(ram,0,0x900);memcpy(ram+0x600,world_actor_state,768);}
    ram[0x2f]=clock;ram[0x47]=world_object_tick_count;
    ram[0x1b]=world_sms_sprite_overflow?0xc0:0x80;
    hero[0]=1;hero[2]=0xf0;hero[3]=hero_flags|1;hero[8]=0xa0;hero[9]=0x80;
    hero[10]=hero_direction;hero[11]=hero_animation;hero[0x11]=hero_y>>8;hero[0x13]=hero_x>>8;
    if(!particles) memset(ram+0x330,0,384);
    for(n=0;n<8;n++)
    {
        u8 *e=ram+0x330+n*48;u16 phase=phases[n];
        total+=76+(particles?screen_spell_orbit_cost(phase,clock):34);
        if(particles)
        {
            u16 amplitude=16+((clock&8)?8-(clock&7):clock&7);
            u16 index=(amplitude-16)<<8;
            s16 dx=(s8)screen_spell_offsets[index+((phase+64)&255)];
            s16 dy=(s8)screen_spell_offsets[index+phase];
            s16 x=(hero_x>>8)+dx;
            e[0]=1;e[2]=0xf4+(clock&1);e[3]=(x>=4 && x<252)?1:0;
            e[8]=0xae;e[9]=0x6e;e[0x13]=x;e[0x11]=((hero_y>>8)+dy-6)&255;
        }
    }
    if(source_sprite_scene_tstates(ram,screen_spell_bank12,sound_low_rom,&scene_tstates,&scene)) {total+=scene_tstates;screen_spell_sprite_count=scene.count;hero_flags|=1;
        for(n=0;n<16;n++) {world_actor_state[n*48+0x1b]=ram[0x600+n*48+0x1b];world_actor_state[n*48+0x1c]=ram[0x600+n*48+0x1c];}}
    else screen_spell_pacing_error=1;
    if(level==1) total+=13+4+(particles?10:17+8088)+17+17;
    else total+=17+13+7+7+((clock&3)?11:12)+13+17;
    return total;
}
