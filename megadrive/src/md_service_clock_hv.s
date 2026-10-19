    .text
    .align 2
    .global md_service_clock_hv
md_service_clock_hv:
    move.w 0xc00008,%d0
    rts
