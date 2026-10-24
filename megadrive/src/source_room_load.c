#include "source_room_load.h"

u8 source_room_load_class0(SourceClock *clock,SourceIrqContext *context,
 const SourceRoomLoadInput *input,SourceRoomLoadData *data,
 SourceRoomLoadOutput *output,SourceGraphicsCheckpoint checkpoint,void *user)
{
 SourceRoomHistoryData history;u16 room;
 if(!output) return 0;
 output->completed=0;
 output->finish.wait_taken=output->finish.error=0;
 output->history.calls=output->history.restored=output->history.last_value=0;
 if(!clock || !context || !context->ram || !input || !data ||
    !input->patterns || !input->bank2 || !input->bank11 || !input->map_bank ||
    !input->bank4 || !input->hud || !data->graphics || !data->map ||
    !data->map->cells || !data->room || !data->flags || !data->objects || !data->masks) return 0;
 if(!source_graphics_load_class0(clock,context,input->patterns,input->bank2,
                                input->bank11,data->graphics,checkpoint,user)) return 0;
 output->completed=1;room=data->room[0]|((u16)data->room[1]<<8);
 if(!source_world_map_load(clock,context,room,input->map_flags,input->map_bank,
                           input->bank2,data->graphics,data->map,checkpoint,user)) return 0;
 output->completed=2;
 if(!source_room_hud_prepare(clock,context,data->graphics,data->map,input->bank4,
                             input->hud,checkpoint,user)) return 0;
 output->completed=3;
 if(!source_room_finish(clock,context,data->graphics,data->map,input->hud,
                        &output->finish,checkpoint,user)) return 0;
 output->completed=4;
 history.room=data->room;history.seed=context->ram+0x28;
 history.history=data->map->cells+0xf0;history.masks=data->masks;
 if(!source_room_actor_prefix(clock,data->flags,data->objects,&history,
                              &output->history,source_irq_interrupt,context)) return 0;
 if(checkpoint && !checkpoint(user,0x1780,clock,context)) return 0;
 output->completed=5;return 1;
}
u8 source_room_load_class0_actors(SourceClock *clock,SourceIrqContext *context,
 const SourceRoomLoadInput *input,SourceRoomLoadData *data,const u8 *bank12,
 SourceActorListData *actors,SourceRoomLoadOutput *output,
 SourceGraphicsCheckpoint checkpoint,void *user)
{
 if(!data || !actors || !bank12 || !data->flags || actors->room!=data->room ||
    actors->masks!=data->masks || actors->active_count!=data->flags+0x12 ||
    !actors->actors || !actors->progression) return 0;
 if(!source_room_load_class0(clock,context,input,data,output,checkpoint,user)) return 0;
 if(!source_actor_list(clock,context,bank12,actors,checkpoint,user)) return 0;
 output->completed=6;return 1;
}
u8 source_room_load_class0_graphics(SourceClock *clock,SourceIrqContext *context,
 const SourceRoomLoadInput *input,SourceRoomLoadData *data,const u8 *rom,
 SourceActorListData *actors,SourceActorGraphicsData *graphics,
 SourceRoomLoadOutput *output,SourceGraphicsCheckpoint checkpoint,void *user)
{
 if(!data || !data->graphics || !actors || !graphics || !rom ||
    graphics->actors!=actors->actors || graphics->patterns!=data->graphics->patterns ||
    graphics->terrain!=data->graphics->terrain || !graphics->allocated) return 0;
 if(!source_room_load_class0_actors(clock,context,input,data,rom+0x30000,actors,output,checkpoint,user)) return 0;
 if(!source_actor_graphics(clock,context,rom,graphics,checkpoint,user)) return 0;
 output->completed=7;return 1;
}
