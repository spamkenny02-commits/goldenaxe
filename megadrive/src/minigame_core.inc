/* Original6719/67CA/680A/68C7. Callers supply the random byte explicitly. */
extern const u8 minigame_weights[],minigame_pairs[],minigame_inverse[],minigame_lucky[],minigame_scores[],minigame_coordinates[];
static u16 minigame_stage;
static u16 minigame_reward_count,minigame_reward_steps,minigame_reward_pc;
static s16 minigame_reward_delta;
static u16 minigame_select(u16 coordinate,u8 flags,const u8 *cells)
{
    u16 n;
    if((flags&0x77)!=0x14 || coordinate>>8!=2) return 65535;
    for(n=0;n<10;n++) if((coordinate&255)==minigame_coordinates[n] && cells[0x33+n]==0x3a) return 0x33+n;
    return 65535;
}
static bool minigame_draw(u8 *cells,u16 cell,u8 roll)
{
    u16 kind=minigame_weights[roll&31],slot;
    u8 top=minigame_pairs[kind*2],bottom=minigame_pairs[kind*2+1];
    if(kind>=4 && cells[12]) return FALSE; /* 675B retries the RNG. */
    cells[cell]=top;
    if(kind>=4) { cells[12]=top;cells[13]=bottom;return TRUE; }
    slot=cells[3]==0x3a?3:cells[6]==0x3a?6:9;
    cells[slot]=top;cells[slot+1]=bottom;
    if(slot==9) minigame_stage++;
    return TRUE;
}
static bool minigame_flip(u8 *cells,u16 cell)
{
    const u8 *table=cells[12]==0x38?minigame_lucky:minigame_inverse;
    u16 n;u8 old=cells[cell];
    for(n=0;n<(cells[12]==0x38?8:16);n+=2) if(old==table[n]) { cells[cell]=table[n+1];break; }
    return old!=cells[cell];
}
static void minigame_prepare_reward(u16 gold,const u8 *cells)
{
    u16 n;u8 sum=0; s16 amount;
    for(n=3;n<=9;n+=3) sum+=minigame_scores[cells[n]-0x34];
    amount=(s8)sum;minigame_reward_delta=amount<0?-1:1;
    minigame_reward_pc=amount<0?0xb982:0xb95f;
    minigame_reward_count=amount<0?min((u16)-amount,gold):min((u16)amount,255-gold);
    /* 683E POP BC then DJNZ: positive zero wraps B and runs256 increments. */
    minigame_reward_steps=minigame_reward_count?minigame_reward_count:amount<0?0:256;
}
