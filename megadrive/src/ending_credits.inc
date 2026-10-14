/* Native source7061 row writer and7027 fractional scrolling.
 * Used by the production ending scene and compared directly with original
 * routines in the standalone credits harness. */
extern const u8 ending_text[],ending_credit_glyphs[];
typedef struct {
    u8 wait,done;
    u16 scroll,row,text;
    u8 vscroll;
} EndingCredits;
static void ending_credit_row(EndingCredits *state,u8 *line)
{
    u16 n,out=2;u8 wait=state->wait-1;
    for(n=0;n<64;n+=2) { line[n]=255;line[n+1]=8; }
    if(wait&128)
    {
        while(TRUE)
        {
            u8 value=ending_text[state->text++];
            if(!value) { state->done=1;wait=255;break; }
            if(value&128) { wait=-value;break; }
            for(n=80;n;n--) if(ending_credit_glyphs[n-1]==value) break;
            if(out<64) line[out]=0xb0+(n?n-1:0);
            out+=2;
        }
    }
    state->wait=wait;
    state->row+=64;if(state->row>=0x7f00) state->row=0x7800;
}
static bool ending_credit_tick(EndingCredits *state,u8 *line)
{
    u16 old=state->scroll;u16 advance;
    state->scroll+=48;
    advance=(u8)((state->scroll>>8)-(old>>8));
    state->vscroll+=advance;if(state->vscroll>=224) state->vscroll=0;
    if((state->scroll^old)&0x800) { ending_credit_row(state,line);return TRUE; }
    return FALSE;
}
