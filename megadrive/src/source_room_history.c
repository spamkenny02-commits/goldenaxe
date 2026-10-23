#include "source_room_history.h"
static u8 contains(const u8 *values,u8 count,u8 value)
{
    u8 i;for(i=0;i<count;i++) if(values[i]==value) return 1;
    return 0;
}
u8 source_room_history(u16 room,u8 *history,u8 *masks,SourceRoomDraw draw,void *context)
{
    static const u8 exceptions[6]={0x1e,0x5e,0x9c,0xb8,0xbe,0xc9};
    u8 dungeon=(room>>8)!=0,length=dungeon?4:16,attempts=dungeon?5:3;
    u8 i,j,value,restored=0;
    for(i=0;i<attempts;i++)
    {
        if(!contains(history,length,(u8)room))
        {
            for(j=length-1;j;j--) history[j]=history[j-1];
            history[0]=(u8)room;
        }
        value=draw(context);
        if(contains(history,length,value)) continue;
        if(dungeon && contains(exceptions,6,value)) continue;
        if(!masks[value]) { masks[value]=255;restored++; }
    }
    return restored;
}
