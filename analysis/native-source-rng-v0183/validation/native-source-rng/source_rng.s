#NO_APP
	.file	"source_rng.c"
	.text
	.align	2
	.globl	source_rng_next_seed
	.type	source_rng_next_seed, @function
source_rng_next_seed:
	move.l %d2,-(%sp)
	move.l 8(%sp),%d0
	move.w %d0,%d2
	lsr.w #8,%d2
	move.b %d2,%d1
	ror.b #2,%d1
	eor.b %d2,%d1
	ror.b #1,%d1
	eor.b %d0,%d1
	ror.b #4,%d1
	eor.b %d0,%d1
	and.w #1,%d1
	add.w %d0,%d0
	add.w %d1,%d0
	jeq .L6
	move.l (%sp)+,%d2
	rts
.L6:
	move.w #29500,%d0
	move.l (%sp)+,%d2
	rts
	.size	source_rng_next_seed, .-source_rng_next_seed
	.align	2
	.globl	source_rng_value
	.type	source_rng_value, @function
source_rng_value:
	move.b 7(%sp),%d0
	move.b 11(%sp),%d1
	eor.b %d1,%d0
	rts
	.size	source_rng_value, .-source_rng_value
	.align	2
	.globl	source_refresh_advance
	.type	source_refresh_advance, @function
source_refresh_advance:
	move.l 4(%sp),%d1
	move.b 11(%sp),%d0
	add.b %d1,%d0
	and.b #127,%d0
	and.b #-128,%d1
	or.b %d1,%d0
	rts
	.size	source_refresh_advance, .-source_refresh_advance
	.ident	"GCC: (crosstool-NG UNKNOWN) 13.2.0"
