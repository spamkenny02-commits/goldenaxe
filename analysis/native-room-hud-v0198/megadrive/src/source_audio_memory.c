#include "source_audio_memory.h"
u8 source_audio_read(const u8 *state,const u8 *low,u16 low_bytes,const u8 *bank,
                     u16 address,u8 *value)
{
    u16 offset;
    if(address<low_bytes) *value=low[address];
    else if(address>=0x8000 && address<0xc000) *value=bank[address-0x8000];
    else if(address>=0xc000)
    {
        offset=address&0x1fff;
        if(offset<0x1e00 || offset>=0x1f90) return 0;
        *value=state[offset-0x1e00];
    }
    else return 0;
    return 1;
}
