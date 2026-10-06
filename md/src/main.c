#include "gaw_core.h"
#include "gaw_ram.h"
void md_main(void){gaw_reset();for(;;)gaw_dispatch_state_once();}
