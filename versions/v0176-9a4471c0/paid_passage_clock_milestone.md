# v0176: paid-exit loading clock

The native paid-exit path formerly advanced world_clock on every video interrupt
spent decoding/converting/uploading its destination. The SMS16D0..1FA7 loader
advances C02F only once: its1DE2/229C wait. Audio-only interrupts continue while
the game clock is stopped (0137,C02E gate;01E3 alternate path).

Twenty-four actual unpatched source exits prove this across six routes,empty/full
enemy persistence masks and PAL/NTSC. They retain real room loading and RNG;
only entrance/hero/initial clock and pre-entry persistence fixtures are controlled.
Timing events and profiles are retained under validation/paid-passage-clocks.

Production now wraps the paid passage's load_house_room call. It measures vtimer
elapsed and adds elapsed-minus-one to world_clock_shift. This preserves a single
logical tick,including8-bit wrap,while retaining audio interrupts and all loading
work. The existing sprite palette restoration then reads the corrected clock.
Other house/dungeon loading callers are unchanged.

Validation:3072 compiled native full-loader cases (six destinations,all256 masks,
both regions;initial clock sweeps0..255),18528 source/native rule cases and20
controlled actual payment/exit/poor/refusal/menu scenarios. The dedicated harness
uses every production source file byte-identically and executes actual decoding,
conversion,enemy resource loading and VDP publication. It does not stub the loader.

Additional source research:original0397 word-fill cost passes2064 cases,including
all counts0..1024 and larger chunk boundaries in both regions. BC0000 retains
65536-word behavior. Live1FA7 clear prefix is51628 foreground T states,matching
both regions;it crosses two observed NTSC frame boundaries versus one PAL.

Limits:physical loading remains too short on some routes. This correction does
not add a fixed frame delay,solve source IRQ alignment,adjust reveal/contour timing,
align earlier dialogue clocks or implement the source refresh-register RNG. Native
natural spawns/combat and full progression remain unproved. Current checks establish
the paid-loader logical clock rule,not whole-transition or full-port fidelity.

Next combine validated graphics/map/HUD/actor costs with24C5 orchestration and
reveal phases,subtract actual native work and verify physical transition timing.
