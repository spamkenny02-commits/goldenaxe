#include "source_sprite_scene_cost.h"
#define GAW_SCENE_COST_ONLY
#define source_sprite_scene_timed source_sprite_scene_count_inner
#include "source_sprite_scene_timed.c"
#undef source_sprite_scene_timed
u8 source_sprite_scene_cost(u8 *ram,const u8 *bank,const u8 *low,
 SourceClockWork *work,SourceSpriteSceneOutput *output)
{
 SourceClock clock;
 if(!ram || !bank || !low || !work || !output) return 0;
 clock.foreground_tstates=clock.foreground_m1=0;
 if(!source_sprite_scene_count_inner(&clock,ram,bank,output,0,0,0,(void *)low)) return 0;
 work->tstates=clock.foreground_tstates;work->fetches=clock.foreground_m1;return 1;
}
