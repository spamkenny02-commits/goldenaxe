#include "pattern_convert.h"
#include "pattern_pair_lut.inc"
#ifdef SGDK_GCC
/* Character writes to the SMS mirror may alias these aligned word reads. */
typedef u16 __attribute__((may_alias)) PlanePair;
#endif
void pattern_convert(const u8 *source,u32 *destination,u16 rows)
{
#ifdef SGDK_GCC
    const PlanePair *planes=(const PlanePair *)source;
    while(rows--)
    {
        *destination++=pattern_pairs[planes[0]]|(pattern_pairs[planes[1]]<<2);
        planes+=2;
    }
#else
    while(rows--)
    {
        u16 low=((u16)source[0]<<8)|source[1],high=((u16)source[2]<<8)|source[3];
        *destination++=pattern_pairs[low]|(pattern_pairs[high]<<2);source+=4;
    }
#endif
}
