; ROM bank 06; file offset $18000; CPU window $8000
; Fixed-window static reachability plus optional bank-aware execution observations.
; DB = unclassified data/code. No claim of complete decompilation.
    org $8000
    LD HL,$de0a                    ; ROM 18000: 210ade
    LD A,(HL)                      ; ROM 18003: 7e
    OR A                           ; ROM 18004: b7
    JR z,$800c                     ; ROM 18005: 2805
    db $F0,$35,$C3,$02,$84 ; ROM 18007
    CALL $8097                     ; ROM 1800C: cd9780
    CALL $807e                     ; ROM 1800F: cd7e80
    CALL $80c8                     ; ROM 18012: cdc880
    CALL $80ff                     ; ROM 18015: cdff80
    CALL $81f8                     ; ROM 18018: cdf881
    LD A,($de03)                   ; ROM 1801B: 3a03de
    OR A                           ; ROM 1801E: b7
    JP z,$8030                     ; ROM 1801F: ca3080
    LD A,($de04)                   ; ROM 18022: 3a04de
    INC A                          ; ROM 18025: 3c
    CP 6                           ; ROM 18026: fe06
    JR c,$802b                     ; ROM 18028: 3801
    XOR A                          ; ROM 1802A: af
    OR A                           ; ROM 1802B: b7
    LD ($de04),A                   ; ROM 1802C: 3204de
    RET z                          ; ROM 1802F: c8
    LD IX,$de40                    ; ROM 18030: dd2140de
    BIT 7,(IX)                     ; ROM 18034: ddcb007e
    CALL nz,$84c7                  ; ROM 18038: c4c784
    LD IX,$de70                    ; ROM 1803B: dd2170de
    BIT 7,(IX)                     ; ROM 1803F: ddcb007e
    CALL nz,$84c7                  ; ROM 18043: c4c784
    LD IX,$dea0                    ; ROM 18046: dd21a0de
    BIT 7,(IX)                     ; ROM 1804A: ddcb007e
    CALL nz,$84c7                  ; ROM 1804E: c4c784
    LD IX,$ded0                    ; ROM 18051: dd21d0de
    BIT 7,(IX)                     ; ROM 18055: ddcb007e
    CALL nz,$864f                  ; ROM 18059: c44f86
    LD IX,$df00                    ; ROM 1805C: dd2100df
    BIT 7,(IX)                     ; ROM 18060: ddcb007e
    CALL nz,$84c7                  ; ROM 18064: c4c784
    LD IX,$df30                    ; ROM 18067: dd2130df
    BIT 7,(IX)                     ; ROM 1806B: ddcb007e
    CALL nz,$84c7                  ; ROM 1806F: c4c784
    LD IX,$df60                    ; ROM 18072: dd2160df
    BIT 7,(IX)                     ; ROM 18076: ddcb007e
    CALL nz,$84c7                  ; ROM 1807A: c4c784
    RET                            ; ROM 1807D: c9
    LD HL,$de01                    ; ROM 1807E: 2101de
    LD A,(HL)                      ; ROM 18081: 7e
    OR A                           ; ROM 18082: b7
    RET z                          ; ROM 18083: c8
    DEC (HL)                       ; ROM 18084: 35
    RET nz                         ; ROM 18085: c0
    LD A,($de02)                   ; ROM 18086: 3a02de
    LD (HL),A                      ; ROM 18089: 77
    LD HL,$de4a                    ; ROM 1808A: 214ade
    LD DE,$30                      ; ROM 1808D: 113000
    LD B,4                         ; ROM 18090: 0604
    INC (HL)                       ; ROM 18092: 34
    ADD HL,DE                      ; ROM 18093: 19
    DJNZ $8092                     ; ROM 18094: 10fc
    RET                            ; ROM 18096: c9
    LD DE,$de06                    ; ROM 18097: 1106de
    LD IX,$de11                    ; ROM 1809A: dd2111de
    LD IY,$de05                    ; ROM 1809E: fd2105de
    CALL $80a8                     ; ROM 180A2: cda880
    CALL $80a8                     ; ROM 180A5: cda880
    LD A,(DE)                      ; ROM 180A8: 1a
    AND $7f                        ; ROM 180A9: e67f
    JR z,$80c4                     ; ROM 180AB: 2817
    DEC A                          ; ROM 180AD: 3d
    LD HL,$8ad5                    ; ROM 180AE: 21d58a
    LD C,A                         ; ROM 180B1: 4f
    LD B,0                         ; ROM 180B2: 0600
    ADD HL,BC                      ; ROM 180B4: 09
    LD A,(HL)                      ; ROM 180B5: 7e
    CP (IX)                        ; ROM 180B6: ddbe00
    JR c,$80c4                     ; ROM 180B9: 3809
    AND $7f                        ; ROM 180BB: e67f
    LD (IX),A                      ; ROM 180BD: dd7700
    LD A,(DE)                      ; ROM 180C0: 1a
    LD (IY),A                      ; ROM 180C1: fd7700
    XOR A                          ; ROM 180C4: af
    LD (DE),A                      ; ROM 180C5: 12
    INC DE                         ; ROM 180C6: 13
    RET                            ; ROM 180C7: c9
    LD A,($de0b)                   ; ROM 180C8: 3a0bde
    OR A                           ; ROM 180CB: b7
    RET z                          ; ROM 180CC: c8
    LD A,($de0c)                   ; ROM 180CD: 3a0cde
    DEC A                          ; ROM 180D0: 3d
    JR z,$80d7                     ; ROM 180D1: 2804
    LD ($de0c),A                   ; ROM 180D3: 320cde
    RET                            ; ROM 180D6: c9
    LD A,($de0d)                   ; ROM 180D7: 3a0dde
    LD ($de0c),A                   ; ROM 180DA: 320cde
    LD A,($de0b)                   ; ROM 180DD: 3a0bde
    DEC A                          ; ROM 180E0: 3d
    LD ($de0b),A                   ; ROM 180E1: 320bde
    JP z,$83ef                     ; ROM 180E4: caef83
    LD HL,$de48                    ; ROM 180E7: 2148de
    LD DE,$30                      ; ROM 180EA: 113000
    LD B,3                         ; ROM 180ED: 0603
    CALL $80f8                     ; ROM 180EF: cdf880
    ADD HL,DE                      ; ROM 180F2: 19
    DJNZ $80ef                     ; ROM 180F3: 10fa
    LD HL,$de18                    ; ROM 180F5: 2118de
    LD A,(HL)                      ; ROM 180F8: 7e
    INC A                          ; ROM 180F9: 3c
    CP 12                          ; ROM 180FA: fe0c
    RET nc                         ; ROM 180FC: d0
    LD (HL),A                      ; ROM 180FD: 77
    RET                            ; ROM 180FE: c9
    LD A,($de05)                   ; ROM 180FF: 3a05de
    BIT 7,A                        ; ROM 18102: cb7f
    JP z,$83ef                     ; ROM 18104: caef83
    CP $90                         ; ROM 18107: fe90
    JR c,$814f                     ; ROM 18109: 3844
    CP $ad                         ; ROM 1810B: fead
    JR c,$817c                     ; ROM 1810D: 386d
    CP $b5                         ; ROM 1810F: feb5
    JP nc,$83ef                    ; ROM 18111: d2ef83
    SUB $b0                        ; ROM 18114: d6b0
    LD HL,$811d                    ; ROM 18116: 211d81
    CALL $8424                     ; ROM 18119: cd2484
    JP (HL)                        ; ROM 1811C: e9
    db $27,$81,$EF,$83,$37,$81,$58,$82,$00,$70 ; ROM 1811D
    LD A,12                        ; ROM 18127: 3e0c
    LD ($de0b),A                   ; ROM 18129: 320bde
    LD A,$12                       ; ROM 1812C: 3e12
    LD ($de0c),A                   ; ROM 1812E: 320cde
    LD ($de0d),A                   ; ROM 18131: 320dde
    JP $8176                       ; ROM 18134: c37681
    db $FD,$21,$00,$DF,$11,$30,$00,$06,$03,$21,$4E,$81,$FD,$75,$03,$FD ; ROM 18137
    db $74,$04,$FD,$19,$10,$F6,$C9,$F2 ; ROM 18147
    SUB $81                        ; ROM 1814F: d681
    RET m                          ; ROM 18151: f8
    EX AF,AF'                      ; ROM 18152: 08
    CALL $83ef                     ; ROM 18153: cdef83
    EX AF,AF'                      ; ROM 18156: 08
    LD HL,$8b09                    ; ROM 18157: 21098b
    LD C,A                         ; ROM 1815A: 4f
    EX AF,AF'                      ; ROM 1815B: 08
    CALL $842e                     ; ROM 1815C: cd2e84
    LD ($de01),A                   ; ROM 1815F: 3201de
    LD ($de02),A                   ; ROM 18162: 3202de
    EX AF,AF'                      ; ROM 18165: 08
    LD HL,$8b16                    ; ROM 18166: 21168b
    CALL $8424                     ; ROM 18169: cd2484
    LD B,(HL)                      ; ROM 1816C: 46
    INC HL                         ; ROM 1816D: 23
    LD DE,$de40                    ; ROM 1816E: 1140de
    CALL $81ca                     ; ROM 18171: cdca81
    DJNZ $8171                     ; ROM 18174: 10fb
    LD A,$80                       ; ROM 18176: 3e80
    LD ($de05),A                   ; ROM 18178: 3205de
    RET                            ; ROM 1817B: c9
    LD ($de0f),A                   ; ROM 1817C: 320fde
    SUB $90                        ; ROM 1817F: d690
    LD HL,$8b30                    ; ROM 18181: 21308b
    CALL $8424                     ; ROM 18184: cd2484
    LD B,(HL)                      ; ROM 18187: 46
    INC HL                         ; ROM 18188: 23
    INC HL                         ; ROM 18189: 23
    LD A,(HL)                      ; ROM 1818A: 7e
    DEC HL                         ; ROM 1818B: 2b
    CP $a0                         ; ROM 1818C: fea0
    JR z,$81b8                     ; ROM 1818E: 2828
    CP $c0                         ; ROM 18190: fec0
    JR z,$819d                     ; ROM 18192: 2809
    LD DE,$df60                    ; ROM 18194: 1160df
    LD IY,$ded0                    ; ROM 18197: fd21d0de
    JR $81bf                       ; ROM 1819B: 1822
    LD IY,$df60                    ; ROM 1819D: fd2160df
    BIT 6,(IY)                     ; ROM 181A1: fdcb0076
    JR nz,$81af                    ; ROM 181A5: 2008
    SET 2,(IY)                     ; ROM 181A7: fdcb00d6
    LD A,$ff                       ; ROM 181AB: 3eff
    OUT ($007f),A                  ; ROM 181AD: d37f
    LD DE,$df30                    ; ROM 181AF: 1130df
    LD IY,$dea0                    ; ROM 181B2: fd21a0de
    JR $81bf                       ; ROM 181B6: 1807
    LD DE,$df00                    ; ROM 181B8: 1100df
    LD IY,$de70                    ; ROM 181BB: fd2170de
    CALL $81c6                     ; ROM 181BF: cdc681
    DJNZ $8189                     ; ROM 181C2: 10c5
    JR $8176                       ; ROM 181C4: 18b0
    SET 2,(IY)                     ; ROM 181C6: fdcb00d6
    LD C,$39                       ; ROM 181CA: 0e39
    PUSH DE                        ; ROM 181CC: d5
    POP IX                         ; ROM 181CD: dde1
    LDI                            ; ROM 181CF: eda0
    LDI                            ; ROM 181D1: eda0
    LDI                            ; ROM 181D3: eda0
    LDI                            ; ROM 181D5: eda0
    LDI                            ; ROM 181D7: eda0
    LDI                            ; ROM 181D9: eda0
    LDI                            ; ROM 181DB: eda0
    LDI                            ; ROM 181DD: eda0
    LDI                            ; ROM 181DF: eda0
    LD A,C                         ; ROM 181E1: 79
    LD (DE),A                      ; ROM 181E2: 12
    INC DE                         ; ROM 181E3: 13
    XOR A                          ; ROM 181E4: af
    LD (IX+$27),A                  ; ROM 181E5: dd7727
    LD (IX+$28),A                  ; ROM 181E8: dd7728
    LD (IX+$29),A                  ; ROM 181EB: dd7729
    INC A                          ; ROM 181EE: 3c
    LD (DE),A                      ; ROM 181EF: 12
    PUSH HL                        ; ROM 181F0: e5
    LD HL,$26                      ; ROM 181F1: 212600
    ADD HL,DE                      ; ROM 181F4: 19
    EX DE,HL                       ; ROM 181F5: eb
    POP HL                         ; ROM 181F6: e1
    RET                            ; ROM 181F7: c9
    LD DE,$de09                    ; ROM 181F8: 1109de
    LD A,(DE)                      ; ROM 181FB: 1a
    CP $80                         ; ROM 181FC: fe80
    JR z,$825f                     ; ROM 181FE: 285f
    AND $7f                        ; ROM 18200: e67f
    RET z                          ; ROM 18202: c8
    db $DD,$21,$10,$DE,$FD,$21,$0E,$DE,$CD,$AD,$80,$FD,$7E,$00,$CD,$61 ; ROM 18203
    db $82,$D6,$90,$21,$30,$8B,$CD,$24,$84,$23,$23,$7E,$2B,$FE,$C0,$28 ; ROM 18213
    db $10,$11,$60,$DF,$FD,$21,$D0,$DE,$1A,$B7,$FA,$54,$82,$3E,$01,$18 ; ROM 18223
    db $1A,$3A,$60,$DF,$B7,$F2,$41,$82,$E6,$40,$3E,$80,$28,$13,$11,$30 ; ROM 18233
    db $DF,$FD,$21,$A0,$DE,$1A,$B7,$FA,$54,$82,$AF,$32,$0F,$DE,$C3,$C6 ; ROM 18243
    db $81,$32,$0F,$DE,$C9,$AF,$CD,$61,$82,$C3,$76,$81,$AF,$12,$32,$0E ; ROM 18253
    db $DE,$08,$3A,$0F,$DE,$B7,$FA,$7B,$82,$21,$30,$DF,$28,$03,$21,$60 ; ROM 18263
    db $DF,$77,$23,$7E,$C6,$1F,$D3,$7F,$08,$C9 ; ROM 18273
    BIT 7,(IX+6)                   ; ROM 1827D: ddcb067e
    RET z                          ; ROM 18281: c8
    BIT 1,(IX)                     ; ROM 18282: ddcb004e
    RET nz                         ; ROM 18286: c0
    LD E,(IX+$10)                  ; ROM 18287: dd5e10
    LD D,(IX+$11)                  ; ROM 1828A: dd5611
    PUSH IX                        ; ROM 1828D: dde5
    POP HL                         ; ROM 1828F: e1
    LD B,0                         ; ROM 18290: 0600
    LD C,$14                       ; ROM 18292: 0e14
    ADD HL,BC                      ; ROM 18294: 09
    EX DE,HL                       ; ROM 18295: eb
    LDI                            ; ROM 18296: eda0
    LDI                            ; ROM 18298: eda0
    LDI                            ; ROM 1829A: eda0
    LD A,(HL)                      ; ROM 1829C: 7e
    SRL A                          ; ROM 1829D: cb3f
    LD (DE),A                      ; ROM 1829F: 12
    XOR A                          ; ROM 182A0: af
    LD (IX+$12),A                  ; ROM 182A1: dd7712
    LD (IX+$13),A                  ; ROM 182A4: dd7713
    RET                            ; ROM 182A7: c9
    BIT 7,(IX+7)                   ; ROM 182A8: ddcb077e
    RET z                          ; ROM 182AC: c8
    db $DD,$CB,$00,$4E,$C0,$DD,$CB,$1D,$7E,$C0,$3E,$FF,$DD,$77,$1F,$E6 ; ROM 182AD
    db $10,$DD,$B6,$1E,$DD,$77,$1D,$C9 ; ROM 182BD
    LD L,(IX+11)                   ; ROM 182C5: dd6e0b
    LD H,(IX+12)                   ; ROM 182C8: dd660c
    LD A,(IX+6)                    ; ROM 182CB: dd7e06
    OR A                           ; ROM 182CE: b7
    RET z                          ; ROM 182CF: c8
    JP p,$831b                     ; ROM 182D0: f21b83
    DEC (IX+$14)                   ; ROM 182D3: dd3514
    RET nz                         ; ROM 182D6: c0
    INC (IX+$14)                   ; ROM 182D7: dd3414
    PUSH HL                        ; ROM 182DA: e5
    LD L,(IX+$12)                  ; ROM 182DB: dd6e12
    LD H,(IX+$13)                  ; ROM 182DE: dd6613
    DEC (IX+$15)                   ; ROM 182E1: dd3515
    LD E,(IX+$10)                  ; ROM 182E4: dd5e10
    LD D,(IX+$11)                  ; ROM 182E7: dd5611
    PUSH DE                        ; ROM 182EA: d5
    POP IY                         ; ROM 182EB: fde1
    JR nz,$8306                    ; ROM 182ED: 2017
    LD A,(IY+1)                    ; ROM 182EF: fd7e01
    LD (IX+$15),A                  ; ROM 182F2: dd7715
    LD A,(IX+$16)                  ; ROM 182F5: dd7e16
    LD C,A                         ; ROM 182F8: 4f
    AND $80                        ; ROM 182F9: e680
    RLCA                           ; ROM 182FB: 07
    NEG                            ; ROM 182FC: ed44
    LD B,A                         ; ROM 182FE: 47
    ADD HL,BC                      ; ROM 182FF: 09
    LD (IX+$12),L                  ; ROM 18300: dd7512
    LD (IX+$13),H                  ; ROM 18303: dd7413
    POP BC                         ; ROM 18306: c1
    ADD HL,BC                      ; ROM 18307: 09
    DEC (IX+$17)                   ; ROM 18308: dd3517
    RET nz                         ; ROM 1830B: c0
    LD A,(IY+3)                    ; ROM 1830C: fd7e03
    LD (IX+$17),A                  ; ROM 1830F: dd7717
    LD A,(IX+$16)                  ; ROM 18312: dd7e16
    NEG                            ; ROM 18315: ed44
    LD (IX+$16),A                  ; ROM 18317: dd7716
    RET                            ; ROM 1831A: c9
    DEC A                          ; ROM 1831B: 3d
    EX DE,HL                       ; ROM 1831C: eb
    LD HL,$8a52                    ; ROM 1831D: 21528a
    CALL $8424                     ; ROM 18320: cd2484
    JR $8328                       ; ROM 18323: 1803
    db $DD,$77,$15 ; ROM 18325
    PUSH HL                        ; ROM 18328: e5
    LD C,(IX+$15)                  ; ROM 18329: dd4e15
    CALL $842e                     ; ROM 1832C: cd2e84
    POP HL                         ; ROM 1832F: e1
    BIT 7,A                        ; ROM 18330: cb7f
    JR z,$834f                     ; ROM 18332: 281b
    db $FE,$83,$28,$0C,$30,$11,$FE,$80,$28,$0A,$DD,$CB,$00,$EE,$E1,$C9 ; ROM 18334
    db $13,$1A,$18,$DD,$AF,$18,$DA,$26,$FF,$18,$02 ; ROM 18344
    LD H,0                         ; ROM 1834F: 2600
    LD L,A                         ; ROM 18351: 6f
    ADD HL,DE                      ; ROM 18352: 19
    INC (IX+$15)                   ; ROM 18353: dd3415
    RET                            ; ROM 18356: c9
    RES 1,(IX)                     ; ROM 18357: ddcb008e
    RES 4,(IX)                     ; ROM 1835B: ddcb00a6
    LD E,(IX+3)                    ; ROM 1835F: dd5e03
    LD D,(IX+4)                    ; ROM 18362: dd5604
    LD A,(DE)                      ; ROM 18365: 1a
    INC DE                         ; ROM 18366: 13
    CP $e0                         ; ROM 18367: fee0
    JP nc,$86db                    ; ROM 18369: d2db86
    BIT 3,(IX)                     ; ROM 1836C: ddcb005e
    JP nz,$83d1                    ; ROM 18370: c2d183
    CP $80                         ; ROM 18373: fe80
    JR c,$839b                     ; ROM 18375: 3824
    JR z,$83cc                     ; ROM 18377: 2853
    EX AF,AF'                      ; ROM 18379: 08
    LD A,(IX+$1d)                  ; ROM 1837A: dd7e1d
    AND $7f                        ; ROM 1837D: e67f
    LD (IX+$1d),A                  ; ROM 1837F: dd771d
    EX AF,AF'                      ; ROM 18382: 08
    CALL $841c                     ; ROM 18383: cd1c84
    LD (IX+11),L                   ; ROM 18386: dd750b
    LD (IX+12),H                   ; ROM 18389: dd740c
    LD A,(DE)                      ; ROM 1838C: 1a
    INC DE                         ; ROM 1838D: 13
    OR A                           ; ROM 1838E: b7
    JP p,$839b                     ; ROM 1838F: f29b83
    LD A,(IX+13)                   ; ROM 18392: dd7e0d
    LD (IX+10),A                   ; ROM 18395: dd770a
    DEC DE                         ; ROM 18398: 1b
    JR $83a4                       ; ROM 18399: 1809
    CALL $8433                     ; ROM 1839B: cd3384
    LD (IX+10),A                   ; ROM 1839E: dd770a
    LD (IX+13),A                   ; ROM 183A1: dd770d
    LD (IX+3),E                    ; ROM 183A4: dd7303
    LD (IX+4),D                    ; ROM 183A7: dd7204
    BIT 1,(IX)                     ; ROM 183AA: ddcb004e
    RET nz                         ; ROM 183AE: c0
    BIT 6,(IX)                     ; ROM 183AF: ddcb0076
    JR nz,$83b9                    ; ROM 183B3: 2004
    RES 5,(IX)                     ; ROM 183B5: ddcb00ae
    LD A,(IX+15)                   ; ROM 183B9: dd7e0f
    LD (IX+14),A                   ; ROM 183BC: dd770e
    XOR A                          ; ROM 183BF: af
    LD (IX+$15),A                  ; ROM 183C0: dd7715
    BIT 7,(IX+7)                   ; ROM 183C3: ddcb077e
    RET nz                         ; ROM 183C7: c0
    LD (IX+$1f),A                  ; ROM 183C8: dd771f
    RET                            ; ROM 183CB: c9
    CALL $85eb                     ; ROM 183CC: cdeb85
    JR $838c                       ; ROM 183CF: 18bb
    LD H,A                         ; ROM 183D1: 67
    LD A,(DE)                      ; ROM 183D2: 1a
    INC DE                         ; ROM 183D3: 13
    LD L,A                         ; ROM 183D4: 6f
    OR H                           ; ROM 183D5: b4
    JR z,$83e4                     ; ROM 183D6: 280c
    LD B,0                         ; ROM 183D8: 0600
    LD A,(IX+5)                    ; ROM 183DA: dd7e05
    OR A                           ; ROM 183DD: b7
    LD C,A                         ; ROM 183DE: 4f
    JP p,$83e3                     ; ROM 183DF: f2e383
    DEC B                          ; ROM 183E2: 05
    ADD HL,BC                      ; ROM 183E3: 09
    LD (IX+11),L                   ; ROM 183E4: dd750b
    LD (IX+12),H                   ; ROM 183E7: dd740c
    LD A,(DE)                      ; ROM 183EA: 1a
    INC DE                         ; ROM 183EB: 13
    JP $839b                       ; ROM 183EC: c39b83
    PUSH HL                        ; ROM 183EF: e5
    PUSH BC                        ; ROM 183F0: c5
    PUSH DE                        ; ROM 183F1: d5
    LD HL,$de05                    ; ROM 183F2: 2105de
    LD DE,$de06                    ; ROM 183F5: 1106de
    LD BC,$18a                     ; ROM 183F8: 018a01
    LD (HL),0                      ; ROM 183FB: 3600
    LDIR                           ; ROM 183FD: edb0
    POP DE                         ; ROM 183FF: d1
    POP BC                         ; ROM 18400: c1
    POP HL                         ; ROM 18401: e1
    PUSH HL                        ; ROM 18402: e5
    PUSH BC                        ; ROM 18403: c5
    LD HL,$8412                    ; ROM 18404: 211284
    LD B,10                        ; ROM 18407: 060a
    LD C,$7f                       ; ROM 18409: 0e7f
    OTIR                           ; ROM 1840B: edb3
    POP BC                         ; ROM 1840D: c1
    POP HL                         ; ROM 1840E: e1
    JP $8176                       ; ROM 1840F: c37681
    db $80,$00,$A0,$00,$C0,$00,$9F,$BF,$DF,$FF ; ROM 18412
    AND $7f                        ; ROM 1841C: e67f
    ADD A,(IX+5)                   ; ROM 1841E: dd8605
    LD HL,$843d                    ; ROM 18421: 213d84
    LD C,A                         ; ROM 18424: 4f
    LD B,0                         ; ROM 18425: 0600
    ADD HL,BC                      ; ROM 18427: 09
    ADD HL,BC                      ; ROM 18428: 09
    LD C,(HL)                      ; ROM 18429: 4e
    INC HL                         ; ROM 1842A: 23
    LD H,(HL)                      ; ROM 1842B: 66
    LD L,C                         ; ROM 1842C: 69
    RET                            ; ROM 1842D: c9
    LD B,0                         ; ROM 1842E: 0600
    ADD HL,BC                      ; ROM 18430: 09
    LD A,(HL)                      ; ROM 18431: 7e
    RET                            ; ROM 18432: c9
    LD B,(IX+2)                    ; ROM 18433: dd4602
    DEC B                          ; ROM 18436: 05
    RET z                          ; ROM 18437: c8
    LD C,A                         ; ROM 18438: 4f
    ADD A,C                        ; ROM 18439: 81
    DJNZ $8439                     ; ROM 1843A: 10fd
    RET                            ; ROM 1843C: c9
    db $56,$03,$26,$03,$F9,$02,$CE,$02,$A5,$02,$80,$02,$5C,$02,$3A,$02 ; ROM 1843D
    db $1A,$02,$FB,$01,$DF,$01,$C4,$01,$AB,$01,$93,$01,$7D,$01,$67,$01 ; ROM 1844D
    db $53,$01,$40,$01,$2E,$01,$1D,$01,$0D,$01,$FE,$00,$EF,$00,$E2,$00 ; ROM 1845D
    db $D6,$00,$C9,$00,$BE,$00,$B4,$00,$A9,$00,$A0,$00,$97,$00,$8F,$00 ; ROM 1846D
    db $87,$00,$7F,$00,$78,$00,$71,$00,$6B,$00,$65,$00,$5F,$00,$5A,$00 ; ROM 1847D
    db $55,$00,$50,$00,$4B,$00,$47,$00,$43,$00,$40,$00,$3C,$00,$39,$00 ; ROM 1848D
    db $36,$00,$33,$00,$30,$00,$2D,$00,$2B,$00,$28,$00,$26,$00,$24,$00 ; ROM 1849D
    db $22,$00,$20,$00,$1F,$00,$1D,$00,$1B,$00,$1A,$00,$18,$00,$17,$00 ; ROM 184AD
    db $16,$00,$15,$00,$13,$00,$12,$00,$11,$00 ; ROM 184BD
    DEC (IX+10)                    ; ROM 184C7: dd350a
    JR nz,$84e1                    ; ROM 184CA: 2015
    CALL $8357                     ; ROM 184CC: cd5783
    BIT 4,(IX)                     ; ROM 184CF: ddcb0066
    RET nz                         ; ROM 184D3: c0
    BIT 2,(IX)                     ; ROM 184D4: ddcb0056
    RET nz                         ; ROM 184D8: c0
    CALL $827d                     ; ROM 184D9: cd7d82
    CALL $82a8                     ; ROM 184DC: cda882
    JR $84fe                       ; ROM 184DF: 181d
    BIT 2,(IX)                     ; ROM 184E1: ddcb0056
    RET nz                         ; ROM 184E5: c0
    LD A,(IX+14)                   ; ROM 184E6: dd7e0e
    OR A                           ; ROM 184E9: b7
    JR z,$84f2                     ; ROM 184EA: 2806
    db $DD,$35,$0E,$CC,$EB,$85 ; ROM 184EC
    LD A,(IX+6)                    ; ROM 184F2: dd7e06
    OR A                           ; ROM 184F5: b7
    JR z,$852d                     ; ROM 184F6: 2835
    BIT 5,(IX)                     ; ROM 184F8: ddcb006e
    JR nz,$852d                    ; ROM 184FC: 202f
    BIT 6,(IX)                     ; ROM 184FE: ddcb0076
    JR nz,$852d                    ; ROM 18502: 2029
    CALL $82c5                     ; ROM 18504: cdc582
    LD D,0                         ; ROM 18507: 1600
    LD A,(IX+$25)                  ; ROM 18509: dd7e25
    OR A                           ; ROM 1850C: b7
    JP p,$8511                     ; ROM 1850D: f21185
    db $15 ; ROM 18510
    LD E,A                         ; ROM 18511: 5f
    ADD HL,DE                      ; ROM 18512: 19
    LD A,(IX+1)                    ; ROM 18513: dd7e01
    CP $e0                         ; ROM 18516: fee0
    JR nz,$851c                    ; ROM 18518: 2002
    LD A,$c0                       ; ROM 1851A: 3ec0
    LD C,A                         ; ROM 1851C: 4f
    LD A,L                         ; ROM 1851D: 7d
    AND 15                         ; ROM 1851E: e60f
    OR C                           ; ROM 18520: b1
    OUT ($007f),A                  ; ROM 18521: d37f
    LD A,L                         ; ROM 18523: 7d
    AND $f0                        ; ROM 18524: e6f0
    OR H                           ; ROM 18526: b4
    RRCA                           ; ROM 18527: 0f
    RRCA                           ; ROM 18528: 0f
    RRCA                           ; ROM 18529: 0f
    RRCA                           ; ROM 1852A: 0f
    OUT ($007f),A                  ; ROM 1852B: d37f
    CALL $854b                     ; ROM 1852D: cd4b85
    BIT 2,(IX)                     ; ROM 18530: ddcb0056
    RET nz                         ; ROM 18534: c0
    BIT 4,(IX)                     ; ROM 18535: ddcb0066
    RET nz                         ; ROM 18539: c0
    ADD A,(IX+8)                   ; ROM 1853A: dd8608
    BIT 4,A                        ; ROM 1853D: cb67
    JR z,$8543                     ; ROM 1853F: 2802
    db $3E,$0F ; ROM 18541
    OR (IX+1)                      ; ROM 18543: ddb601
    ADD A,$10                      ; ROM 18546: c610
    OUT ($007f),A                  ; ROM 18548: d37f
    RET                            ; ROM 1854A: c9
    LD A,(IX+7)                    ; ROM 1854B: dd7e07
    OR A                           ; ROM 1854E: b7
    RET z                          ; ROM 1854F: c8
    JP p,$8602                     ; ROM 18550: f20286
    db $DD,$CB,$1D,$66,$28,$1A,$DD,$56,$20,$DD,$7E,$1F,$92,$30,$01,$AF ; ROM 18553
    db $B7,$DD,$77,$1F,$20,$78,$DD,$7E,$1D,$EE,$30,$DD,$77,$1D,$18,$6E ; ROM 18563
    db $DD,$CB,$1D,$6E,$28,$2A,$DD,$7E,$1F,$DD,$56,$21,$DD,$5E,$22,$82 ; ROM 18573
    db $38,$03,$BB,$38,$01,$7B,$BB,$DD,$77,$1F,$20,$52,$DD,$7E,$1D,$DD ; ROM 18583
    db $CB,$1D,$5E,$28,$04,$EE,$30,$18,$02,$EE,$60,$DD,$77,$1D,$18,$3E ; ROM 18593
    db $DD,$CB,$1D,$76,$28,$1C,$DD,$7E,$1F,$DD,$56,$23,$82,$30,$02,$3E ; ROM 185A3
    db $FF,$FE,$FF,$DD,$77,$1F,$20,$26,$DD,$7E,$1D,$E6,$8F,$DD,$77,$1D ; ROM 185B3
    db $18,$1C,$DD,$7E,$1F,$DD,$56,$24,$82,$30,$10,$DD,$7E,$1D,$E6,$0F ; ROM 185C3
    db $DD,$77,$1D,$3E,$FF,$DD,$77,$1F,$C3,$3E,$86,$DD,$77,$1F,$DD,$7E ; ROM 185D3
    db $1F,$0F,$0F,$0F,$0F,$E6,$0F,$C9 ; ROM 185E3
    BIT 1,(IX)                     ; ROM 185EB: ddcb004e
    RET nz                         ; ROM 185EF: c0
    BIT 7,(IX+7)                   ; ROM 185F0: ddcb077e
    JP z,$863e                     ; ROM 185F4: ca3e86
    db $DD,$7E,$1D,$E6,$0F,$F6,$80,$DD,$77,$1D,$C9 ; ROM 185F7
    DEC A                          ; ROM 18602: 3d
    LD HL,$897f                    ; ROM 18603: 217f89
    CALL $8424                     ; ROM 18606: cd2484
    JR $860e                       ; ROM 18609: 1803
    db $DD,$77,$1F ; ROM 1860B
    PUSH HL                        ; ROM 1860E: e5
    LD C,(IX+$1f)                  ; ROM 1860F: dd4e1f
    CALL $842e                     ; ROM 18612: cd2e84
    POP HL                         ; ROM 18615: e1
    BIT 7,A                        ; ROM 18616: cb7f
    JR z,$863a                     ; ROM 18618: 2820
    CP $82                         ; ROM 1861A: fe82
    JR z,$862a                     ; ROM 1861C: 280c
    CP $81                         ; ROM 1861E: fe81
    JR z,$8634                     ; ROM 18620: 2812
    db $FE,$80,$28,$0B,$13,$1A,$18,$E1 ; ROM 18622
    SET 4,(IX)                     ; ROM 1862A: ddcb00e6
    POP HL                         ; ROM 1862E: e1
    JR $863e                       ; ROM 1862F: 180d
    db $AF,$18,$D7 ; ROM 18631
    SET 4,(IX)                     ; ROM 18634: ddcb00e6
    POP HL                         ; ROM 18638: e1
    RET                            ; ROM 18639: c9
    INC (IX+$1f)                   ; ROM 1863A: dd341f
    RET                            ; ROM 1863D: c9
    SET 4,(IX)                     ; ROM 1863E: ddcb00e6
    BIT 2,(IX)                     ; ROM 18642: ddcb0056
    RET nz                         ; ROM 18646: c0
    LD A,$1f                       ; ROM 18647: 3e1f
    ADD A,(IX+1)                   ; ROM 18649: dd8601
    OUT ($007f),A                  ; ROM 1864C: d37f
    RET                            ; ROM 1864E: c9
    DEC (IX+10)                    ; ROM 1864F: dd350a
    JP nz,$852d                    ; ROM 18652: c22d85
    RES 4,(IX)                     ; ROM 18655: ddcb00a6
    LD E,(IX+3)                    ; ROM 18659: dd5e03
    LD D,(IX+4)                    ; ROM 1865C: dd5604
    LD A,(DE)                      ; ROM 1865F: 1a
    INC DE                         ; ROM 18660: 13
    CP $e0                         ; ROM 18661: fee0
    JR nc,$8670                    ; ROM 18663: 300b
    CP $80                         ; ROM 18665: fe80
    JP c,$839b                     ; ROM 18667: da9b83
    CALL $8679                     ; ROM 1866A: cd7986
    JP $838c                       ; ROM 1866D: c38c83
    LD HL,$8676                    ; ROM 18670: 217686
    JP $86de                       ; ROM 18673: c3de86
    INC DE                         ; ROM 18676: 13
    JR $865f                       ; ROM 18677: 18e6
    BIT 0,A                        ; ROM 18679: cb47
    JR nz,$86bc                    ; ROM 1867B: 203f
    BIT 1,A                        ; ROM 1867D: cb4f
    JR nz,$869c                    ; ROM 1867F: 201b
    BIT 2,A                        ; ROM 18681: cb57
    JR nz,$86b4                    ; ROM 18683: 202f
    BIT 3,A                        ; ROM 18685: cb5f
    JR nz,$8694                    ; ROM 18687: 200b
    BIT 4,A                        ; ROM 18689: cb67
    JR nz,$86ac                    ; ROM 1868B: 201f
    BIT 5,A                        ; ROM 1868D: cb6f
    JR nz,$86a4                    ; ROM 1868F: 2013
    JP $863e                       ; ROM 18691: c33e86
    LD A,2                         ; ROM 18694: 3e02
    LD B,3                         ; ROM 18696: 0603
    LD C,$e5                       ; ROM 18698: 0ee5
    JR $86c2                       ; ROM 1869A: 1826
    db $3E,$03,$06,$06,$0E,$E4,$18,$1E,$3E,$04,$06,$04,$0E,$E4,$18,$16 ; ROM 1869C
    db $3E,$03,$06,$03,$0E,$E6,$18,$0E ; ROM 186AC
    LD A,1                         ; ROM 186B4: 3e01
    LD B,1                         ; ROM 186B6: 0601
    LD C,$e6                       ; ROM 186B8: 0ee6
    JR $86c2                       ; ROM 186BA: 1806
    LD A,1                         ; ROM 186BC: 3e01
    LD B,4                         ; ROM 186BE: 0604
    LD C,$e4                       ; ROM 186C0: 0ee4
    LD (IX+7),A                    ; ROM 186C2: dd7707
    LD A,($de18)                   ; ROM 186C5: 3a18de
    ADD A,B                        ; ROM 186C8: 80
    LD (IX+8),A                    ; ROM 186C9: dd7708
    BIT 2,(IX)                     ; ROM 186CC: ddcb0056
    RET nz                         ; ROM 186D0: c0
    LD A,($de17)                   ; ROM 186D1: 3a17de
    ADD A,C                        ; ROM 186D4: 81
    LD ($de13),A                   ; ROM 186D5: 3213de
    OUT ($007f),A                  ; ROM 186D8: d37f
    RET                            ; ROM 186DA: c9
    LD HL,$86ef                    ; ROM 186DB: 21ef86
    PUSH HL                        ; ROM 186DE: e5
    SUB $e0                        ; ROM 186DF: d6e0
    LD HL,$86f3                    ; ROM 186E1: 21f386
    ADD A,A                        ; ROM 186E4: 87
    LD C,A                         ; ROM 186E5: 4f
    LD B,0                         ; ROM 186E6: 0600
    ADD HL,BC                      ; ROM 186E8: 09
    LD C,(HL)                      ; ROM 186E9: 4e
    INC HL                         ; ROM 186EA: 23
    LD H,(HL)                      ; ROM 186EB: 66
    LD L,C                         ; ROM 186EC: 69
    LD A,(DE)                      ; ROM 186ED: 1a
    JP (HL)                        ; ROM 186EE: e9
    INC DE                         ; ROM 186EF: 13
    JP $8365                       ; ROM 186F0: c36583
    db $5B,$89,$B8,$88,$33,$87,$07,$89,$70,$87,$75,$89,$60,$87,$B2,$88 ; ROM 186F3
    db $9A,$88,$5B,$89,$DA,$88,$5A,$89,$34,$89,$16,$89,$56,$89,$7F,$89 ; ROM 18703
    db $A4,$88,$FB,$87,$00,$88,$86,$87,$E3,$87,$DF,$87,$E7,$87,$83,$88 ; ROM 18713
    db $56,$88,$70,$88,$82,$87,$7B,$87,$7E,$89,$ED,$87,$1D,$89,$1D,$89 ; ROM 18723
    db $DD,$46,$26,$DD,$77,$26,$2F,$4F,$DD,$7E,$01,$FE,$80,$28,$14,$CB ; ROM 18733
    db $00,$CB,$01,$FE,$A0,$28,$0C,$CB,$00,$CB,$01,$FE,$C0,$28,$04,$CB ; ROM 18743
    db $00,$CB,$01,$21,$12,$DE,$7E,$B0,$A1,$77,$D3,$06,$C9 ; ROM 18753
    EX AF,AF'                      ; ROM 18760: 08
    LD A,($de0b)                   ; ROM 18761: 3a0bde
    OR A                           ; ROM 18764: b7
    RET nz                         ; ROM 18765: c0
    EX AF,AF'                      ; ROM 18766: 08
    ADD A,(IX+8)                   ; ROM 18767: dd8608
    AND 15                         ; ROM 1876A: e60f
    LD (IX+8),A                    ; ROM 1876C: dd7708
    RET                            ; ROM 1876F: c9
    db $4F,$3A,$18,$DE,$81,$E6,$0F,$32,$18,$DE,$C9 ; ROM 18770
    ADD A,(IX+5)                   ; ROM 1877B: dd8605
    LD (IX+5),A                    ; ROM 1877E: dd7705
    RET                            ; ROM 18781: c9
    db $DD,$77,$02,$C9 ; ROM 18782
    EX AF,AF'                      ; ROM 18786: 08
    LD A,($de0f)                   ; ROM 18787: 3a0fde
    OR A                           ; ROM 1878A: b7
    JP m,$87af                     ; ROM 1878B: faaf87
    db $08,$F6,$FC,$3C,$20,$1B,$21,$30,$DF,$CB,$7E,$28,$14,$21,$D0,$DE ; ROM 1878E
    db $CB,$96,$CB,$E6,$AF,$DD,$77,$00,$3D,$D3,$7F,$32,$0F,$DE,$E1,$E1 ; ROM 1879E
    db $C9 ; ROM 187AE
    LD A,(DE)                      ; ROM 187AF: 1a
    OUT ($007f),A                  ; ROM 187B0: d37f
    LD HL,$dea0                    ; ROM 187B2: 21a0de
    LD IY,$df30                    ; ROM 187B5: fd2130df
    OR $fc                         ; ROM 187B9: f6fc
    INC A                          ; ROM 187BB: 3c
    JR nz,$87cd                    ; ROM 187BC: 200f
    LD A,$df                       ; ROM 187BE: 3edf
    OUT ($007f),A                  ; ROM 187C0: d37f
    RES 6,(IX)                     ; ROM 187C2: ddcb00b6
    SET 2,(HL)                     ; ROM 187C6: cbd6
    SET 2,(IY)                     ; ROM 187C8: fdcb00d6
    RET                            ; ROM 187CC: c9
    db $DD,$CB,$00,$F6,$FD,$CB,$00,$7E,$20,$03,$CB,$96,$C9,$FD,$CB,$00 ; ROM 187CD
    db $96,$C9 ; ROM 187DD
    LD (IX+7),A                    ; ROM 187DF: dd7707
    RET                            ; ROM 187E2: c9
    db $DD,$77,$06,$C9 ; ROM 187E3
    EX DE,HL                       ; ROM 187E7: eb
    LD E,(HL)                      ; ROM 187E8: 5e
    INC HL                         ; ROM 187E9: 23
    LD D,(HL)                      ; ROM 187EA: 56
    DEC DE                         ; ROM 187EB: 1b
    RET                            ; ROM 187EC: c9
    db $FE,$01,$20,$05,$DD,$CB,$00,$DE,$C9,$DD,$CB,$00,$9E,$C9,$3E,$80 ; ROM 187ED
    db $32,$12,$DE ; ROM 187FD
    LD A,(IX+1)                    ; ROM 18800: dd7e01
    CP $a0                         ; ROM 18803: fea0
    JR z,$8838                     ; ROM 18805: 2831
    CP $c0                         ; ROM 18807: fec0
    JR z,$882c                     ; ROM 18809: 2821
    BIT 6,(IX)                     ; ROM 1880B: ddcb0076
    JR nz,$8827                    ; ROM 1880F: 2016
    LD HL,$df30                    ; ROM 18811: 2130df
    BIT 7,(HL)                     ; ROM 18814: cb7e
    JP nz,$8827                    ; ROM 18816: c22788
    LD HL,$dea0                    ; ROM 18819: 21a0de
    RES 2,(HL)                     ; ROM 1881C: cb96
    RES 6,(HL)                     ; ROM 1881E: cbb6
    SET 4,(HL)                     ; ROM 18820: cbe6
    LD HL,$df30                    ; ROM 18822: 2130df
    LD (HL),0                      ; ROM 18825: 3600
    LD HL,$ded0                    ; ROM 18827: 21d0de
    JR $883b                       ; ROM 1882A: 180f
    LD HL,$df60                    ; ROM 1882C: 2160df
    BIT 7,(HL)                     ; ROM 1882F: cb7e
    JR nz,$883b                    ; ROM 18831: 2008
    LD HL,$dea0                    ; ROM 18833: 21a0de
    JR $883b                       ; ROM 18836: 1803
    LD HL,$de70                    ; ROM 18838: 2170de
    RES 2,(HL)                     ; ROM 1883B: cb96
    SET 4,(HL)                     ; ROM 1883D: cbe6
    OR $1f                         ; ROM 1883F: f61f
    OUT ($007f),A                  ; ROM 18841: d37f
    XOR A                          ; ROM 18843: af
    LD ($de11),A                   ; ROM 18844: 3211de
    LD (IX),A                      ; ROM 18847: dd7700
    LD A,($de0e)                   ; ROM 1884A: 3a0ede
    OR A                           ; ROM 1884D: b7
    JR z,$8853                     ; ROM 1884E: 2803
    db $CD,$11,$82 ; ROM 18850
    POP BC                         ; ROM 18853: c1
    POP BC                         ; ROM 18854: c1
    RET                            ; ROM 18855: c9
    LD C,A                         ; ROM 18856: 4f
    INC DE                         ; ROM 18857: 13
    LD A,(DE)                      ; ROM 18858: 1a
    LD B,A                         ; ROM 18859: 47
    PUSH BC                        ; ROM 1885A: c5
    PUSH IX                        ; ROM 1885B: dde5
    POP HL                         ; ROM 1885D: e1
    DEC (IX+9)                     ; ROM 1885E: dd3509
    LD C,(IX+9)                    ; ROM 18861: dd4e09
    DEC (IX+9)                     ; ROM 18864: dd3509
    LD B,0                         ; ROM 18867: 0600
    ADD HL,BC                      ; ROM 18869: 09
    LD (HL),D                      ; ROM 1886A: 72
    DEC HL                         ; ROM 1886B: 2b
    LD (HL),E                      ; ROM 1886C: 73
    POP DE                         ; ROM 1886D: d1
    DEC DE                         ; ROM 1886E: 1b
    RET                            ; ROM 1886F: c9
    PUSH IX                        ; ROM 18870: dde5
    POP HL                         ; ROM 18872: e1
    LD C,(IX+9)                    ; ROM 18873: dd4e09
    LD B,0                         ; ROM 18876: 0600
    ADD HL,BC                      ; ROM 18878: 09
    LD E,(HL)                      ; ROM 18879: 5e
    INC HL                         ; ROM 1887A: 23
    LD D,(HL)                      ; ROM 1887B: 56
    INC (IX+9)                     ; ROM 1887C: dd3409
    INC (IX+9)                     ; ROM 1887F: dd3409
    RET                            ; ROM 18882: c9
    INC DE                         ; ROM 18883: 13
    ADD A,$27                      ; ROM 18884: c627
    LD C,A                         ; ROM 18886: 4f
    LD B,0                         ; ROM 18887: 0600
    PUSH IX                        ; ROM 18889: dde5
    POP HL                         ; ROM 1888B: e1
    ADD HL,BC                      ; ROM 1888C: 09
    LD A,(HL)                      ; ROM 1888D: 7e
    OR A                           ; ROM 1888E: b7
    JR nz,$8893                    ; ROM 1888F: 2002
    LD A,(DE)                      ; ROM 18891: 1a
    LD (HL),A                      ; ROM 18892: 77
    INC DE                         ; ROM 18893: 13
    DEC (HL)                       ; ROM 18894: 35
    JP nz,$87e7                    ; ROM 18895: c2e787
    INC DE                         ; ROM 18898: 13
    RET                            ; ROM 18899: c9
    db $CD,$33,$84,$DD,$77,$0E,$DD,$77,$0F,$C9 ; ROM 1889A
    LD (IX+$10),E                  ; ROM 188A4: dd7310
    LD (IX+$11),D                  ; ROM 188A7: dd7211
    LD (IX+6),$80                  ; ROM 188AA: dd360680
    INC DE                         ; ROM 188AE: 13
    INC DE                         ; ROM 188AF: 13
    INC DE                         ; ROM 188B0: 13
    RET                            ; ROM 188B1: c9
    SET 1,(IX)                     ; ROM 188B2: ddcb00ce
    DEC DE                         ; ROM 188B6: 1b
    RET                            ; ROM 188B7: c9
    db $DD,$77,$25,$C9,$4F,$ED,$5F,$DD,$86,$03,$DD,$CB,$00,$A6,$E6,$07 ; ROM 188B8
    db $A1,$DD,$77,$08,$DD,$36,$1A,$E1,$C9,$1B,$AF,$DD,$77,$08,$DD,$77 ; ROM 188C8
    db $1A,$C9,$CB,$7F,$28,$10,$DD,$CB,$00,$C6,$DD,$77,$18,$13,$1A,$DD ; ROM 188D8
    db $77,$19,$DD,$77,$1A,$C9,$DD,$CB,$00,$86,$DD,$36,$1A,$00,$13,$C9 ; ROM 188E8
    db $ED,$5F,$DD,$86,$03,$E6,$07,$DD,$77,$06,$DD,$36,$1A,$E4,$C9,$ED ; ROM 188F8
    db $5F,$DD,$86,$03,$E6,$07,$DD,$77,$07,$DD,$36,$1A,$E5,$C9,$32,$02 ; ROM 18908
    db $DE,$32,$01,$DE,$C9,$B7,$28,$11,$4F,$ED,$5F,$B7,$28,$FB,$A1,$CD ; ROM 18918
    db $33,$84,$DD,$77,$0E,$DD,$77,$0F,$C9,$AF,$18,$F6,$B7,$28,$17,$ED ; ROM 18928
    db $5F,$DD,$86,$03,$CB,$47,$28,$04,$F6,$FC,$18,$02,$E6,$03,$DD,$77 ; ROM 18938
    db $25,$DD,$36,$1A,$E6,$C9,$AF,$DD,$77,$25,$DD,$77,$1A,$C9,$DD,$77 ; ROM 18948
    db $1C,$C9,$C9,$DD,$36,$07,$80,$DD,$E5,$E1,$06,$00,$0E,$20,$09,$EB ; ROM 18958
    db $ED,$A0,$ED,$A0,$ED,$A0,$ED,$A0,$ED,$A0,$EB,$1B,$C9,$B7,$28,$02 ; ROM 18968
    db $3E,$08,$DD,$77,$1E,$C9,$C9,$9F,$89,$A2,$89,$AB,$89,$B4,$89,$BD ; ROM 18978
    db $89,$C8,$89,$E7,$89,$F2,$89,$01,$8A,$0D,$8A,$13,$8A,$1E,$8A,$2F ; ROM 18988
    db $8A,$3A,$8A,$3F,$8A,$46,$8A,$02,$06,$82,$00,$01,$02,$04,$05,$06 ; ROM 18998
    db $07,$0A,$82,$01,$00,$01,$01,$03,$04,$07,$0A,$82,$02,$00,$00,$00 ; ROM 189A8
    db $01,$02,$03,$04,$82,$02,$01,$00,$01,$02,$02,$03,$03,$04,$04,$81 ; ROM 189B8
    db $05,$02,$00,$00,$01,$01,$02,$02,$02,$02,$03,$03,$03,$03,$04,$04 ; ROM 189C8
    db $04,$04,$05,$05,$05,$05,$06,$06,$06,$06,$07,$07,$07,$08,$81,$00 ; ROM 189D8
    db $00,$01,$01,$03,$03,$04,$05,$05,$05,$82,$00,$00,$01,$01,$02,$02 ; ROM 189E8
    db $02,$03,$03,$03,$03,$04,$04,$05,$81,$00,$00,$01,$01,$01,$02,$04 ; ROM 189F8
    db $03,$02,$02,$83,$04,$02,$02,$03,$03,$0F,$81,$02,$01,$00,$00,$01 ; ROM 18A08
    db $01,$02,$03,$04,$05,$81,$07,$07,$06,$06,$05,$05,$04,$04,$03,$03 ; ROM 18A18
    db $02,$02,$02,$01,$01,$01,$82,$00,$00,$01,$02,$03,$04,$03,$02,$01 ; ROM 18A28
    db $00,$82,$01,$02,$04,$07,$81,$02,$02,$03,$03,$06,$06,$81,$00,$00 ; ROM 18A38
    db $00,$01,$01,$02,$02,$03,$03,$03,$04,$81,$62,$8A,$79,$8A,$92,$8A ; ROM 18A48
    db $AA,$8A,$B3,$8A,$BA,$8A,$C0,$8A,$CB,$8A,$01,$01,$01,$01,$01,$01 ; ROM 18A58
    db $01,$01,$01,$01,$00,$00,$01,$01,$01,$01,$01,$01,$00,$00,$01,$00 ; ROM 18A68
    db $80,$00,$00,$01,$00,$03,$00,$01,$01,$01,$00,$00,$01,$02,$03,$02 ; ROM 18A78
    db $02,$02,$01,$00,$00,$00,$01,$03,$07,$02,$00,$01,$02,$03,$05,$03 ; ROM 18A88
    db $01,$00,$01,$02,$04,$02,$01,$00,$01,$02,$03,$05,$03,$02,$01,$00 ; ROM 18A98
    db $83,$40,$00,$50,$00,$01,$01,$00,$00,$83,$04,$57,$18,$11,$00,$3F ; ROM 18AA8
    db $01,$80,$11,$41,$01,$41,$01,$80,$00,$00,$01,$02,$01,$00,$00,$FF ; ROM 18AB8
    db $FE,$FF,$80,$00,$00,$00,$01,$01,$00,$00,$FF,$FF,$80,$80,$80,$80 ; ROM 18AC8
    db $80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$80,$20,$30,$60,$60 ; ROM 18AD8
    db $60,$25,$65,$60,$25,$20,$68,$40,$50,$45,$68,$25,$67,$68,$30,$50 ; ROM 18AE8
    db $50,$25,$68,$68,$68,$50,$50,$65,$70,$20,$70,$00,$80,$80,$80,$80 ; ROM 18AF8
    db $00,$04,$05,$06,$00,$00,$03,$00,$06,$05,$08,$03,$10,$00,$6A,$8B ; ROM 18B08
    db $68,$8C,$3F,$8E,$83,$8F,$BE,$90,$9E,$91,$FD,$92,$ED,$93,$80,$95 ; ROM 18B18
    db $0F,$96,$79,$96,$AF,$99,$F7,$99,$41,$9A,$56,$9A,$67,$9A,$8E,$9A ; ROM 18B28
    db $BB,$9A,$D0,$9A,$DE,$9A,$F5,$9A,$0A,$9B,$21,$9B,$34,$9B,$4E,$9B ; ROM 18B38
    db $63,$9B,$78,$9B,$8C,$9B,$D9,$9B,$EC,$9B,$09,$9C,$19,$9C,$35,$9C ; ROM 18B48
    db $50,$9C,$8B,$9C,$AE,$9C,$CE,$9C,$E2,$9C,$01,$9D,$1C,$9D,$31,$9D ; ROM 18B58
    db $4B,$9D,$04,$80,$80,$01,$8F,$8B,$D3,$00,$08,$02,$80,$A0,$01,$C3 ; ROM 18B68
    db $8B,$D3,$00,$02,$04,$80,$C0,$01,$00,$8C,$D3,$00,$05,$04,$80,$E0 ; ROM 18B78
    db $01,$41,$8C,$00,$00,$00,$0F,$C6,$18,$CE,$0C,$CD,$C9,$C6,$18,$80 ; ROM 18B88
    db $06,$CB,$E7,$18,$C6,$0C,$E7,$06,$C4,$E7,$30,$C4,$0C,$C7,$18,$D0 ; ROM 18B98
    db $0C,$E7,$0C,$CE,$CD,$C6,$CB,$0C,$CB,$06,$06,$80,$0C,$CD,$0C,$CD ; ROM 18BA8
    db $06,$06,$80,$0C,$C9,$06,$CD,$CB,$0C,$80,$F1,$B3,$06,$03,$03,$F7 ; ROM 18BB8
    db $00,$04,$C3,$8B,$F7,$01,$02,$C3,$8B,$F8,$F6,$8B,$F8,$F6,$8B,$AF ; ROM 18BC8
    db $06,$03,$03,$F7,$00,$04,$D7,$8B,$F8,$F6,$8B,$AE,$0C,$06,$06,$80 ; ROM 18BD8
    db $0C,$B1,$B1,$06,$06,$80,$0C,$AE,$06,$06,$B3,$0C,$80,$F2,$B1,$06 ; ROM 18BE8
    db $03,$03,$F7,$00,$04,$F6,$8B,$F9,$80,$06,$BF,$C2,$C6,$CB,$C6,$C2 ; ROM 18BF8
    db $BF,$F7,$00,$02,$00,$8C,$80,$06,$BD,$C0,$C4,$C9,$C4,$C0,$BD,$F7 ; ROM 18C08
    db $00,$02,$0E,$8C,$80,$06,$C1,$C4,$C7,$CD,$C7,$C4,$C1,$80,$06,$BE ; ROM 18C18
    db $C1,$C6,$CA,$C6,$C1,$BE,$C2,$0C,$06,$06,$80,$0C,$C4,$C4,$06,$06 ; ROM 18C28
    db $80,$0C,$C1,$06,$C4,$C2,$0C,$80,$F2,$84,$03,$81,$81,$81,$88,$06 ; ROM 18C38
    db $81,$03,$03,$F7,$00,$02,$41,$8C,$F7,$01,$06,$41,$8C,$88,$06,$81 ; ROM 18C48
    db $88,$88,$81,$81,$88,$81,$88,$88,$81,$81,$88,$88,$88,$0C,$80,$F2 ; ROM 18C58
    db $04,$80,$80,$01,$8D,$8C,$CF,$00,$10,$03,$80,$A0,$01,$1B,$8D,$CF ; ROM 18C68
    db $00,$07,$05,$80,$C0,$01,$BD,$8D,$CF,$00,$08,$04,$80,$E0,$01,$37 ; ROM 18C78
    db $8E,$00,$00,$00,$0F,$C8,$0C,$C6,$06,$C4,$1E,$C9,$0C,$C8,$06,$C6 ; ROM 18C88
    db $12,$C9,$0C,$C8,$24,$CB,$0C,$C8,$24,$80,$0C,$F7,$00,$02,$8D,$8C ; ROM 18C98
    db $C1,$18,$C3,$0C,$C4,$C6,$C4,$C3,$C1,$C3,$24,$C4,$0C,$C3,$12,$BF ; ROM 18CA8
    db $1E,$C3,$24,$C4,$0C,$C3,$12,$BF,$C1,$0C,$24,$C3,$0C,$C1,$24,$80 ; ROM 18CB8
    db $0C,$C1,$18,$C3,$0C,$C4,$C8,$C4,$C3,$C1,$C6,$24,$CB,$0C,$C6,$24 ; ROM 18CC8
    db $C8,$0C,$C9,$12,$C4,$C9,$0C,$CD,$12,$C9,$CD,$0C,$CF,$24,$D0,$0C ; ROM 18CD8
    db $CF,$12,$CC,$1E,$CD,$06,$D4,$D0,$CD,$E7,$18,$CD,$06,$D4,$D0,$CD ; ROM 18CE8
    db $E7,$18,$CD,$24,$CF,$0C,$CD,$12,$CB,$1E,$CD,$06,$D4,$D0,$CD,$E7 ; ROM 18CF8
    db $18,$CD,$06,$D4,$D0,$CD,$E7,$18,$D0,$0C,$CD,$C9,$CD,$CF,$18,$CB ; ROM 18D08
    db $F6,$8D,$8C,$F8,$AA,$8D,$F8,$6A,$8D,$F7,$01,$02,$1B,$8D,$F8,$6A ; ROM 18D18
    db $8D,$F8,$79,$8D,$F8,$79,$8D,$F8,$6A,$8D,$F8,$6A,$8D,$F8,$79,$8D ; ROM 18D28
    db $F8,$88,$8D,$F8,$97,$8D,$B5,$0C,$BC,$06,$B5,$80,$B5,$BC,$B5,$B3 ; ROM 18D38
    db $0C,$BA,$06,$B3,$80,$B3,$BA,$B3,$B1,$0C,$B8,$06,$B1,$80,$B1,$B8 ; ROM 18D48
    db $B1,$B3,$0C,$BA,$06,$B3,$80,$B3,$BA,$B3,$F7,$00,$02,$3E,$8D,$F6 ; ROM 18D58
    db $1B,$8D,$B5,$0C,$BC,$06,$B5,$80,$B5,$BC,$B5,$F7,$00,$02,$6A,$8D ; ROM 18D68
    db $F9,$B3,$0C,$BA,$06,$B3,$80,$B3,$BA,$B3,$F7,$00,$02,$79,$8D,$F9 ; ROM 18D78
    db $B1,$0C,$B8,$06,$B1,$80,$B1,$B8,$B1,$F7,$00,$02,$88,$8D,$F9,$B3 ; ROM 18D88
    db $0C,$BA,$06,$B3,$80,$B3,$BA,$B3,$B4,$0C,$BA,$06,$B4,$80,$B4,$BA ; ROM 18D98
    db $B4,$F9,$B5,$0C,$BC,$06,$B5,$80,$B5,$BC,$B5,$B6,$0C,$BD,$06,$B6 ; ROM 18DA8
    db $80,$B6,$BD,$B6,$F9,$C1,$30,$C2,$24,$C4,$0C,$C1,$24,$C4,$0C,$C1 ; ROM 18DB8
    db $30,$C1,$30,$C2,$12,$C4,$BF,$0C,$C1,$24,$BC,$0C,$C1,$30,$BC,$30 ; ROM 18DC8
    db $E7,$30,$BA,$E6,$02,$BF,$12,$C1,$BF,$0C,$BA,$30,$BF,$12,$C1,$BD ; ROM 18DD8
    db $0C,$BC,$24,$BD,$0C,$BC,$30,$E6,$FE,$BC,$18,$BF,$0C,$C1,$C3,$C1 ; ROM 18DE8
    db $BF,$BC,$BF,$24,$BA,$0C,$BF,$24,$80,$0C,$C1,$18,$BF,$BD,$BC,$BA ; ROM 18DF8
    db $30,$BC,$C8,$30,$E7,$30,$80,$06,$C1,$C3,$C4,$C6,$C4,$C3,$C4,$C6 ; ROM 18E08
    db $C4,$C6,$C8,$C9,$C8,$C9,$CB,$C8,$30,$E7,$30,$80,$06,$C1,$C3,$C4 ; ROM 18E18
    db $C6,$C4,$C6,$C8,$C9,$C8,$C6,$C8,$C9,$CB,$CD,$CF,$F6,$BD,$8D,$84 ; ROM 18E28
    db $06,$81,$88,$84,$F6,$37,$8E,$04,$80,$80,$02,$64,$8E,$CE,$00,$10 ; ROM 18E38
    db $03,$80,$A0,$02,$CE,$8E,$CE,$00,$0B,$02,$80,$C0,$02,$15,$8F,$CE ; ROM 18E48
    db $02,$10,$07,$80,$E0,$02,$5E,$8F,$00,$00,$00,$0F,$C8,$18,$C5,$C2 ; ROM 18E58
    db $03,$C1,$06,$BD,$03,$BC,$24,$80,$30,$BC,$18,$BF,$08,$BC,$BA,$BC ; ROM 18E68
    db $03,$BA,$BC,$06,$E7,$24,$BC,$18,$BF,$06,$C1,$BD,$BA,$BC,$03,$BA ; ROM 18E78
    db $BC,$06,$E7,$24,$C5,$03,$C8,$C2,$06,$E7,$18,$C1,$0C,$80,$03,$C3 ; ROM 18E88
    db $C4,$06,$E7,$18,$80,$0C,$03,$C3,$C4,$06,$E7,$18,$C6,$0C,$C8,$03 ; ROM 18E98
    db $C6,$C8,$06,$E7,$24,$C3,$03,$C6,$C2,$C5,$F7,$00,$04,$AD,$8E,$FB ; ROM 18EA8
    db $01,$F7,$01,$03,$AD,$8E,$FB,$FD,$C6,$03,$C9,$C5,$C8,$C6,$C9,$C5 ; ROM 18EB8
    db $C8,$C1,$18,$F6,$71,$8E,$80,$30,$80,$18,$B5,$0C,$0C,$B5,$0C,$0C ; ROM 18EC8
    db $0C,$0C,$E6,$03,$B5,$0C,$0C,$0C,$0C,$F7,$00,$04,$DC,$8E,$B3,$0C ; ROM 18ED8
    db $0C,$0C,$0C,$B5,$0C,$0C,$0C,$0C,$B5,$0C,$0C,$0C,$0C,$BC,$0C,$0C ; ROM 18EE8
    db $0C,$0C,$FB,$0C,$AE,$0C,$AD,$AC,$AB,$AF,$0C,$AE,$AD,$AC,$B0,$0C ; ROM 18EF8
    db $AF,$AE,$AD,$AC,$0C,$AB,$AA,$A9,$FB,$F4,$F6,$DC,$8E,$80,$01,$C8 ; ROM 18F08
    db $18,$C5,$C2,$03,$C1,$06,$BD,$03,$BC,$23,$E6,$FE,$F5,$06,$F4,$01 ; ROM 18F18
    db $CD,$30,$CD,$18,$CE,$12,$CB,$06,$CD,$30,$F7,$00,$02,$2A,$8F,$CB ; ROM 18F28
    db $18,$C9,$C8,$30,$E7,$18,$C9,$C8,$30,$80,$06,$CE,$F7,$00,$04,$41 ; ROM 18F38
    db $8F,$FB,$01,$F7,$01,$03,$41,$8F,$FB,$FD,$80,$06,$CE,$80,$CE,$80 ; ROM 18F48
    db $CE,$80,$CE,$F6,$2A,$8F,$80,$30,$81,$0C,$81,$81,$81,$84,$84,$84 ; ROM 18F58
    db $84,$84,$06,$84,$88,$84,$F7,$00,$10,$69,$8F,$84,$06,$81,$80,$03 ; ROM 18F68
    db $81,$88,$06,$F7,$00,$08,$73,$8F,$F6,$69,$8F,$04,$80,$80,$02,$A8 ; ROM 18F78
    db $8F,$D6,$00,$0F,$02,$80,$A0,$02,$F4,$8F,$D6,$00,$0E,$03,$80,$C0 ; ROM 18F88
    db $02,$4D,$90,$D6,$00,$0F,$03,$80,$E0,$02,$99,$90,$00,$00,$00,$0F ; ROM 18F98
    db $80,$0C,$C1,$80,$C2,$80,$C1,$80,$06,$C6,$C5,$C2,$80,$0C,$C1,$80 ; ROM 18FA8
    db $C2,$80,$C1,$80,$06,$C1,$C0,$C1,$F7,$00,$02,$A8,$8F,$F8,$E5,$8F ; ROM 18FB8
    db $80,$0C,$C1,$80,$C2,$80,$06,$C1,$BF,$BD,$BF,$C1,$C2,$C1,$F8,$E5 ; ROM 18FC8
    db $8F,$80,$0C,$C5,$80,$C6,$80,$C8,$80,$18,$F6,$A8,$8F,$80,$0C,$C2 ; ROM 18FD8
    db $80,$C5,$80,$C6,$06,$C8,$C9,$0C,$C8,$06,$C6,$F9,$BA,$0C,$80,$BA ; ROM 18FE8
    db $80,$BA,$80,$BA,$80,$BA,$80,$BA,$80,$BA,$80,$BA,$B9,$06,$BA,$AE ; ROM 18FF8
    db $0C,$BA,$06,$AE,$AE,$0C,$BA,$06,$AE,$F7,$00,$04,$07,$90,$F8,$3D ; ROM 19008
    db $90,$AE,$0C,$B5,$06,$AE,$AE,$0C,$B5,$06,$AE,$F7,$00,$02,$19,$90 ; ROM 19018
    db $F8,$3D,$90,$B5,$0C,$BC,$06,$B5,$B5,$0C,$BC,$06,$B5,$F7,$00,$02 ; ROM 19028
    db $2B,$90,$F6,$F4,$8F,$B3,$0C,$BA,$06,$B3,$B3,$0C,$BA,$06,$B3,$F7 ; ROM 19038
    db $00,$02,$3D,$90,$F9,$80,$0C,$BE,$80,$BF,$80,$BE,$80,$06,$C1,$C0 ; ROM 19048
    db $BF,$80,$0C,$BE,$80,$BF,$80,$BE,$80,$06,$BE,$BD,$BE,$F7,$00,$02 ; ROM 19058
    db $4D,$90,$F8,$8A,$90,$80,$0C,$BD,$80,$BF,$80,$06,$BD,$BA,$B8,$BA ; ROM 19068
    db $BD,$BD,$BD,$F8,$8A,$90,$80,$0C,$C1,$80,$C2,$80,$C5,$80,$18,$F6 ; ROM 19078
    db $4D,$90,$80,$0C,$BF,$80,$C1,$80,$C2,$06,$C5,$C6,$0C,$C5,$06,$C2 ; ROM 19088
    db $F9,$80,$18,$81,$06,$80,$12,$81,$06,$80,$12,$81,$06,$80,$81,$81 ; ROM 19098
    db $F7,$00,$02,$99,$90,$81,$06,$80,$88,$81,$81,$80,$88,$80,$F7,$00 ; ROM 190A8
    db $0C,$AD,$90,$F6,$99,$90,$04,$80,$80,$02,$E3,$90,$E4,$00,$10,$03 ; ROM 190B8
    db $80,$A0,$02,$0E,$91,$E4,$00,$08,$04,$80,$C0,$02,$58,$91,$E4,$00 ; ROM 190C8
    db $0B,$03,$80,$E0,$02,$8C,$91,$00,$00,$00,$0F,$B6,$12,$B7,$B8,$B9 ; ROM 190D8
    db $BA,$0C,$BB,$BA,$30,$B1,$18,$B3,$B8,$B5,$B3,$B8,$B3,$24,$B5,$0C ; ROM 190E8
    db $B3,$09,$B1,$03,$B1,$24,$80,$0C,$AE,$B0,$B1,$B3,$18,$B5,$B3,$0C ; ROM 190F8
    db $B1,$B0,$B1,$F6,$ED,$90,$F5,$10,$B1,$12,$B2,$B3,$B4,$B5,$0C,$B6 ; ROM 19108
    db $F5,$08,$A2,$09,$03,$09,$03,$09,$03,$09,$03,$A2,$09,$03,$09,$03 ; ROM 19118
    db $09,$03,$09,$03,$FB,$FE,$F8,$49,$91,$FB,$FE,$F8,$49,$91,$A2,$09 ; ROM 19128
    db $03,$09,$03,$09,$03,$09,$03,$FB,$02,$F8,$49,$91,$FB,$02,$F6,$23 ; ROM 19138
    db $91,$A2,$09,$03,$09,$03,$09,$03,$09,$03,$F7,$00,$02,$49,$91,$F9 ; ROM 19148
    db $F5,$10,$AD,$12,$AE,$AF,$B0,$B1,$0C,$B2,$B5,$30,$FB,$E8,$F5,$0B ; ROM 19158
    db $B5,$30,$BC,$18,$BA,$0C,$B8,$BC,$18,$BF,$C2,$24,$C4,$0C,$C2,$09 ; ROM 19168
    db $C1,$03,$C1,$24,$BF,$0C,$C1,$BF,$BD,$C2,$18,$BD,$BC,$0C,$BA,$B8 ; ROM 19178
    db $B6,$F6,$68,$91,$88,$12,$12,$12,$12,$0C,$0C,$84,$09,$81,$03,$88 ; ROM 19188
    db $09,$81,$03,$F6,$93,$91,$04,$80,$80,$01,$C3,$91,$D2,$00,$10,$03 ; ROM 19198
    db $80,$A0,$01,$28,$92,$D2,$00,$02,$05,$80,$C0,$01,$68,$92,$D2,$00 ; ROM 191A8
    db $05,$04,$80,$E0,$01,$F1,$92,$00,$00,$00,$0F,$CD,$18,$CE,$12,$D0 ; ROM 191B8
    db $06,$CD,$24,$80,$0C,$CE,$18,$D0,$12,$CE,$06,$CD,$30,$CD,$18,$CE ; ROM 191C8
    db $12,$D0,$06,$CD,$24,$80,$0C,$D4,$18,$D2,$CD,$30,$E6,$01,$CE,$03 ; ROM 191D8
    db $CB,$C6,$C2,$C6,$C5,$C5,$C9,$CD,$CC,$CC,$D2,$CE,$CB,$C8,$C5,$C9 ; ROM 191E8
    db $C8,$CD,$C9,$C6,$C1,$C9,$C8,$C6,$C8,$C9,$C8,$C9,$CB,$CE,$CD,$F7 ; ROM 191F8
    db $00,$02,$E6,$91,$E6,$FF,$E6,$FF,$BF,$18,$BA,$12,$C2,$06,$C1,$0C ; ROM 19208
    db $BC,$18,$C1,$0C,$18,$BF,$C2,$0C,$BA,$C2,$C1,$E6,$01,$F6,$C3,$91 ; ROM 19218
    db $AE,$06,$03,$03,$06,$03,$03,$06,$03,$03,$80,$AE,$AE,$AE,$F7,$00 ; ROM 19228
    db $08,$28,$92,$E6,$FD,$B3,$06,$03,$03,$06,$03,$03,$06,$03,$03,$80 ; ROM 19238
    db $B3,$B3,$B3,$F7,$00,$04,$3D,$92,$E6,$03,$B3,$06,$03,$03,$06,$03 ; ROM 19248
    db $03,$06,$03,$03,$80,$B3,$B3,$B3,$F7,$00,$04,$52,$92,$F6,$28,$92 ; ROM 19258
    db $F5,$05,$80,$03,$BD,$BA,$B5,$F7,$00,$08,$68,$92,$80,$03,$BF,$BA ; ROM 19268
    db $B6,$F7,$00,$04,$74,$92,$80,$03,$BD,$BA,$B5,$F7,$00,$0C,$7E,$92 ; ROM 19278
    db $80,$03,$BF,$BA,$B6,$F7,$00,$04,$88,$92,$80,$03,$BD,$BA,$B5,$F7 ; ROM 19288
    db $00,$04,$92,$92,$F5,$07,$E6,$01,$CB,$03,$C8,$C3,$BF,$C3,$C2,$C2 ; ROM 19298
    db $C6,$CA,$C9,$C9,$CF,$CB,$C8,$C5,$C2,$C6,$C5,$CA,$C6,$C3,$BE,$C6 ; ROM 192A8
    db $C5,$C3,$C5,$C6,$C5,$C6,$C8,$CB,$CA,$F7,$00,$02,$A0,$92,$E6,$FF ; ROM 192B8
    db $CE,$03,$CB,$C6,$C2,$C6,$C5,$C5,$C9,$CD,$CC,$CC,$D2,$CE,$CB,$C8 ; ROM 192C8
    db $C5,$C9,$C8,$CD,$C9,$C6,$C1,$C9,$C8,$C6,$C8,$C9,$C8,$C9,$CB,$CE ; ROM 192D8
    db $CD,$F7,$00,$02,$C8,$92,$F6,$68,$92,$84,$0C,$88,$06,$84,$0C,$06 ; ROM 192E8
    db $88,$84,$F6,$F1,$92,$04,$80,$80,$02,$22,$93,$D4,$00,$10,$03,$80 ; ROM 192F8
    db $A0,$02,$56,$93,$D4,$00,$06,$05,$80,$C0,$02,$8B,$93,$D4,$00,$08 ; ROM 19308
    db $04,$80,$E0,$02,$C8,$93,$00,$00,$00,$0F,$C4,$0C,$C9,$12,$C8,$06 ; ROM 19318
    db $C9,$0C,$CB,$CD,$12,$C9,$06,$C4,$0C,$0C,$C6,$C4,$C6,$C8,$C9,$18 ; ROM 19328
    db $80,$0C,$C4,$F7,$00,$02,$24,$93,$D5,$0C,$D2,$D5,$D2,$D4,$D0,$18 ; ROM 19338
    db $80,$0C,$D5,$D2,$D5,$D2,$D4,$D7,$18,$C4,$0C,$F6,$24,$93,$80,$0C ; ROM 19348
    db $C1,$0C,$BF,$C1,$C2,$C4,$C1,$BD,$C1,$C2,$C1,$C2,$C4,$C1,$C4,$C1 ; ROM 19358
    db $80,$F7,$00,$02,$58,$93,$C2,$0C,$06,$C4,$C6,$0C,$C2,$C4,$C8,$C6 ; ROM 19368
    db $C4,$C2,$C2,$06,$C4,$C6,$0C,$C2,$C4,$06,$C2,$C1,$C2,$C4,$0C,$80 ; ROM 19378
    db $F6,$58,$93,$80,$0C,$B5,$0C,$B6,$B8,$18,$B1,$0C,$B3,$B5,$18,$AE ; ROM 19388
    db $0C,$B3,$B1,$06,$B0,$AE,$B0,$B1,$0C,$B8,$B1,$80,$F7,$00,$02,$8D ; ROM 19398
    db $93,$B3,$0C,$06,$B5,$B6,$0C,$80,$B5,$B5,$06,$B6,$B8,$0C,$80,$B6 ; ROM 193A8
    db $B6,$06,$B8,$BA,$0C,$80,$B8,$B8,$06,$BA,$BC,$0C,$80,$F6,$8D,$93 ; ROM 193B8
    db $80,$0C,$81,$0C,$0C,$0C,$0C,$F7,$00,$03,$CA,$93,$88,$0C,$0C,$81 ; ROM 193C8
    db $06,$06,$06,$06,$80,$06,$81,$88,$81,$80,$81,$88,$81,$F7,$00,$08 ; ROM 193D8
    db $DC,$93,$F6,$CA,$93,$04,$80,$80,$02,$12,$94,$D1,$00,$10,$02,$80 ; ROM 193E8
    db $A0,$02,$8F,$94,$D1,$00,$05,$04,$80,$C0,$02,$00,$95,$D1,$00,$08 ; ROM 193F8
    db $05,$80,$E0,$02,$52,$95,$00,$00,$00,$0F,$C8,$18,$08,$C9,$C8,$C6 ; ROM 19408
    db $18,$CB,$08,$CD,$CB,$CB,$18,$C9,$12,$C8,$06,$C9,$24,$0C,$18,$CB ; ROM 19418
    db $0C,$C9,$C8,$CB,$D0,$C8,$C8,$18,$C6,$12,$C8,$06,$C6,$30,$C8,$18 ; ROM 19428
    db $08,$C9,$C8,$CB,$18,$08,$CD,$CB,$D0,$12,$CD,$06,$18,$D0,$12,$CC ; ROM 19438
    db $06,$D0,$0C,$D2,$D4,$D0,$CB,$D0,$CF,$18,$CD,$12,$CF,$06,$D0,$30 ; ROM 19448
    db $E7,$30,$CD,$24,$CF,$06,$D0,$D0,$30,$CD,$24,$CF,$06,$D2,$D0,$30 ; ROM 19458
    db $ED,$05,$CD,$18,$CF,$0C,$D0,$ED,$04,$CB,$02,$D0,$D4,$03,$E7,$11 ; ROM 19468
    db $ED,$03,$D0,$02,$D4,$D7,$03,$E7,$11,$ED,$06,$D5,$0C,$D2,$CF,$CD ; ROM 19478
    db $CB,$CD,$CB,$C9,$F6,$12,$94,$B8,$0C,$B8,$B8,$B8,$B7,$B7,$B7,$B7 ; ROM 19488
    db $B6,$B6,$B6,$B6,$B5,$B5,$B5,$B5,$B4,$B4,$B4,$B4,$B3,$B3,$B3,$B3 ; ROM 19498
    db $B1,$B1,$B1,$B1,$B3,$B3,$B3,$B3,$B8,$0C,$B8,$B8,$B8,$B6,$B6,$B6 ; ROM 194A8
    db $B6,$B5,$B5,$B5,$B5,$B4,$B4,$B4,$B4,$B3,$B3,$B3,$B3,$B3,$B3,$B3 ; ROM 194B8
    db $B3,$B8,$B8,$B8,$B8,$B8,$B8,$B8,$B8,$80,$06,$B1,$B5,$B8,$BD,$18 ; ROM 194C8
    db $80,$06,$B8,$BC,$BF,$C4,$18,$80,$06,$B1,$B5,$B8,$BD,$18,$B0,$06 ; ROM 194D8
    db $B3,$B8,$BC,$BF,$C4,$C8,$CB,$C4,$18,$C0,$BC,$C4,$B3,$0C,$0C,$0C ; ROM 194E8
    db $0C,$0C,$0C,$0C,$0C,$F6,$8F,$94,$BF,$18,$18,$18,$C6,$C4,$C4,$C4 ; ROM 194F8
    db $C4,$C4,$C4,$C4,$BF,$C1,$C1,$C3,$C3,$BF,$BF,$C4,$C4,$C9,$C9,$C9 ; ROM 19508
    db $C9,$C4,$0C,$CB,$C8,$CB,$C6,$CB,$C9,$CB,$C9,$18,$CB,$0C,$C9,$E6 ; ROM 19518
    db $FE,$C8,$18,$C9,$0C,$CB,$E6,$02,$C9,$0C,$C8,$C9,$CB,$C8,$CB,$CA ; ROM 19528
    db $CB,$C9,$C4,$C1,$C4,$C8,$C8,$C9,$CB,$C9,$18,$18,$C4,$C8,$CB,$0C ; ROM 19538
    db $C9,$CB,$C9,$C9,$C9,$C8,$C6,$F6,$00,$95,$81,$0C,$81,$81,$81,$F7 ; ROM 19548
    db $00,$08,$52,$95,$81,$06,$81,$88,$81,$F7,$00,$10,$5C,$95,$82,$0C ; ROM 19558
    db $80,$24,$F7,$00,$06,$66,$95,$81,$0C,$81,$81,$81,$81,$06,$81,$88 ; ROM 19568
    db $81,$81,$81,$88,$81,$F6,$52,$95,$04,$80,$80,$01,$A5,$95,$D4,$00 ; ROM 19578
    db $05,$03,$80,$A0,$01,$CF,$95,$C8,$00,$05,$04,$80,$C0,$01,$F7,$95 ; ROM 19588
    db $EC,$00,$0F,$03,$80,$E0,$01,$0A,$96,$00,$00,$00,$0F,$F0,$01,$02 ; ROM 19598
    db $01,$08,$80,$08,$C1,$C6,$BF,$C1,$C6,$F7,$00,$04,$AA,$95,$80,$C1 ; ROM 195A8
    db $C8,$C2,$C5,$C8,$F7,$00,$02,$B6,$95,$80,$C1,$C9,$C6,$C8,$C9,$F7 ; ROM 195B8
    db $00,$02,$C1,$95,$F6,$AA,$95,$F8,$EC,$95,$B8,$0C,$80,$B8,$80,$F7 ; ROM 195C8
    db $00,$02,$D2,$95,$BC,$0C,$80,$BC,$80,$F7,$00,$02,$DC,$95,$F8,$EC ; ROM 195D8
    db $95,$F6,$CF,$95,$BA,$0C,$80,$BA,$80,$F7,$00,$02,$EC,$95,$F9,$B5 ; ROM 195E8
    db $30,$B6,$B3,$30,$E7,$30,$B6,$30,$BC,$18,$BD,$BA,$30,$E7,$30,$F6 ; ROM 195F8
    db $F7,$95,$80,$30,$F6,$0A,$96,$04,$80,$80,$02,$34,$96,$DA,$00,$08 ; ROM 19608
    db $02,$80,$A0,$02,$4A,$96,$DA,$00,$08,$04,$80,$C0,$02,$60,$96,$DA ; ROM 19618
    db $00,$08,$04,$80,$E0,$02,$71,$96,$00,$00,$00,$0F,$C4,$06,$C7,$CB ; ROM 19628
    db $D0,$CE,$CC,$CB,$C9,$CC,$CB,$C9,$C7,$CB,$C9,$C7,$C6,$C4,$30,$E7 ; ROM 19638
    db $18,$F1,$AF,$0C,$AE,$06,$AC,$A8,$0C,$AD,$AC,$AA,$06,$A8,$A7,$0C ; ROM 19648
    db $AC,$06,$AB,$A7,$18,$A8,$A7,$F2,$BB,$18,$BD,$BF,$C0,$C4,$06,$C2 ; ROM 19658
    db $C0,$BF,$BD,$BB,$BA,$BB,$B8,$18,$F2,$80,$30,$F7,$00,$04,$71,$96 ; ROM 19668
    db $F2,$04,$80,$80,$01,$9E,$96,$D2,$00,$08,$03,$80,$A0,$01,$48,$97 ; ROM 19678
    db $DE,$00,$04,$05,$80,$C0,$01,$79,$98,$D2,$00,$05,$04,$80,$E0,$01 ; ROM 19688
    db $05,$99,$00,$00,$00,$0F,$F8,$21,$97,$80,$06,$C9,$C8,$CB,$C9,$C8 ; ROM 19698
    db $C6,$C4,$C6,$C8,$80,$C9,$1E,$80,$06,$C9,$C8,$CB,$C9,$C8,$C6,$C4 ; ROM 196A8
    db $C6,$C8,$80,$C6,$1E,$C8,$30,$E7,$18,$C8,$0C,$C4,$06,$C6,$36,$C4 ; ROM 196B8
    db $06,$C3,$BF,$C1,$0C,$BD,$12,$F7,$00,$02,$A1,$96,$F8,$21,$97,$80 ; ROM 196C8
    db $30,$80,$30,$C8,$24,$C6,$06,$C8,$06,$C4,$2D,$C3,$15,$BF,$12,$C1 ; ROM 196D8
    db $30,$C8,$0C,$CB,$24,$CD,$0C,$CA,$12,$C6,$12,$CA,$0C,$C8,$30,$E7 ; ROM 196E8
    db $24,$80,$0C,$F7,$00,$02,$D7,$96,$F8,$21,$97,$D2,$09,$D2,$D2,$06 ; ROM 196F8
    db $D4,$0C,$D0,$D4,$09,$D2,$27,$D2,$09,$D2,$D5,$06,$D4,$0C,$D7,$D9 ; ROM 19708
    db $30,$F7,$00,$02,$03,$97,$F6,$9E,$96,$C6,$24,$C9,$03,$C8,$C9,$CB ; ROM 19718
    db $CD,$30,$CB,$24,$C4,$0C,$C9,$03,$C8,$C6,$2A,$C6,$24,$C9,$03,$C8 ; ROM 19728
    db $C9,$CB,$CD,$30,$CB,$24,$C4,$0C,$C6,$30,$F7,$00,$02,$21,$97,$F9 ; ROM 19738
    db $F8,$1B,$98,$AE,$03,$AE,$80,$AE,$A2,$06,$AE,$03,$AE,$80,$03,$AE ; ROM 19748
    db $A2,$06,$AE,$A2,$AE,$03,$AE,$80,$AE,$A2,$06,$AE,$03,$AE,$80,$03 ; ROM 19758
    db $AE,$A2,$06,$AE,$A2,$AA,$03,$AA,$80,$AA,$A5,$06,$AA,$03,$AA,$80 ; ROM 19768
    db $AA,$A5,$06,$AA,$A9,$AA,$03,$AA,$80,$AA,$A5,$06,$AA,$03,$AA,$80 ; ROM 19778
    db $AA,$A5,$06,$AA,$A9,$AC,$03,$AC,$80,$AC,$A7,$06,$AC,$03,$AC,$80 ; ROM 19788
    db $03,$AC,$A7,$06,$AC,$A7,$AC,$03,$AC,$80,$AC,$A7,$06,$AC,$03,$AC ; ROM 19798
    db $80,$03,$AC,$A7,$06,$AC,$AC,$AE,$03,$AE,$80,$AE,$A9,$06,$AE,$03 ; ROM 197A8
    db $AE,$80,$03,$AE,$A9,$06,$AE,$A9,$AE,$03,$AE,$80,$AE,$A9,$06,$AE ; ROM 197B8
    db $03,$AE,$80,$03,$AE,$A9,$06,$AE,$AE,$F7,$00,$02,$4B,$97,$F8,$1B ; ROM 197C8
    db $98,$A9,$06,$A9,$A9,$A9,$0C,$A9,$06,$A9,$A9,$F7,$00,$14,$D9,$97 ; ROM 197D8
    db $F8,$1B,$98,$AA,$09,$AA,$AA,$06,$AC,$09,$AC,$AC,$06,$AE,$09,$AE ; ROM 197E8
    db $AE,$06,$AE,$09,$AE,$AC,$06,$AA,$09,$AA,$AA,$06,$AC,$09,$AC,$AC ; ROM 197F8
    db $06,$AE,$09,$AE,$AE,$06,$AE,$09,$AE,$AE,$06,$F7,$00,$02,$EB,$97 ; ROM 19808
    db $F6,$48,$97,$AE,$09,$AE,$AE,$0C,$AE,$06,$AE,$03,$AC,$09,$AA,$09 ; ROM 19818
    db $AA,$AA,$0C,$AA,$06,$AA,$03,$AA,$09,$AC,$09,$AC,$AC,$0C,$AC,$06 ; ROM 19828
    db $AC,$03,$AC,$09,$AE,$09,$AE,$AE,$0C,$AE,$06,$AE,$03,$AC,$09,$AE ; ROM 19838
    db $09,$AE,$AE,$0C,$AE,$06,$AE,$03,$AC,$09,$AA,$09,$AA,$AA,$0C,$AA ; ROM 19848
    db $06,$AC,$03,$AA,$09,$AC,$09,$AC,$AC,$0C,$AC,$06,$AC,$03,$AC,$09 ; ROM 19858
    db $AE,$09,$AE,$AE,$0C,$AE,$06,$AE,$03,$AC,$09,$F7,$00,$02,$1B,$98 ; ROM 19868
    db $F9,$F8,$E1,$98,$80,$06,$C6,$C4,$C6,$80,$C8,$12,$C9,$06,$CB,$80 ; ROM 19878
    db $CD,$1E,$80,$06,$C6,$C4,$C6,$80,$C8,$12,$C9,$0C,$C8,$06,$C6,$1E ; ROM 19888
    db $C8,$30,$E7,$18,$C8,$0C,$C4,$06,$C6,$36,$D0,$06,$CF,$CB,$CD,$0C ; ROM 19898
    db $C9,$12,$F7,$00,$02,$7C,$98,$F8,$E1,$98,$C1,$06,$BF,$C1,$C2,$C4 ; ROM 198A8
    db $C2,$C1,$BF,$F7,$00,$14,$B2,$98,$F8,$E1,$98,$CE,$09,$CE,$CE,$06 ; ROM 198B8
    db $D0,$0C,$CB,$CD,$09,$CD,$27,$CE,$09,$CE,$D2,$06,$D0,$0C,$D4,$D2 ; ROM 198C8
    db $30,$F7,$00,$02,$C3,$98,$F6,$79,$98,$C6,$09,$C8,$06,$80,$03,$C9 ; ROM 198D8
    db $1E,$C6,$09,$C8,$06,$80,$03,$C9,$1E,$C8,$09,$C9,$06,$80,$03,$CB ; ROM 198E8
    db $12,$C4,$0C,$C8,$09,$C6,$27,$F7,$00,$04,$E1,$98,$F9,$F8,$54,$99 ; ROM 198F8
    db $F7,$00,$2E,$05,$99,$F8,$66,$99,$F8,$79,$99,$F8,$8B,$99,$F7,$00 ; ROM 19908
    db $12,$13,$99,$F8,$66,$99,$F8,$79,$99,$F8,$54,$99,$F7,$00,$07,$21 ; ROM 19918
    db $99,$F8,$79,$99,$F8,$54,$99,$F7,$00,$06,$2C,$99,$F8,$66,$99,$F8 ; ROM 19928
    db $79,$99,$F8,$54,$99,$F8,$66,$99,$F8,$54,$99,$F7,$00,$03,$40,$99 ; ROM 19938
    db $F8,$66,$99,$F8,$54,$99,$F8,$9D,$99,$F6,$05,$99,$84,$03,$81,$81 ; ROM 19948
    db $84,$88,$81,$81,$81,$84,$81,$81,$84,$88,$81,$84,$81,$F9,$84,$03 ; ROM 19958
    db $81,$81,$88,$84,$81,$81,$03,$88,$81,$81,$84,$81,$88,$88,$81,$81 ; ROM 19968
    db $F9,$84,$03,$81,$81,$88,$84,$81,$81,$81,$81,$81,$84,$84,$84,$84 ; ROM 19978
    db $81,$81,$F9,$84,$03,$81,$84,$81,$84,$80,$84,$80,$84,$80,$84,$80 ; ROM 19988
    db $09,$84,$03,$80,$F9,$84,$03,$81,$81,$88,$84,$81,$81,$81,$81,$81 ; ROM 19998
    db $84,$84,$80,$88,$88,$88,$F9,$04,$80,$80,$01,$D4,$99,$EA,$00,$08 ; ROM 199A8
    db $03,$80,$A0,$01,$DF,$99,$EA,$00,$08,$04,$80,$C0,$01,$EB,$99,$EA ; ROM 199B8
    db $00,$08,$04,$80,$E0,$01,$F6,$99,$00,$00,$00,$0F,$B6,$0C,$06,$06 ; ROM 199C8
    db $0C,$B5,$B3,$B5,$B6,$24,$F2,$AE,$0C,$06,$06,$AE,$0C,$AC,$AA,$AC ; ROM 199D8
    db $AE,$24,$F2,$B1,$0C,$06,$06,$0C,$B1,$AF,$B1,$B1,$24,$F2,$F2,$04 ; ROM 199E8
    db $80,$80,$02,$1C,$9A,$E6,$00,$08,$02,$80,$A0,$02,$30,$9A,$E6,$00 ; ROM 199F8
    db $08,$04,$80,$C0,$02,$38,$9A,$E6,$00,$08,$04,$80,$E0,$02,$40,$9A ; ROM 19A08
    db $00,$00,$00,$0F,$80,$06,$AE,$B1,$B6,$B8,$B0,$B3,$B8,$BA,$B1,$B6 ; ROM 19A18
    db $BA,$BC,$B3,$B8,$BC,$BD,$30,$F2,$AA,$18,$AC,$AE,$B0,$B1,$30,$F2 ; ROM 19A28
    db $A5,$18,$A7,$A9,$AA,$AC,$30,$F2,$F2,$01,$88,$E0,$02,$4B,$9A,$00 ; ROM 19A38
    db $00,$02,$01,$F3,$E7,$F0,$01,$02,$44,$02,$00,$03,$02,$F2,$01,$88 ; ROM 19A48
    db $C0,$01,$60,$9A,$00,$05,$03,$02,$01,$07,$02,$01,$C2,$03,$F2,$02 ; ROM 19A58
    db $88,$A0,$01,$7A,$9A,$00,$00,$00,$04,$88,$E0,$01,$83,$9A,$D9,$00 ; ROM 19A68
    db $00,$02,$F0,$01,$01,$03,$01,$00,$0A,$09,$F2,$F3,$E7,$F0,$02,$01 ; ROM 19A78
    db $14,$05,$00,$4D,$09,$F2,$02,$80,$A0,$01,$A1,$9A,$00,$00,$00,$02 ; ROM 19A88
    db $88,$E0,$01,$B0,$9A,$00,$00,$00,$02,$F0,$01,$01,$18,$02,$FD,$01 ; ROM 19A98
    db $03,$DF,$08,$FD,$00,$80,$07,$F2,$F3,$E7,$F0,$02,$02,$40,$04,$00 ; ROM 19AA8
    db $5F,$0F,$F2,$01,$88,$E0,$02,$C5,$9A,$03,$00,$00,$01,$F3,$E7,$F0 ; ROM 19AB8
    db $01,$02,$FB,$90,$00,$83,$50,$F2,$01,$88,$C0,$02,$DA,$9A,$00,$00 ; ROM 19AC8
    db $02,$01,$00,$40,$02,$F2,$01,$80,$C0,$01,$E8,$9A,$E2,$04,$02,$01 ; ROM 19AD8
    db $BF,$03,$C1,$03,$C6,$03,$C8,$03,$C3,$03,$C1,$03,$F2,$01,$80,$C0 ; ROM 19AE8
    db $01,$FF,$9A,$00,$00,$05,$01,$9D,$04,$99,$FB,$02,$F7,$00,$02,$FF ; ROM 19AF8
    db $9A,$F2,$02,$88,$A0,$02,$1D,$9B,$00,$00,$02,$01,$88,$C0,$02,$1D ; ROM 19B08
    db $9B,$F8,$00,$02,$01,$00,$30,$05,$F2,$01,$88,$E0,$01,$2B,$9B,$00 ; ROM 19B18
    db $00,$0A,$00,$F3,$E7,$00,$50,$04,$00,$2B,$02,$F2,$01,$88,$E0,$02 ; ROM 19B28
    db $3E,$9B,$F6,$00,$05,$00,$F3,$E6,$00,$10,$05,$F3,$E7,$F0,$01,$02 ; ROM 19B38
    db $28,$05,$00,$0A,$10,$F2,$01,$88,$E0,$01,$58,$9B,$01,$00,$03,$01 ; ROM 19B48
    db $F3,$E7,$F0,$02,$02,$72,$08,$00,$20,$08,$F2,$01,$88,$E0,$01,$6D ; ROM 19B58
    db $9B,$00,$00,$00,$00,$F3,$E7,$F0,$01,$02,$7F,$01,$00,$23,$0F,$F2 ; ROM 19B68
    db $01,$80,$C0,$01,$82,$9B,$00,$00,$00,$02,$F0,$01,$01,$06,$02,$B5 ; ROM 19B78
    db $03,$BA,$02,$F2,$02,$80,$A0,$02,$9F,$9B,$00,$00,$00,$02,$88,$E0 ; ROM 19B88
    db $01,$B6,$9B,$08,$00,$00,$00,$FD,$01,$03,$60,$07,$03,$F0,$02,$03 ; ROM 19B98
    db $B0,$02,$E6,$01,$F7,$00,$07,$A4,$9B,$FD,$00,$80,$08,$F2,$F3,$E7 ; ROM 19BA8
    db $F0,$01,$02,$50,$01,$00,$04,$08,$00,$03,$05,$00,$05,$05,$F0,$01 ; ROM 19BB8
    db $01,$30,$06,$00,$10,$03,$00,$0C,$03,$E6,$01,$F7,$00,$0B,$CB,$9B ; ROM 19BC8
    db $F2,$01,$88,$C0,$01,$E3,$9B,$00,$00,$02,$01,$F0,$01,$01,$18,$02 ; ROM 19BD8
    db $00,$80,$02,$F2,$01,$88,$E0,$01,$F6,$9B,$00,$00,$00,$01,$F3,$E7 ; ROM 19BE8
    db $F0,$01,$01,$50,$01,$00,$01,$07,$F0,$01,$01,$04,$01,$00,$0D,$06 ; ROM 19BF8
    db $F2,$01,$88,$E0,$01,$13,$9C,$E0,$00,$00,$00,$F3,$E2,$00,$30,$0C ; ROM 19C08
    db $F2,$01,$88,$C0,$01,$23,$9C,$00,$00,$02,$02,$F0,$01,$01,$48,$01 ; ROM 19C18
    db $00,$30,$01,$00,$20,$01,$00,$50,$02,$00,$40,$01,$F2,$01,$88,$C0 ; ROM 19C28
    db $01,$3F,$9C,$08,$00,$05,$01,$F0,$01,$03,$D0,$03,$00,$40,$03,$00 ; ROM 19C38
    db $20,$03,$F7,$00,$03,$44,$9C,$F2,$01,$80,$C0,$01,$5A,$9C,$20,$00 ; ROM 19C48
    db $02,$01,$F0,$01,$01,$0B,$02,$F8,$7A,$9C,$FB,$02,$80,$05,$F8,$7A ; ROM 19C58
    db $9C,$FB,$FC,$80,$05,$F8,$7A,$9C,$FB,$06,$80,$05,$F8,$7A,$9C,$80 ; ROM 19C68
    db $05,$F2,$FD,$01,$00,$08,$02,$00,$06,$02,$00,$07,$02,$00,$09,$03 ; ROM 19C78
    db $FD,$00,$F9,$01,$80,$E0,$01,$95,$9C,$E0,$00,$00,$01,$F3,$E7,$F0 ; ROM 19C88
    db $02,$02,$56,$02,$FD,$01,$00,$90,$02,$00,$30,$01,$FD,$00,$80,$03 ; ROM 19C98
    db $F7,$00,$02,$9C,$9C,$F2,$01,$80,$C0,$01,$B8,$9C,$FA,$00,$00,$00 ; ROM 19CA8
    db $F0,$01,$01,$38,$08,$A5,$05,$FB,$01,$F7,$00,$02,$B8,$9C,$E6,$01 ; ROM 19CB8
    db $F7,$01,$09,$B8,$9C,$F2,$01,$80,$C0,$01,$D8,$9C,$F6,$00,$05,$01 ; ROM 19CC8
    db $B7,$03,$B3,$03,$F7,$00,$02,$D8,$9C,$F2,$02,$80,$A0,$01,$F5,$9C ; ROM 19CD8
    db $EC,$00,$05,$01,$80,$C0,$01,$FB,$9C,$EC,$00,$05,$01,$AE,$05,$B0 ; ROM 19CE8
    db $B1,$B5,$F2,$A9,$0A,$AA,$05,$B1,$F2,$01,$88,$E0,$01,$0B,$9D,$00 ; ROM 19CF8
    db $00,$00,$00,$F3,$E7,$F0,$01,$01,$10,$08,$E0,$17,$10,$20,$08,$14 ; ROM 19D08
    db $00,$60,$20,$F2,$01,$88,$E0,$01,$26,$9D,$10,$00,$00,$02,$F3,$E7 ; ROM 19D18
    db $F0,$01,$01,$1D,$07,$00,$17,$08,$F2,$02,$80,$A0,$01,$46,$9D,$F2 ; ROM 19D28
    db $00,$07,$01,$80,$C0,$01,$44,$9D,$EF,$00,$07,$02,$80,$02,$AE,$03 ; ROM 19D38
    db $B3,$B8,$F2,$02,$88,$A0,$01,$60,$9D,$00,$00,$00,$02,$88,$C0,$01 ; ROM 19D48
    db $5E,$9D,$00,$00,$00,$02,$FB,$03,$E8,$03,$00,$70,$05,$01,$90,$05 ; ROM 19D58
    db $F7,$00,$02,$60,$9D,$E8,$00,$F2,$00,$07,$0B,$0F,$0E,$FF,$81,$FE ; ROM 19D68
    db $04,$FF,$81,$EF,$06,$FF,$99,$FE,$FD,$FA,$F4,$F5,$EB,$67,$4F,$9C ; ROM 19D78
    db $38,$70,$C0,$80,$01,$80,$01,$07,$0F,$1F,$7F,$FF,$FF,$FC,$FE,$FE ; ROM 19D88
    db $05,$FF,$04,$00,$02,$80,$82,$C0,$E0,$08,$00,$02,$FF,$02,$7F,$02 ; ROM 19D98
    db $3F,$02,$1F,$02,$FE,$06,$FF,$98,$CF,$4F,$47,$67,$27,$A3,$B3,$93 ; ROM 19DA8
    db $FF,$FF,$EF,$FD,$FF,$DF,$DF,$FD,$DF,$FD,$FD,$DF,$D7,$87,$93,$03 ; ROM 19DB8
    db $05,$FF,$02,$BF,$A8,$FB,$FF,$FF,$EF,$FF,$F8,$E0,$A1,$80,$FF,$FF ; ROM 19DC8
    db $FE,$79,$76,$D8,$3C,$7E,$FD,$9D,$5F,$BF,$3E,$3C,$19,$02,$D6,$AC ; ROM 19DD8
    db $58,$30,$60,$C1,$01,$01,$07,$0F,$1F,$7F,$FF,$DF,$DF,$05,$FF,$89 ; ROM 19DE8
    db $F7,$FF,$DF,$DE,$FC,$F0,$E9,$D1,$D1,$03,$A3,$06,$FF,$02,$EF,$02 ; ROM 19DF8
    db $FF,$96,$CF,$C7,$E3,$EB,$E9,$E9,$F0,$F0,$F8,$FC,$BC,$FE,$FF,$FF ; ROM 19E08
    db $0F,$0F,$07,$07,$03,$03,$01,$01,$08,$FF,$88,$D1,$D9,$C9,$E8,$EC ; ROM 19E18
    db $E4,$F4,$F6,$06,$FF,$02,$7F,$95,$BF,$FB,$F3,$F7,$BF,$DF,$4F,$07 ; ROM 19E28
    db $FF,$F4,$F0,$70,$F0,$B2,$A0,$A0,$01,$00,$00,$08,$08,$03,$00,$8C ; ROM 19E38
    db $FF,$EE,$EC,$48,$00,$08,$02,$02,$00,$00,$10,$10,$04,$00,$81,$21 ; ROM 19E48
    db $07,$00,$81,$04,$07,$00,$81,$11,$03,$00,$94,$10,$70,$60,$00,$BF ; ROM 19E58
    db $FB,$9B,$2F,$27,$07,$05,$05,$FF,$FF,$FE,$FE,$FF,$FF,$78,$70,$03 ; ROM 19E68
    db $FF,$91,$C7,$0F,$2F,$BF,$1F,$41,$41,$40,$40,$A0,$A0,$D0,$D8,$EC ; ROM 19E78
    db $E3,$1F,$18,$04,$00,$84,$3F,$1F,$0F,$03,$04,$00,$8B,$E9,$D0,$D0 ; ROM 19E88
    db $A0,$60,$C1,$81,$03,$FF,$FF,$FB,$03,$FF,$02,$FD,$81,$BF,$03,$FF ; ROM 19E98
    db $8C,$DF,$FF,$7F,$FF,$80,$C0,$C0,$E0,$F0,$F8,$F8,$FC,$03,$FF,$8E ; ROM 19EA8
    db $7F,$3F,$3F,$1F,$0F,$F2,$FA,$FB,$F9,$FD,$FD,$FC,$FE,$7F,$03,$3F ; ROM 19EB8
    db $84,$1F,$9F,$9F,$8F,$03,$FF,$81,$FD,$03,$FF,$85,$FD,$87,$05,$11 ; ROM 19EC8
    db $10,$06,$00,$81,$20,$11,$00,$89,$08,$00,$10,$18,$00,$08,$00,$00 ; ROM 19ED8
    db $40,$1B,$00,$8D,$01,$20,$00,$03,$00,$08,$08,$00,$E8,$E0,$C0,$80 ; ROM 19EE8
    db $20,$03,$00,$8A,$1F,$0F,$0B,$03,$10,$00,$02,$00,$C0,$F0,$03,$60 ; ROM 19EF8
    db $03,$00,$9A,$03,$07,$0D,$1F,$06,$02,$00,$08,$FF,$FF,$F6,$FB,$F2 ; ROM 19F08
    db $E0,$00,$00,$EF,$7F,$3F,$5F,$4D,$0D,$07,$17,$FE,$FE,$03,$FF,$83 ; ROM 19F18
    db $EF,$FF,$FD,$03,$00,$03,$80,$86,$A0,$F0,$0F,$0F,$07,$07,$03,$03 ; ROM 19F28
    db $91,$01,$CF,$47,$63,$23,$A3,$B3,$91,$D1,$FF,$DA,$FE,$FD,$D4,$F4 ; ROM 19F38
    db $68,$60,$03,$00,$85,$10,$18,$00,$02,$06,$03,$00,$9D,$04,$86,$C8 ; ROM 19F48
    db $0B,$2F,$18,$02,$23,$6B,$3F,$9B,$73,$EF,$00,$80,$C0,$C0,$50,$1B ; ROM 19F58
    db $BB,$FF,$10,$90,$30,$A0,$26,$C0,$E9,$E8,$07,$00,$02,$80,$81,$01 ; ROM 19F68
    db $0A,$00,$81,$03,$03,$00,$81,$08,$03,$00,$82,$80,$0E,$05,$00,$81 ; ROM 19F78
    db $40,$14,$00,$81,$04,$07,$00,$85,$13,$03,$03,$44,$04,$03,$00,$8D ; ROM 19F88
    db $FF,$BD,$F5,$DF,$16,$48,$44,$0C,$F0,$60,$00,$08,$40,$0B,$00,$81 ; ROM 19F98
    db $01,$07,$00,$03,$FF,$02,$7F,$02,$3F,$AD,$1F,$D8,$C8,$E8,$EC,$E4 ; ROM 19FA8
    db $F4,$F6,$F2,$20,$88,$00,$20,$20,$00,$08,$0C,$16,$1B,$2B,$2F,$3F ; ROM 19FB8
    db $7F,$9F,$BF,$82,$C2,$D0,$40,$08,$99,$51,$50,$2F,$3E,$36,$37,$73 ; ROM 19FC8
    db $7B,$3F,$EF,$EF,$FF,$FF,$DF,$04,$FF,$02,$7F,$02,$FF,$81,$FB,$03 ; ROM 19FD8
    db $FF,$90,$78,$3A,$BF,$FF,$FB,$FB,$FF,$FF,$00,$60,$20,$E8,$DC,$FD ; ROM 19FE8
    db $FF,$DD,$04,$00,$84,$80,$A0,$FC,$FF,$08,$00,$81,$20,$08,$00,$81 ; ROM 19FF8
    db $08,$04,$00,$95,$04,$00,$00,$08,$00,$00,$C4,$82,$06,$27,$08,$20 ; ROM 1A008
    db $00,$17,$7E,$FC,$FC,$FE,$00,$00,$40,$04,$00,$81,$40,$08,$00,$B0 ; ROM 1A018
    db $1F,$0F,$0F,$07,$07,$03,$01,$01,$FA,$FB,$F9,$FD,$FD,$FC,$FE,$FE ; ROM 1A028
    db $24,$20,$00,$02,$80,$88,$80,$80,$FE,$FE,$7E,$7D,$ED,$E5,$F3,$FA ; ROM 1A038
    db $DB,$9A,$96,$9F,$0E,$1A,$3B,$7F,$EF,$FF,$DF,$CB,$EF,$FF,$FB,$FB ; ROM 1A048
    db $05,$FF,$83,$F8,$E7,$DC,$03,$FF,$85,$BF,$FF,$FF,$3F,$3F,$03,$FF ; ROM 1A058
    db $81,$EF,$04,$FF,$88,$DF,$FF,$7B,$FB,$FF,$FC,$BC,$CC,$03,$FF,$89 ; ROM 1A068
    db $DF,$FF,$3F,$7F,$FF,$C0,$F0,$FC,$FE,$04,$FF,$06,$00,$87,$80,$C0 ; ROM 1A078
    db $00,$00,$03,$03,$01,$03,$00,$82,$5F,$7F,$04,$FF,$9A,$7F,$3F,$FE ; ROM 1A088
    db $FF,$FD,$FC,$FF,$F9,$FA,$F9,$40,$80,$C0,$D0,$D1,$F3,$7D,$3D,$40 ; ROM 1A098
    db $04,$10,$F0,$E2,$EB,$FB,$FE,$03,$00,$89,$80,$C0,$E0,$E0,$F0,$FE ; ROM 1A0A8
    db $FC,$F0,$60,$0C,$00,$02,$FA,$97,$F6,$F4,$F4,$F5,$ED,$E9,$77,$77 ; ROM 1A0B8
    db $FF,$FE,$FF,$FF,$EF,$EF,$FF,$FF,$FE,$FE,$FD,$FD,$FC,$F8,$80,$07 ; ROM 1A0C8
    db $00,$81,$3F,$06,$1F,$89,$3F,$FF,$F8,$BB,$F8,$FC,$FE,$FC,$FC,$04 ; ROM 1A0D8
    db $00,$8F,$04,$0C,$1F,$1F,$00,$FF,$00,$FF,$FF,$7F,$FF,$FF,$00,$FF ; ROM 1A0E8
    db $00,$03,$FF,$86,$E3,$81,$00,$E0,$00,$F8,$03,$FC,$86,$FE,$3F,$1F ; ROM 1A0F8
    db $0F,$0F,$03,$03,$01,$81,$F9,$04,$F8,$03,$FC,$95,$57,$A7,$19,$46 ; ROM 1A108
    db $69,$76,$39,$3E,$FE,$7F,$FF,$FF,$2F,$C6,$38,$C0,$F0,$F8,$F8,$F0 ; ROM 1A118
    db $80,$03,$00,$8B,$EB,$E3,$E3,$E7,$C7,$C7,$CF,$CF,$FF,$FF,$FE,$05 ; ROM 1A128
    db $FF,$02,$FA,$90,$F8,$D8,$D0,$80,$80,$00,$7F,$FF,$7F,$7F,$0F,$03 ; ROM 1A138
    db $01,$00,$F8,$F8,$03,$F0,$03,$E0,$05,$1F,$87,$03,$00,$00,$FE,$FC ; ROM 1A148
    db $FC,$F8,$03,$F0,$81,$20,$08,$00,$02,$FF,$04,$7F,$02,$FF,$88,$00 ; ROM 1A158
    db $80,$80,$C0,$C0,$E0,$F0,$F0,$07,$00,$89,$01,$FC,$FC,$7C,$3E,$3E ; ROM 1A168
    db $1E,$1E,$0E,$03,$1F,$82,$0E,$0C,$03,$00,$82,$20,$C0,$06,$00,$98 ; ROM 1A178
    db $8F,$9F,$9B,$1B,$03,$03,$1F,$00,$FF,$FE,$FC,$F8,$F8,$F0,$F0,$00 ; ROM 1A188
    db $F0,$78,$7C,$3E,$1F,$1F,$0F,$0F,$05,$00,$84,$C0,$E0,$C0,$01,$03 ; ROM 1A198
    db $03,$04,$00,$04,$FF,$84,$7F,$3F,$0F,$07,$03,$F8,$03,$FC,$02,$FE ; ROM 1A1A8
    db $02,$01,$05,$03,$91,$07,$C0,$F8,$FF,$FF,$F8,$E0,$C0,$00,$06,$06 ; ROM 1A1B8
    db $07,$07,$03,$90,$96,$07,$06,$00,$8C,$01,$27,$00,$00,$03,$0F,$3F ; ROM 1A1C8
    db $7F,$FF,$FF,$00,$80,$0A,$00,$84,$F8,$FF,$F1,$E1,$05,$00,$93,$80 ; ROM 1A1D8
    db $E1,$FF,$00,$00,$10,$30,$78,$F0,$E4,$CC,$07,$07,$0F,$0F,$1F,$3F ; ROM 1A1E8
    db $7F,$7F,$03,$C0,$05,$80,$06,$00,$84,$03,$07,$03,$01,$04,$00,$84 ; ROM 1A1F8
    db $80,$F0,$FF,$C3,$06,$00,$82,$06,$04,$06,$00,$93,$1F,$0F,$07,$0B ; ROM 1A208
    db $09,$09,$02,$02,$00,$00,$80,$F0,$FC,$FE,$FE,$FF,$E1,$E0,$E0,$03 ; ROM 1A218
    db $C0,$02,$80,$85,$FF,$7C,$00,$01,$07,$03,$3F,$02,$1E,$81,$7F,$05 ; ROM 1A228
    db $FF,$03,$00,$03,$80,$03,$00,$02,$01,$05,$00,$05,$FF,$83,$7F,$3F ; ROM 1A238
    db $3F,$05,$C0,$03,$00,$81,$1F,$03,$3F,$03,$7F,$82,$FF,$F0,$04,$E0 ; ROM 1A248
    db $02,$C0,$83,$E0,$03,$03,$03,$01,$03,$00,$02,$7F,$03,$BF,$03,$DF ; ROM 1A258
    db $88,$00,$80,$E0,$FC,$FE,$FE,$FF,$FF,$00,$1A,$FF,$99,$FE,$FD,$FB ; ROM 1A268
    db $F7,$F6,$EC,$78,$70,$E0,$C0,$80,$00,$00,$01,$00,$01,$07,$0F,$1F ; ROM 1A278
    db $7F,$FF,$FF,$FC,$FE,$FE,$05,$FF,$04,$00,$02,$80,$82,$C0,$E0,$10 ; ROM 1A288
    db $00,$02,$01,$06,$00,$02,$EF,$03,$F7,$03,$7B,$22,$FF,$9A,$FE,$F8 ; ROM 1A298
    db $F0,$F8,$FC,$FE,$FF,$9F,$1F,$3F,$3E,$3D,$1A,$04,$D8,$B0,$60,$40 ; ROM 1A2A8
    db $80,$01,$07,$0F,$07,$0F,$1F,$7F,$0C,$FF,$85,$FC,$F2,$E5,$C9,$C1 ; ROM 1A2B8
    db $03,$93,$0A,$FF,$8E,$CF,$C7,$E3,$E3,$E5,$E5,$F0,$F0,$F8,$FC,$FC ; ROM 1A2C8
    db $FE,$FF,$FF,$10,$00,$03,$3D,$03,$1E,$02,$0F,$06,$FF,$02,$7F,$22 ; ROM 1A2D8
    db $FF,$02,$FE,$86,$FC,$F8,$F0,$F0,$E1,$80,$0C,$00,$8A,$1C,$3E,$1F ; ROM 1A2E8
    db $7F,$FF,$E3,$07,$07,$0F,$0F,$18,$FF,$02,$21,$02,$20,$02,$90,$85 ; ROM 1A2F8
    db $C8,$C0,$FC,$E0,$80,$05,$00,$84,$3F,$1F,$0F,$03,$04,$00,$88,$E5 ; ROM 1A308
    db $C8,$C8,$98,$10,$21,$41,$03,$10,$FF,$88,$80,$C0,$C0,$E0,$F0,$F8 ; ROM 1A318
    db $F8,$FC,$08,$00,$81,$0F,$03,$07,$03,$03,$82,$01,$7F,$03,$BF,$03 ; ROM 1A328
    db $DF,$81,$EF,$24,$FF,$8B,$F7,$FF,$EF,$E7,$F0,$F0,$F8,$F0,$F0,$E0 ; ROM 1A338
    db $C0,$08,$00,$85,$78,$3F,$1F,$0F,$03,$04,$00,$82,$1F,$BF,$03,$FF ; ROM 1A348
    db $83,$3F,$07,$01,$18,$FF,$82,$E0,$F0,$03,$E0,$02,$C0,$86,$80,$03 ; ROM 1A358
    db $07,$0F,$1F,$3F,$03,$7F,$10,$FF,$02,$FE,$06,$FF,$03,$00,$02,$80 ; ROM 1A368
    db $83,$C0,$E0,$F0,$08,$00,$81,$EF,$03,$F7,$03,$7B,$81,$3D,$0B,$FF ; ROM 1A378
    db $85,$EF,$E7,$FF,$FD,$F9,$03,$FF,$9D,$FB,$79,$37,$F4,$D0,$E7,$FD ; ROM 1A388
    db $DC,$94,$C0,$64,$8C,$10,$00,$01,$03,$23,$A3,$E4,$44,$00,$EC,$6E ; ROM 1A398
    db $CF,$5F,$D9,$3F,$16,$17,$03,$00,$88,$80,$C0,$C0,$E0,$70,$7F,$7F ; ROM 1A3A8
    db $1F,$05,$00,$03,$FF,$82,$7C,$03,$03,$00,$03,$FF,$82,$07,$F0,$03 ; ROM 1A3B8
    db $00,$03,$80,$02,$C0,$08,$00,$03,$01,$81,$7F,$12,$FF,$81,$BF,$0A ; ROM 1A3C8
    db $FF,$87,$FB,$F3,$F0,$F8,$FC,$FC,$BE,$03,$FF,$07,$00,$81,$80,$10 ; ROM 1A3D8
    db $00,$02,$3D,$03,$1E,$03,$0F,$05,$FF,$9F,$7F,$77,$73,$E9,$E4,$D4 ; ROM 1A3E8
    db $D0,$C0,$80,$60,$40,$7D,$3D,$2F,$9F,$97,$06,$4E,$4F,$D0,$C1,$C9 ; ROM 1A3F8
    db $C8,$8C,$84,$C0,$10,$10,$00,$00,$20,$04,$00,$02,$80,$02,$00,$81 ; ROM 1A408
    db $04,$03,$00,$90,$87,$C5,$40,$00,$04,$04,$00,$00,$F8,$9C,$DE,$17 ; ROM 1A418
    db $23,$02,$00,$22,$05,$00,$84,$40,$00,$00,$01,$07,$00,$02,$FF,$82 ; ROM 1A428
    db $3F,$03,$04,$00,$82,$FF,$F7,$03,$FF,$96,$7F,$1B,$0F,$FF,$F7,$FF ; ROM 1A438
    db $FF,$3B,$7D,$F9,$D8,$F7,$FF,$FF,$E8,$81,$03,$03,$01,$FF,$FF,$BF ; ROM 1A448
    db $04,$FF,$89,$BF,$C0,$C0,$E0,$F0,$F8,$F8,$FC,$FE,$08,$00,$03,$07 ; ROM 1A458
    db $03,$03,$02,$01,$A0,$9B,$9F,$BF,$DD,$DF,$D0,$C7,$9F,$00,$00,$80 ; ROM 1A468
    db $81,$11,$19,$0B,$02,$C4,$85,$89,$80,$31,$25,$04,$00,$10,$00,$20 ; ROM 1A478
    db $34,$10,$00,$04,$04,$06,$00,$82,$07,$1C,$03,$00,$81,$40,$07,$00 ; ROM 1A488
    db $81,$10,$04,$00,$87,$20,$00,$84,$04,$00,$00,$40,$04,$00,$81,$20 ; ROM 1A498
    db $14,$00,$02,$07,$81,$04,$05,$00,$82,$A0,$80,$06,$00,$9B,$01,$00 ; ROM 1A4A8
    db $02,$03,$00,$00,$02,$01,$BF,$7F,$3F,$2F,$2E,$0C,$82,$02,$BE,$FB ; ROM 1A4B8
    db $EF,$0F,$1D,$14,$04,$01,$00,$00,$80,$07,$00,$83,$03,$0C,$10,$03 ; ROM 1A4C8
    db $00,$82,$78,$C0,$06,$00,$02,$02,$81,$06,$03,$04,$81,$0C,$03,$08 ; ROM 1A4D8
    db $86,$00,$01,$00,$00,$10,$10,$04,$00,$02,$01,$14,$00,$83,$43,$00 ; ROM 1A4E8
    db $02,$0C,$00,$81,$FF,$07,$00,$81,$FF,$05,$00,$83,$18,$00,$E0,$0E ; ROM 1A4F8
    db $00,$81,$01,$07,$00,$90,$C8,$E0,$78,$7E,$77,$79,$3E,$3F,$01,$80 ; ROM 1A508
    db $00,$00,$10,$C0,$F8,$38,$08,$00,$81,$08,$09,$00,$81,$01,$05,$00 ; ROM 1A518
    db $02,$02,$83,$00,$20,$20,$1C,$00,$02,$01,$81,$03,$03,$06,$84,$00 ; ROM 1A528
    db $60,$C0,$80,$25,$00,$03,$1F,$82,$0E,$0C,$03,$00,$02,$C0,$7F,$00 ; ROM 1A538
    db $37,$00,$88,$C0,$E0,$70,$18,$1C,$0C,$06,$06,$50,$00,$02,$03,$03 ; ROM 1A548
    db $01,$05,$00,$03,$80,$03,$C0,$08,$00,$00,$7F,$00,$7F,$00,$7F,$00 ; ROM 1A558
    db $7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00 ; ROM 1A568
    db $7F,$00,$14,$00,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F ; ROM 1A578
    db $00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$14,$00,$00 ; ROM 1A588
    db $81,$83,$03,$00,$83,$04,$00,$83,$03,$03,$83,$05,$00,$87,$03,$06 ; ROM 1A598
    db $04,$08,$83,$03,$00,$E7,$08,$0C,$81,$00,$03,$14,$86,$00,$17,$00 ; ROM 1A5A8
    db $18,$08,$08,$04,$19,$81,$00,$12,$1D,$82,$08,$08,$10,$2F,$82,$08 ; ROM 1A5B8
    db $08,$05,$3F,$83,$08,$44,$0A,$03,$45,$81,$35,$05,$48,$81,$08,$04 ; ROM 1A5C8
    db $4D,$81,$08,$13,$51,$83,$05,$08,$95,$07,$64,$81,$08,$0D,$6B,$83 ; ROM 1A5D8
    db $05,$08,$93,$06,$78,$81,$08,$0C,$7E,$83,$06,$08,$85,$05,$8A,$83 ; ROM 1A5E8
    db $03,$08,$8B,$03,$8F,$81,$08,$07,$92,$86,$03,$08,$86,$99,$08,$08 ; ROM 1A5F8
    db $03,$9A,$8B,$04,$08,$82,$9D,$9E,$03,$08,$86,$9F,$A0,$08,$03,$A1 ; ROM 1A608
    db $86,$03,$08,$87,$A4,$A5,$08,$04,$A6,$83,$03,$08,$8B,$03,$AA,$85 ; ROM 1A618
    db $08,$08,$AD,$AE,$08,$03,$AF,$8D,$03,$08,$87,$B2,$08,$08,$58,$B3 ; ROM 1A628
    db $1A,$B4,$03,$08,$8A,$07,$B5,$94,$08,$BC,$BD,$08,$08,$86,$BE,$BF ; ROM 1A638
    db $1A,$C0,$08,$08,$00,$7F,$00,$7F,$00,$22,$00,$00,$00,$00,$2F,$1A ; ROM 1A648
    db $05,$0A,$00,$86,$01,$03,$0B,$09,$0C,$07,$03,$00,$97,$80,$A0,$20 ; ROM 1A658
    db $60,$C0,$00,$00,$20,$70,$20,$08,$00,$08,$01,$03,$01,$00,$01,$00 ; ROM 1A668
    db $02,$02,$00,$80,$05,$00,$89,$80,$00,$00,$10,$38,$10,$20,$40,$A0 ; ROM 1A678
    db $06,$00,$8E,$04,$0C,$00,$00,$10,$38,$BA,$92,$C6,$7C,$07,$00,$02 ; ROM 1A688
    db $02,$04,$00,$85,$1C,$30,$E0,$E0,$C0,$03,$80,$A6,$0C,$05,$06,$07 ; ROM 1A698
    db $03,$02,$01,$01,$02,$06,$86,$42,$3D,$D2,$32,$3F,$80,$81,$43,$4E ; ROM 1A6A8
    db $0C,$E4,$97,$D8,$A0,$40,$40,$C0,$C1,$66,$01,$B2,$0A,$08,$50,$A0 ; ROM 1A6B8
    db $40,$80,$05,$00,$8A,$80,$A0,$20,$60,$C0,$73,$05,$2A,$2A,$0C,$03 ; ROM 1A6C8
    db $10,$94,$C0,$00,$01,$03,$0B,$09,$0C,$07,$80,$80,$00,$80,$A0,$20 ; ROM 1A6D8
    db $60,$C0,$73,$05,$2A,$2A,$04,$2C,$AC,$C0,$00,$01,$03,$0B,$09,$0C ; ROM 1A6E8
    db $07,$01,$01,$00,$01,$01,$03,$02,$00,$C3,$3C,$D8,$E7,$FF,$FF,$00 ; ROM 1A6F8
    db $74,$FA,$39,$46,$9F,$C4,$C4,$CD,$8F,$8A,$34,$0C,$78,$B8,$D8,$5C ; ROM 1A708
    db $04,$07,$00,$02,$02,$04,$00,$88,$1C,$30,$60,$60,$C0,$FF,$00,$7F ; ROM 1A718
    db $04,$10,$86,$34,$FF,$00,$FF,$07,$00,$03,$02,$8B,$FF,$00,$FF,$1C ; ROM 1A728
    db $30,$60,$60,$C0,$FF,$00,$FF,$05,$2C,$83,$EF,$2C,$EF,$04,$10,$95 ; ROM 1A738
    db $30,$FF,$00,$FF,$07,$00,$02,$02,$01,$F9,$03,$FE,$3C,$50,$A0,$A0 ; ROM 1A748
    db $40,$40,$80,$00,$00,$03,$03,$9C,$02,$01,$07,$07,$60,$A0,$47,$27 ; ROM 1A758
    db $B7,$93,$B8,$3E,$CE,$06,$06,$EC,$EC,$CD,$DD,$3C,$AE,$82,$2C,$26 ; ROM 1A768
    db $56,$62,$91,$35,$04,$00,$8C,$03,$01,$00,$02,$04,$F6,$F9,$78,$9C ; ROM 1A778
    db $F1,$F1,$C6,$03,$00,$AD,$C0,$80,$40,$00,$20,$0E,$08,$09,$04,$0C ; ROM 1A788
    db $0F,$1F,$13,$FF,$03,$D0,$BE,$3F,$EF,$FF,$7C,$3E,$BE,$DA,$1C,$65 ; ROM 1A798
    db $F6,$F8,$D9,$29,$48,$43,$15,$55,$C6,$EA,$A5,$00,$80,$00,$00,$C0 ; ROM 1A7A8
    db $C0,$20,$B0,$07,$00,$81,$03,$03,$00,$87,$07,$1F,$7F,$FF,$FF,$00 ; ROM 1A7B8
    db $0F,$06,$FF,$82,$0F,$F0,$08,$FF,$89,$1F,$E7,$F9,$FE,$FF,$FF,$00 ; ROM 1A7C8
    db $F0,$FE,$03,$FF,$82,$3F,$DF,$03,$00,$96,$80,$E0,$F0,$FC,$FE,$01 ; ROM 1A7D8
    db $01,$02,$02,$00,$01,$00,$00,$F2,$F3,$F1,$E3,$0F,$0F,$2B,$2B,$60 ; ROM 1A7E8
    db $03,$C0,$04,$80,$BC,$00,$01,$07,$08,$16,$14,$14,$20,$00,$80,$C0 ; ROM 1A7F8
    db $DC,$DF,$1F,$5F,$47,$17,$37,$26,$02,$D1,$E4,$F6,$F2,$7E,$6F,$55 ; ROM 1A808
    db $D4,$90,$84,$64,$20,$CD,$29,$23,$63,$0B,$1F,$7F,$7F,$75,$33,$19 ; ROM 1A818
    db $1F,$03,$80,$80,$CF,$9F,$D8,$DF,$B7,$B3,$4B,$6F,$B7,$07,$0F,$1F ; ROM 1A828
    db $7F,$0C,$FF,$84,$EF,$F7,$F9,$FE,$08,$FF,$91,$7F,$BF,$DF,$EF,$00 ; ROM 1A838
    db $80,$E0,$F0,$F8,$FC,$FE,$FF,$2B,$2B,$28,$29,$29,$03,$2B,$88,$80 ; ROM 1A848
    db $00,$40,$E0,$E0,$E8,$DC,$DE,$04,$00,$9F,$01,$03,$07,$0C,$20,$26 ; ROM 1A858
    db $30,$CF,$E3,$F8,$FC,$1E,$43,$4C,$C6,$83,$F1,$F2,$39,$0D,$FC,$FF ; ROM 1A868
    db $3F,$03,$83,$40,$30,$98,$33,$03,$87,$03,$FF,$87,$3F,$01,$FE,$80 ; ROM 1A878
    db $FF,$FF,$F8,$03,$FF,$90,$3F,$FC,$F0,$83,$3F,$F8,$C0,$FF,$0F,$03 ; ROM 1A888
    db $78,$C0,$00,$00,$60,$03,$03,$FF,$89,$3F,$07,$01,$01,$86,$EF,$F7 ; ROM 1A898
    db $F9,$FE,$03,$FF,$86,$7F,$F7,$F7,$FB,$FD,$FE,$08,$FF,$02,$7F,$8D ; ROM 1A8A8
    db $BF,$80,$80,$C0,$E0,$F0,$F8,$F8,$FC,$69,$69,$F4,$01,$04,$00,$81 ; ROM 1A8B8
    db $BF,$05,$FF,$02,$7F,$85,$80,$E0,$F8,$FC,$FE,$03,$FF,$D4,$3C,$70 ; ROM 1A8C8
    db $70,$39,$19,$1C,$1C,$BE,$C3,$60,$30,$18,$DC,$EE,$FF,$FF,$04,$84 ; ROM 1A8D8
    db $E2,$7A,$7F,$7F,$3E,$BF,$CC,$62,$61,$30,$18,$1C,$8E,$87,$80,$60 ; ROM 1A8E8
    db $98,$CF,$30,$18,$04,$01,$7F,$07,$00,$80,$F8,$1F,$03,$00,$F0,$FF ; ROM 1A8F8
    db $00,$00,$07,$F0,$FF,$00,$78,$00,$03,$1F,$00,$03,$F0,$01,$0F,$3F ; ROM 1A908
    db $E1,$07,$27,$9F,$38,$E1,$7F,$BF,$DF,$27,$F7,$FB,$FD,$FE,$DF,$DF ; ROM 1A918
    db $EF,$EF,$03,$F7,$83,$FB,$FE,$FE,$06,$FF,$04,$00,$03,$80,$89,$C0 ; ROM 1A928
    db $3F,$3F,$1F,$1F,$0F,$0F,$07,$03,$08,$FF,$83,$BE,$BF,$BF,$04,$FF ; ROM 1A938
    db $81,$F8,$08,$FF,$98,$47,$43,$A1,$A0,$A0,$90,$98,$CC,$80,$C0,$E0 ; ROM 1A948
    db $F0,$FC,$7F,$3F,$3F,$00,$E0,$3C,$1F,$01,$00,$C0,$78,$03,$00,$82 ; ROM 1A958
    db $FF,$FC,$03,$00,$A0,$07,$00,$1C,$F0,$07,$3E,$00,$00,$07,$0F,$3E ; ROM 1A968
    db $F8,$E1,$3E,$00,$F0,$E3,$8F,$3F,$78,$E3,$07,$1F,$F8,$7F,$BF,$DF ; ROM 1A978
    db $6F,$EF,$F3,$FB,$81,$03,$FB,$05,$FD,$03,$C0,$05,$E0,$83,$03,$00 ; ROM 1A988
    db $00,$05,$08,$02,$FF,$82,$7F,$1C,$04,$00,$82,$F0,$C0,$06,$00,$A4 ; ROM 1A998
    db $FF,$1F,$FF,$7F,$3F,$1F,$0F,$07,$C4,$C6,$E2,$F1,$F1,$FC,$FE,$FF ; ROM 1A9A8
    db $0F,$07,$03,$03,$80,$E0,$38,$08,$8F,$E0,$FE,$FF,$FF,$7F,$1F,$03 ; ROM 1A9B8
    db $C0,$7F,$00,$F8,$03,$FF,$99,$FC,$3F,$00,$00,$1F,$FF,$F8,$00,$00 ; ROM 1A9C8
    db $80,$00,$3E,$E0,$00,$01,$02,$08,$00,$00,$07,$1F,$6F,$9F,$3F,$7C ; ROM 1A9D8
    db $03,$00,$85,$80,$E0,$E0,$F0,$71,$03,$FD,$05,$FE,$03,$E0,$05,$F0 ; ROM 1A9E8
    db $88,$0C,$04,$04,$06,$02,$03,$01,$01,$07,$00,$81,$80,$08,$07,$88 ; ROM 1A9F8
    db $8C,$84,$C6,$E3,$E5,$F2,$F2,$F1,$05,$00,$84,$E0,$3F,$03,$1F,$04 ; ROM 1AA08
    db $00,$88,$07,$F8,$E0,$C0,$00,$03,$18,$E0,$04,$00,$8C,$41,$03,$07 ; ROM 1AA18
    db $0E,$38,$73,$CF,$FB,$E7,$C1,$80,$3F,$03,$FF,$03,$F1,$85,$73,$B3 ; ROM 1AA28
    db $D3,$F3,$F7,$08,$FE,$08,$F0,$88,$C0,$40,$40,$60,$20,$30,$10,$10 ; ROM 1AA38
    db $05,$07,$90,$0F,$0E,$0C,$EF,$EF,$CF,$8F,$07,$07,$03,$01,$F8,$F8 ; ROM 1AA48
    db $FC,$FC,$FE,$03,$FF,$88,$80,$40,$60,$30,$1C,$0F,$87,$E3,$06,$00 ; ROM 1AA58
    db $8A,$E0,$FC,$01,$02,$05,$0F,$1F,$37,$7F,$FF,$03,$F7,$05,$FF,$00 ; ROM 1AA68
    db $0A,$00,$99,$02,$04,$0C,$0E,$0F,$07,$00,$00,$80,$40,$60,$E0,$E0 ; ROM 1AA78
    db $C0,$00,$00,$10,$00,$50,$18,$08,$04,$00,$00,$02,$05,$01,$02,$00 ; ROM 1AA88
    db $81,$80,$04,$00,$81,$80,$04,$00,$84,$28,$30,$20,$60,$06,$00,$02 ; ROM 1AA98
    db $02,$02,$00,$8B,$28,$44,$C6,$EE,$FE,$7C,$38,$0F,$05,$05,$03,$03 ; ROM 1AAA8
    db $01,$85,$FC,$F0,$E0,$E0,$C0,$03,$80,$99,$02,$03,$01,$00,$00,$01 ; ROM 1AAB8
    db $02,$02,$01,$01,$81,$CD,$C2,$2D,$CD,$C0,$80,$80,$C0,$C1,$F3,$1B ; ROM 1AAC8
    db $68,$27,$60,$04,$C0,$98,$E1,$FF,$4E,$06,$18,$30,$60,$C0,$80,$00 ; ROM 1AAD8
    db $00,$03,$00,$80,$40,$60,$E0,$E0,$C0,$8F,$FD,$5A,$5A,$3C,$03,$08 ; ROM 1AAE8
    db $94,$C1,$01,$02,$04,$0C,$0E,$0F,$07,$83,$80,$80,$40,$60,$E0,$E0 ; ROM 1AAF8
    db $C0,$8F,$FD,$5A,$5A,$04,$1C,$9C,$C0,$00,$02,$04,$0C,$0E,$0F,$07 ; ROM 1AB08
    db $02,$02,$03,$02,$02,$00,$01,$02,$3C,$FF,$3F,$18,$00,$00,$FF,$4C ; ROM 1AB18
    db $07,$C6,$FF,$7F,$03,$3F,$99,$FF,$76,$FC,$FC,$F8,$78,$38,$BC,$FC ; ROM 1AB28
    db $38,$0F,$05,$05,$03,$03,$01,$00,$FC,$F0,$E0,$E0,$C0,$00,$FF,$7F ; ROM 1AB38
    db $04,$08,$94,$0C,$00,$FF,$FF,$38,$0F,$05,$05,$01,$00,$FF,$FF,$FC ; ROM 1AB48
    db $F0,$E0,$E0,$C0,$00,$FF,$FF,$06,$1C,$02,$DF,$04,$08,$95,$0C,$00 ; ROM 1AB58
    db $FF,$FF,$38,$0F,$05,$05,$03,$07,$FF,$FE,$FC,$D0,$A0,$A0,$40,$40 ; ROM 1AB68
    db $80,$00,$02,$03,$04,$8C,$05,$06,$00,$00,$5C,$5F,$B8,$F8,$F8,$FC ; ROM 1AB78
    db $47,$C1,$03,$FF,$02,$1F,$02,$3E,$8A,$FF,$7E,$7E,$DE,$DE,$FE,$FE ; ROM 1AB88
    db $7F,$FF,$00,$03,$01,$02,$02,$02,$03,$88,$FC,$0E,$07,$C7,$7F,$0F ; ROM 1AB98
    db $0F,$3F,$03,$00,$A6,$C0,$E0,$A0,$E0,$E0,$01,$07,$06,$03,$03,$10 ; ROM 1ABA8
    db $00,$2C,$E0,$FC,$3F,$79,$F0,$10,$00,$83,$FD,$79,$3D,$F3,$9A,$09 ; ROM 1ABB8
    db $07,$27,$F7,$B7,$BF,$FB,$FB,$F9,$FD,$FF,$00,$03,$80,$02,$C0,$82 ; ROM 1ABC8
    db $E0,$F0,$06,$00,$8C,$03,$04,$00,$00,$07,$18,$60,$80,$00,$00,$0F ; ROM 1ABD8
    db $F0,$06,$00,$82,$FF,$0F,$06,$00,$03,$FF,$83,$1F,$07,$01,$03,$00 ; ROM 1ABE8
    db $82,$F0,$FE,$04,$FF,$81,$3F,$03,$00,$8D,$80,$E0,$F0,$FC,$FE,$02 ; ROM 1ABF8
    db $02,$03,$03,$01,$01,$00,$00,$03,$0F,$86,$1F,$FF,$FF,$DB,$DB,$E0 ; ROM 1AC08
    db $03,$C0,$02,$80,$02,$C0,$03,$00,$A1,$07,$09,$0B,$0B,$1F,$00,$40 ; ROM 1AC18
    db $38,$3F,$3F,$EF,$A3,$B9,$28,$48,$59,$7D,$EE,$FB,$F9,$FD,$81,$90 ; ROM 1AC28
    db $AA,$2B,$6F,$7B,$9B,$DF,$33,$D7,$DF,$9F,$04,$FF,$87,$7F,$3F,$1F ; ROM 1AC38
    db $1F,$03,$80,$84,$03,$FF,$02,$FC,$88,$FE,$7E,$7E,$BE,$08,$10,$60 ; ROM 1AC48
    db $80,$0C,$00,$84,$1F,$0F,$07,$01,$04,$00,$05,$FF,$8D,$7F,$3F,$1F ; ROM 1AC58
    db $00,$80,$E0,$F0,$F8,$FC,$FE,$FF,$5B,$5B,$06,$1B,$88,$C0,$E0,$E0 ; ROM 1AC68
    db $F0,$F8,$FC,$FE,$FF,$07,$00,$9A,$03,$1F,$19,$0F,$30,$1F,$07,$03 ; ROM 1AC78
    db $E1,$BC,$B3,$39,$7C,$CE,$EF,$F7,$F3,$7F,$1F,$CF,$FF,$7C,$BF,$CF ; ROM 1AC88
    db $E7,$CF,$04,$FF,$83,$3F,$C7,$FE,$04,$FF,$81,$F8,$04,$FF,$8E,$FC ; ROM 1AC98
    db $F0,$83,$3F,$F8,$C0,$FF,$0C,$00,$78,$C0,$00,$00,$60,$07,$00,$86 ; ROM 1ACA8
    db $1E,$7F,$1F,$0F,$07,$01,$03,$00,$86,$80,$0F,$0F,$07,$03,$01,$03 ; ROM 1ACB8
    db $00,$07,$FF,$8D,$7F,$80,$80,$C0,$E0,$F0,$F8,$F8,$FC,$19,$19,$0C ; ROM 1ACC8
    db $01,$04,$00,$06,$FF,$02,$7F,$83,$C0,$F0,$F9,$05,$FF,$89,$03,$0F ; ROM 1ACD8
    db $CF,$E7,$F7,$F3,$F3,$F9,$FC,$07,$FF,$02,$FB,$02,$FD,$03,$FE,$84 ; ROM 1ACE8
    db $FF,$F3,$FD,$FE,$03,$FF,$03,$7F,$91,$9F,$67,$30,$CF,$E7,$FB,$FE ; ROM 1ACF8
    db $81,$F8,$FF,$7F,$07,$E0,$FC,$FF,$F0,$00,$03,$FF,$84,$0F,$00,$FF ; ROM 1AD08
    db $07,$04,$FF,$82,$FC,$0F,$05,$FF,$90,$DF,$7F,$FF,$FF,$80,$C0,$E0 ; ROM 1AD18
    db $F8,$F8,$FC,$FE,$FF,$3F,$3F,$1F,$1F,$03,$0F,$83,$07,$FE,$FE,$06 ; ROM 1AD28
    db $FF,$04,$00,$03,$80,$89,$C0,$3F,$3F,$1F,$1F,$0F,$0F,$1F,$1B,$08 ; ROM 1AD38
    db $FF,$84,$F9,$F8,$FC,$FC,$03,$FE,$85,$F8,$FF,$FF,$7F,$7F,$06,$3F ; ROM 1AD48
    db $03,$9F,$83,$8F,$87,$C3,$09,$FF,$84,$1F,$C3,$E0,$FE,$06,$FF,$82 ; ROM 1AD58
    db $00,$03,$05,$FF,$82,$E3,$0F,$0B,$FF,$81,$0F,$08,$FF,$88,$80,$C0 ; ROM 1AD68
    db $E0,$F0,$F0,$FC,$FC,$FE,$03,$07,$05,$03,$03,$C0,$05,$E0,$81,$1B ; ROM 1AD78
    db $07,$18,$02,$FF,$82,$7F,$1C,$04,$00,$82,$F0,$C0,$06,$00,$8F,$1F ; ROM 1AD88
    db $FF,$1F,$0F,$4F,$6F,$77,$3F,$C3,$C1,$E1,$F0,$F0,$FC,$FE,$05,$FF ; ROM 1AD98
    db $84,$7F,$1F,$07,$07,$10,$FF,$81,$C0,$07,$FF,$81,$7F,$04,$FF,$93 ; ROM 1ADA8
    db $FE,$FC,$F0,$FF,$FF,$F8,$E7,$8F,$1F,$3F,$7F,$C3,$01,$01,$80,$E0 ; ROM 1ADB8
    db $E0,$F0,$F0,$03,$03,$05,$01,$03,$E0,$05,$F0,$02,$1C,$86,$0C,$0E ; ROM 1ADC8
    db $06,$07,$03,$01,$07,$00,$81,$80,$08,$3F,$02,$83,$86,$C1,$E0,$E4 ; ROM 1ADD8
    db $F2,$F2,$F1,$05,$FF,$83,$1F,$00,$00,$05,$FF,$87,$F8,$00,$00,$FF ; ROM 1ADE8
    db $FF,$FC,$E0,$04,$00,$87,$E0,$81,$03,$07,$0F,$3F,$7F,$09,$FF,$08 ; ROM 1ADF8
    db $F0,$08,$01,$08,$F0,$03,$C0,$02,$60,$02,$30,$81,$10,$05,$3F,$90 ; ROM 1AE08
    db $7F,$7E,$7C,$EF,$EF,$CF,$8F,$07,$07,$03,$01,$F8,$F8,$FC,$FC,$FE ; ROM 1AE18
    db $03,$FF,$88,$80,$40,$60,$30,$1C,$0F,$87,$E3,$06,$00,$8A,$E0,$FC ; ROM 1AE28
    db $01,$03,$07,$0F,$1F,$3F,$7F,$FF,$04,$F0,$04,$E0,$00,$7F,$00,$7F ; ROM 1AE38
    db $00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$29 ; ROM 1AE48
    db $00,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00,$7F,$00 ; ROM 1AE58
    db $7F,$00,$7F,$00,$29,$00,$00,$85,$07,$00,$85,$01,$02,$04,$00,$82 ; ROM 1AE68
    db $00,$85,$05,$03,$83,$0A,$00,$8E,$03,$08,$03,$08,$83,$08,$00,$00 ; ROM 1AE78
    db $05,$0B,$84,$08,$00,$8F,$01,$05,$10,$85,$12,$13,$11,$15,$02,$04 ; ROM 1AE88
    db $16,$83,$09,$00,$8F,$06,$1A,$82,$1D,$1E,$07,$20,$83,$0D,$00,$83 ; ROM 1AE98
    db $03,$27,$83,$04,$00,$85,$05,$2A,$83,$04,$00,$99,$07,$2F,$81,$00 ; ROM 1AEA8
    db $03,$36,$82,$00,$00,$07,$39,$03,$33,$85,$00,$40,$04,$41,$93,$03 ; ROM 1AEB8
    db $42,$84,$00,$45,$46,$00,$0A,$47,$85,$43,$44,$06,$41,$92,$10,$51 ; ROM 1AEC8
    db $85,$51,$52,$07,$41,$91,$07,$61,$81,$65,$08,$68,$86,$61,$07,$41 ; ROM 1AED8
    db $91,$70,$65,$05,$71,$81,$65,$08,$76,$86,$70,$07,$41,$91,$7E,$65 ; ROM 1AEE8
    db $03,$7F,$84,$00,$82,$65,$65,$07,$83,$8D,$7E,$07,$41,$91,$8A,$65 ; ROM 1AEF8
    db $8B,$00,$8C,$00,$8D,$8E,$65,$04,$8F,$8C,$65,$65,$93,$8A,$00,$7F ; ROM 1AF08
    db $00,$7F,$00,$22,$00,$00,$00,$00,$14,$29,$3E,$1E,$FF,$08,$00,$96 ; ROM 1AF18
    db $FC,$FF,$FF,$C3,$F8,$FF,$FF,$7F,$BF,$C4,$79,$3C,$9F,$47,$31,$98 ; ROM 1AF28
    db $CE,$E7,$E2,$70,$78,$7C,$03,$9F,$83,$8F,$C3,$70,$1E,$00,$1D,$FF ; ROM 1AF38
    db $81,$C0,$09,$00,$03,$FF,$81,$61,$03,$FF,$94,$F3,$3F,$FF,$20,$08 ; ROM 1AF48
    db $C3,$F0,$3C,$0F,$C0,$00,$E1,$7E,$3F,$07,$F1,$FC,$FF,$FF,$70,$1E ; ROM 1AF58
    db $00,$1C,$FF,$81,$C0,$09,$00,$02,$FF,$81,$9F,$03,$FF,$81,$C1,$03 ; ROM 1AF68
    db $FF,$91,$FC,$5F,$F8,$FF,$1C,$03,$C0,$FF,$0F,$C1,$1F,$C0,$F8,$FF ; ROM 1AF78
    db $3E,$80,$80,$1F,$00,$1A,$FF,$82,$FC,$03,$03,$00,$03,$01,$02,$00 ; ROM 1AF88
    db $84,$03,$7F,$FF,$F8,$03,$FF,$81,$F3,$04,$FF,$8E,$0F,$FF,$25,$FF ; ROM 1AF98
    db $1E,$CF,$18,$00,$FF,$FF,$E3,$FF,$0F,$F0,$22,$00,$1A,$FF,$91,$00 ; ROM 1AFA8
    db $F0,$9C,$C7,$31,$1C,$87,$C3,$C1,$E1,$F0,$2F,$FF,$7F,$FF,$FF,$F3 ; ROM 1AFB8
    db $04,$FF,$81,$A0,$03,$FF,$89,$FE,$7F,$FF,$E7,$3F,$80,$FF,$FF,$F0 ; ROM 1AFC8
    db $24,$00,$1A,$FF,$8D,$3F,$00,$C0,$3F,$83,$E4,$38,$9E,$FE,$FF,$3F ; ROM 1AFD8
    db $FF,$E3,$11,$FF,$82,$00,$FC,$26,$00,$1B,$FF,$8D,$0F,$F0,$01,$FF ; ROM 1AFE8
    db $FF,$30,$0F,$43,$3F,$FF,$F3,$FF,$FC,$05,$FF,$81,$27,$06,$FF,$84 ; ROM 1AFF8
    db $C7,$FF,$FF,$80,$28,$00,$1C,$FF,$88,$00,$FF,$F8,$00,$00,$F8,$FF ; ROM 1B008
    db $8F,$03,$FF,$81,$55,$04,$FF,$81,$9F,$04,$FF,$81,$4F,$03,$FF,$81 ; ROM 1B018
    db $FC,$2A,$00,$1B,$FF,$83,$00,$F8,$C0,$03,$00,$84,$07,$FF,$FF,$31 ; ROM 1B028
    db $07,$FF,$83,$FC,$FF,$37,$04,$FF,$82,$F8,$C0,$2B,$00,$19,$FF,$88 ; ROM 1B038
    db $F8,$00,$00,$02,$04,$0D,$1F,$7F,$0F,$FF,$82,$FE,$F0,$2E,$00,$18 ; ROM 1B048
    db $FF,$87,$F0,$0C,$9B,$39,$7D,$FC,$FE,$0B,$FF,$81,$9F,$03,$FF,$82 ; ROM 1B058
    db $FC,$E0,$30,$00,$19,$FF,$8C,$03,$0C,$90,$9C,$CF,$67,$71,$F4,$B3 ; ROM 1B068
    db $FD,$FC,$FE,$07,$FF,$82,$FC,$C0,$32,$00,$1A,$FF,$8B,$3F,$C7,$78 ; ROM 1B078
    db $03,$F8,$FF,$7F,$0F,$E0,$01,$3F,$04,$FF,$82,$FC,$E0,$25,$00,$05 ; ROM 1B088
    db $01,$87,$00,$02,$06,$04,$04,$08,$08,$04,$00,$1C,$FF,$87,$0F,$C0 ; ROM 1B098
    db $00,$F8,$FF,$FF,$0F,$03,$FF,$82,$F8,$E0,$10,$00,$07,$01,$02,$00 ; ROM 1B0A8
    db $03,$01,$8C,$03,$07,$0C,$09,$17,$3F,$28,$70,$70,$40,$C0,$80,$10 ; ROM 1B0B8
    db $00,$1D,$FF,$84,$7F,$00,$0E,$80,$03,$FF,$A5,$E0,$01,$06,$07,$03 ; ROM 1B0C8
    db $02,$02,$06,$04,$0C,$0C,$14,$30,$20,$51,$58,$5C,$CE,$E7,$E0,$FE ; ROM 1B0D8
    db $FF,$0F,$01,$80,$C0,$C0,$E0,$B0,$B0,$B8,$38,$38,$78,$7F,$E1,$80 ; ROM 1B0E8
    db $17,$00,$1D,$FF,$84,$00,$FF,$01,$7F,$04,$FF,$9B,$3F,$4F,$34,$DB ; ROM 1B0F8
    db $C0,$79,$7E,$1F,$0F,$07,$03,$00,$00,$01,$00,$80,$C0,$E0,$F8,$7C ; ROM 1B108
    db $3E,$87,$F3,$7F,$7E,$0F,$01,$06,$00,$88,$F0,$DF,$71,$1C,$0F,$07 ; ROM 1B118
    db $03,$01,$12,$00,$1B,$FF,$A8,$F8,$00,$00,$C0,$FF,$FE,$F8,$E7,$1F ; ROM 1B128
    db $FC,$F0,$80,$F9,$9F,$63,$9E,$46,$91,$90,$E6,$F1,$F9,$7C,$1F,$8F ; ROM 1B138
    db $C7,$61,$60,$F0,$38,$1E,$03,$00,$80,$80,$C0,$F8,$0C,$07,$01,$05 ; ROM 1B148
    db $00,$8D,$F8,$1F,$FF,$FE,$3E,$8F,$C0,$60,$30,$18,$08,$04,$02,$0B ; ROM 1B158
    db $00,$19,$FF,$8E,$F8,$E0,$00,$03,$07,$09,$13,$77,$E7,$CF,$07,$0F ; ROM 1B168
    db $3F,$7F,$03,$FF,$92,$8B,$3F,$C7,$79,$07,$18,$86,$F3,$78,$9F,$CE ; ROM 1B178
    db $F7,$7B,$1D,$0E,$07,$03,$80,$06,$00,$84,$C0,$60,$1C,$03,$04,$00 ; ROM 1B188
    db $86,$80,$E0,$3C,$87,$FF,$07,$10,$00,$18,$FF,$85,$C0,$30,$7B,$FD ; ROM 1B198
    db $FC,$0D,$FF,$81,$F2,$04,$FF,$91,$F0,$38,$AF,$03,$19,$E2,$7C,$BF ; ROM 1B1A8
    db $CF,$60,$10,$CC,$E6,$3F,$0F,$0F,$03,$05,$00,$82,$80,$C0,$07,$00 ; ROM 1B1B8
    db $85,$80,$E0,$38,$04,$03,$0D,$00,$19,$FF,$86,$0F,$40,$8F,$C1,$70 ; ROM 1B1C8
    db $F8,$0A,$FF,$81,$FE,$03,$FF,$9A,$F4,$FF,$1F,$C2,$0F,$83,$F8,$3C ; ROM 1B1D8
    db $CF,$E1,$F9,$FE,$3F,$1F,$03,$00,$80,$80,$C0,$70,$18,$04,$20,$0C ; ROM 1B1E8
    db $07,$01,$08,$00,$85,$C0,$78,$1E,$0F,$83,$0C,$00,$1A,$FF,$86,$7F ; ROM 1B1F8
    db $00,$FE,$07,$00,$80,$06,$FF,$9A,$FE,$FF,$FF,$7B,$FF,$A5,$FF,$1F ; ROM 1B208
    db $FE,$FF,$FD,$FF,$86,$FF,$18,$C9,$FF,$FF,$3E,$EF,$E3,$F9,$FF,$1F ; ROM 1B218
    db $03,$01,$05,$00,$9B,$80,$C0,$30,$00,$80,$78,$3F,$1F,$19,$0E,$07 ; ROM 1B228
    db $03,$01,$00,$E0,$FC,$3B,$0F,$06,$03,$03,$00,$80,$30,$18,$07,$00 ; ROM 1B238
    db $1B,$FF,$87,$1F,$00,$C0,$1F,$07,$00,$FC,$04,$FF,$84,$1F,$FF,$FF ; ROM 1B248
    db $D9,$04,$FF,$81,$7F,$03,$FF,$92,$7E,$FF,$39,$FF,$00,$00,$F0,$7C ; ROM 1B258
    db $9F,$CF,$F1,$FC,$FF,$FF,$1F,$87,$20,$03,$08,$00,$94,$80,$F0,$7F ; ROM 1B268
    db $3F,$87,$C0,$E6,$F3,$78,$FC,$FF,$7F,$1F,$CF,$E7,$79,$1C,$07,$01 ; ROM 1B278
    db $E0,$1B,$FF,$8B,$F8,$07,$FF,$E0,$FF,$3F,$00,$F8,$FF,$FF,$E7,$08 ; ROM 1B288
    db $FF,$9C,$FE,$FF,$CC,$FF,$92,$FF,$C3,$FF,$10,$3F,$0C,$00,$80,$E0 ; ROM 1B298
    db $FC,$7F,$1F,$E0,$FE,$E7,$38,$8E,$F3,$7F,$01,$00,$78,$0F,$04,$00 ; ROM 1B2A8
    db $8B,$C0,$F8,$FF,$78,$06,$C1,$7C,$20,$0F,$F1,$FC,$03,$FF,$84,$7F ; ROM 1B2B8
    db $1F,$C7,$E3,$19,$FF,$86,$FC,$80,$00,$C0,$00,$1F,$03,$FF,$82,$1F ; ROM 1B2C8
    db $FE,$03,$FF,$92,$F4,$FF,$FF,$CF,$FF,$E0,$FF,$36,$FF,$FF,$F0,$FF ; ROM 1B2D8
    db $FA,$3F,$FC,$87,$FC,$0F,$04,$00,$8F,$C0,$FE,$FF,$03,$EC,$F1,$3E ; ROM 1B2E8
    db $87,$E0,$F0,$1E,$0F,$F0,$3F,$03,$04,$00,$90,$80,$FC,$07,$F0,$FC ; ROM 1B2F8
    db $1F,$03,$F0,$7F,$3F,$9F,$E7,$F9,$FC,$FF,$FF,$00,$29,$00,$82,$3C ; ROM 1B308
    db $07,$04,$00,$8D,$03,$80,$C0,$E0,$F8,$FE,$7F,$3F,$1F,$1F,$8F,$87 ; ROM 1B318
    db $83,$03,$E0,$85,$F0,$FC,$FF,$F8,$80,$46,$00,$81,$9E,$03,$00,$94 ; ROM 1B328
    db $0C,$C0,$00,$1F,$07,$00,$00,$C0,$F0,$FF,$FF,$1F,$81,$C0,$F8,$0E ; ROM 1B338
    db $03,$00,$00,$80,$46,$00,$81,$60,$03,$00,$81,$3E,$03,$00,$85,$03 ; ROM 1B348
    db $A0,$07,$00,$03,$03,$00,$88,$F0,$FE,$E0,$3F,$07,$00,$C0,$60,$3A ; ROM 1B358
    db $00,$81,$03,$0C,$00,$81,$07,$03,$00,$81,$0C,$04,$00,$87,$F0,$00 ; ROM 1B368
    db $DA,$00,$E1,$30,$07,$03,$00,$83,$1C,$00,$F0,$3D,$00,$86,$FF,$0F ; ROM 1B378
    db $63,$38,$0E,$03,$05,$00,$86,$D0,$00,$80,$00,$00,$0C,$04,$00,$81 ; ROM 1B388
    db $5F,$03,$00,$84,$01,$80,$00,$18,$43,$00,$89,$C0,$FF,$3F,$C0,$7C ; ROM 1B398
    db $1F,$C7,$61,$01,$03,$00,$81,$1C,$54,$00,$8D,$F0,$FF,$FE,$00,$00 ; ROM 1B3A8
    db $C0,$F0,$FC,$C0,$00,$0C,$00,$03,$05,$00,$81,$D8,$06,$00,$84,$38 ; ROM 1B3B8
    db $00,$00,$60,$44,$00,$81,$FF,$06,$00,$81,$70,$03,$00,$81,$AA,$04 ; ROM 1B3C8
    db $00,$81,$60,$04,$00,$81,$B0,$52,$00,$81,$CE,$07,$00,$83,$03,$00 ; ROM 1B3D8
    db $C8,$7F,$00,$2A,$00,$87,$0F,$03,$04,$06,$02,$03,$01,$0B,$00,$81 ; ROM 1B3E8
    db $60,$4E,$00,$8C,$FC,$FF,$6F,$63,$30,$98,$8E,$0F,$4F,$03,$03,$01 ; ROM 1B3F8
    db $55,$00,$8B,$C0,$F8,$FF,$FF,$07,$00,$80,$F0,$FF,$FE,$C0,$57,$00 ; ROM 1B408
    db $87,$F0,$FF,$FF,$07,$00,$00,$F0,$23,$00,$85,$03,$06,$08,$00,$10 ; ROM 1B418
    db $32,$00,$84,$80,$FF,$FF,$7F,$05,$00,$81,$01,$0B,$00,$03,$20,$84 ; ROM 1B428
    db $30,$18,$1F,$01,$07,$00,$03,$40,$02,$C0,$02,$80,$38,$00,$82,$FE ; ROM 1B438
    db $80,$04,$00,$87,$C0,$F0,$F8,$3C,$3F,$07,$01,$0C,$00,$86,$80,$C0 ; ROM 1B448
    db $78,$0C,$00,$01,$09,$00,$83,$20,$0E,$03,$3F,$00,$89,$80,$E0,$F8 ; ROM 1B458
    db $6E,$6F,$19,$0E,$06,$03,$17,$00,$84,$E0,$00,$01,$01,$3D,$00,$8F ; ROM 1B468
    db $74,$00,$00,$80,$F8,$FF,$7F,$0F,$87,$60,$30,$08,$04,$02,$01,$13 ; ROM 1B478
    db $00,$82,$C0,$78,$2A,$00,$85,$3F,$0F,$04,$02,$03,$0D,$00,$81,$0D ; ROM 1B488
    db $04,$00,$8D,$07,$C0,$D0,$FC,$FE,$1F,$03,$00,$00,$80,$E0,$30,$18 ; ROM 1B498
    db $3D,$00,$86,$F0,$FF,$7F,$3F,$8F,$07,$0A,$00,$81,$01,$03,$00,$84 ; ROM 1B4A8
    db $0B,$00,$E0,$3D,$03,$00,$85,$C0,$30,$1E,$06,$01,$41,$00,$81,$80 ; ROM 1B4B8
    db $04,$FF,$81,$7F,$06,$00,$8F,$01,$00,$00,$84,$00,$5A,$00,$E0,$01 ; ROM 1B4C8
    db $00,$02,$00,$79,$00,$07,$03,$00,$84,$C1,$10,$1C,$06,$11,$00,$82 ; ROM 1B4D8
    db $06,$01,$06,$00,$83,$04,$00,$01,$23,$00,$87,$E0,$FF,$FF,$E0,$F8 ; ROM 1B4E8
    db $FF,$03,$04,$00,$84,$E0,$00,$00,$26,$04,$00,$81,$80,$03,$00,$8C ; ROM 1B4F8
    db $81,$00,$C6,$00,$0F,$00,$00,$80,$60,$30,$0E,$03,$10,$00,$8F,$80 ; ROM 1B508
    db $C0,$78,$3F,$1F,$0F,$07,$03,$00,$80,$E0,$30,$18,$06,$03,$1F,$00 ; ROM 1B518
    db $81,$F8,$03,$00,$86,$C0,$FF,$07,$00,$00,$18,$08,$00,$8B,$01,$00 ; ROM 1B528
    db $33,$00,$6D,$00,$3C,$00,$EF,$C0,$03,$04,$00,$87,$80,$E0,$1F,$01 ; ROM 1B538
    db $18,$07,$01,$0D,$00,$88,$87,$F9,$FE,$FF,$FF,$F0,$0E,$03,$03,$00 ; ROM 1B548
    db $84,$80,$E0,$38,$1C,$22,$00,$82,$E0,$01,$03,$00,$93,$0B,$00,$00 ; ROM 1B558
    db $30,$00,$1F,$00,$C9,$00,$00,$0F,$00,$05,$C0,$03,$78,$03,$F0,$3F ; ROM 1B568
    db $06,$00,$88,$FC,$1F,$0F,$C1,$78,$1F,$0F,$01,$0A,$00,$8C,$F8,$0F ; ROM 1B578
    db $03,$E0,$FC,$0F,$80,$C0,$60,$18,$06,$03,$02,$00,$00,$76,$00,$04 ; ROM 1B588
    db $01,$0C,$03,$02,$01,$4E,$00,$02,$B0,$02,$BC,$02,$FF,$02,$F0,$02 ; ROM 1B598
    db $E0,$02,$C0,$02,$C3,$04,$C0,$02,$E0,$02,$70,$86,$30,$38,$18,$18 ; ROM 1B5A8
    db $0C,$0C,$0C,$00,$85,$0F,$09,$04,$02,$01,$26,$00,$93,$60,$B8,$9C ; ROM 1B5B8
    db $9E,$8F,$CF,$C0,$C7,$FF,$F7,$E7,$27,$23,$33,$33,$21,$E9,$E9,$08 ; ROM 1B5C8
    db $03,$04,$85,$06,$FE,$FE,$0F,$0F,$03,$07,$03,$03,$03,$01,$11,$00 ; ROM 1B5D8
    db $97,$80,$F8,$FF,$7F,$3F,$9F,$4F,$27,$13,$09,$04,$02,$07,$06,$06 ; ROM 1B5E8
    db $0E,$0E,$0C,$0C,$18,$18,$11,$07,$04,$0F,$07,$1F,$0C,$00,$02,$03 ; ROM 1B5F8
    db $86,$83,$03,$8F,$8F,$FF,$FC,$03,$F0,$03,$F8,$03,$FC,$84,$FE,$7E ; ROM 1B608
    db $7E,$7F,$03,$3F,$87,$1F,$9F,$9F,$8F,$CF,$CF,$C7,$03,$E7,$02,$FF ; ROM 1B618
    db $8C,$3D,$31,$39,$18,$18,$1C,$0C,$0C,$0E,$06,$06,$07,$03,$03,$83 ; ROM 1B628
    db $01,$C1,$FD,$07,$FF,$89,$7F,$3F,$9F,$47,$71,$7C,$7E,$7F,$7F,$05 ; ROM 1B638
    db $FF,$05,$EF,$02,$E7,$02,$F7,$92,$F0,$F8,$FC,$FE,$CF,$C7,$F7,$F3 ; ROM 1B648
    db $F1,$F1,$FC,$FC,$EC,$EC,$C0,$C0,$83,$83,$04,$03,$03,$01,$0A,$00 ; ROM 1B658
    db $9F,$03,$FF,$FF,$03,$07,$0C,$8C,$90,$90,$D0,$D0,$C0,$90,$90,$C0 ; ROM 1B668
    db $C0,$E0,$E0,$F0,$7C,$7F,$73,$38,$38,$18,$1C,$1C,$8C,$8E,$8E,$C6 ; ROM 1B678
    db $04,$FC,$09,$FF,$83,$3F,$80,$FF,$06,$00,$02,$C0,$02,$F0,$02,$FC ; ROM 1B688
    db $02,$F0,$05,$00,$8A,$80,$C0,$E0,$F0,$F8,$F8,$FC,$7C,$7E,$3E,$03 ; ROM 1B698
    db $3F,$03,$9F,$87,$8F,$CF,$CF,$87,$87,$B7,$B3,$04,$30,$02,$70,$91 ; ROM 1B6A8
    db $FC,$F2,$E4,$C8,$10,$20,$20,$C0,$F0,$F0,$F8,$D8,$D9,$DF,$EC,$EC ; ROM 1B6B8
    db $7C,$05,$3C,$02,$FC,$0A,$3C,$84,$1F,$07,$00,$C0,$04,$FF,$02,$C0 ; ROM 1B6C8
    db $02,$CF,$84,$13,$F3,$00,$1C,$03,$3C,$81,$38,$03,$00,$02,$06,$02 ; ROM 1B6D8
    db $02,$13,$00,$04,$80,$0A,$C0,$0A,$00,$02,$03,$86,$07,$0F,$1F,$3F ; ROM 1B6E8
    db $7F,$7F,$03,$FF,$05,$DF,$02,$CF,$82,$C7,$C3,$06,$C0,$02,$FF,$02 ; ROM 1B6F8
    db $00,$04,$FF,$02,$00,$04,$FF,$81,$F8,$06,$E0,$87,$F0,$70,$78,$38 ; ROM 1B708
    db $3C,$3C,$3E,$22,$00,$02,$01,$08,$00,$02,$C0,$02,$F0,$03,$FC,$8B ; ROM 1B718
    db $FB,$F8,$F8,$F4,$F4,$EE,$EF,$C7,$C0,$C3,$83,$04,$00,$02,$03,$84 ; ROM 1B728
    db $FF,$FC,$00,$03,$04,$FF,$02,$03,$02,$F3,$82,$F8,$FF,$06,$00,$85 ; ROM 1B738
    db $03,$07,$07,$03,$01,$25,$00,$87,$80,$E0,$70,$38,$1C,$0E,$07,$03 ; ROM 1B748
    db $03,$02,$01,$03,$00,$8A,$20,$60,$C0,$00,$00,$01,$02,$0E,$FC,$F0 ; ROM 1B758
    db $07,$00,$02,$8F,$02,$1F,$81,$3F,$08,$FF,$88,$F8,$03,$FC,$00,$00 ; ROM 1B768
    db $03,$0F,$3F,$05,$FF,$81,$FC,$2D,$00,$02,$80,$09,$C0,$0D,$00,$09 ; ROM 1B778
    db $FF,$89,$FC,$F9,$E2,$8C,$30,$C0,$00,$00,$F8,$03,$FC,$89,$FD,$F1 ; ROM 1B788
    db $F1,$C1,$C1,$03,$03,$0F,$0F,$40,$00,$81,$03,$05,$FF,$88,$FC,$F9 ; ROM 1B798
    db $E2,$CC,$10,$60,$E0,$61,$04,$F3,$04,$F0,$06,$F8,$03,$FC,$81,$FE ; ROM 1B7A8
    db $3D,$00,$91,$03,$0F,$7E,$F9,$F3,$E7,$CE,$9C,$38,$4F,$80,$3F,$3E ; ROM 1B7B8
    db $3C,$30,$00,$F0,$03,$F8,$83,$80,$3E,$3E,$05,$FF,$03,$7F,$02,$3F ; ROM 1B7C8
    db $82,$1F,$0F,$3C,$00,$86,$70,$E0,$40,$C0,$80,$80,$04,$00,$81,$C0 ; ROM 1B7D8
    db $0E,$00,$02,$80,$03,$C0,$02,$E0,$03,$F0,$81,$F8,$7F,$00,$41,$00 ; ROM 1B7E8
    db $00,$76,$00,$04,$02,$0C,$04,$02,$02,$02,$01,$4C,$00,$02,$70,$02 ; ROM 1B7F8
    db $7C,$08,$FF,$04,$FC,$02,$7C,$02,$3C,$02,$9C,$86,$5C,$4C,$2C,$2C ; ROM 1B808
    db $10,$10,$0C,$00,$02,$0F,$83,$07,$03,$01,$26,$00,$8A,$60,$78,$7C ; ROM 1B818
    db $7E,$7F,$3F,$3F,$38,$03,$0F,$03,$1F,$02,$0F,$84,$3F,$37,$F7,$F7 ; ROM 1B828
    db $03,$FB,$83,$F9,$01,$01,$1C,$00,$82,$80,$F8,$04,$FF,$86,$7F,$3F ; ROM 1B838
    db $1F,$0F,$07,$03,$03,$07,$04,$0F,$02,$1F,$82,$1E,$38,$03,$30,$81 ; ROM 1B848
    db $70,$04,$60,$03,$20,$0E,$00,$02,$81,$84,$03,$83,$FF,$FF,$03,$CF ; ROM 1B858
    db $03,$E7,$03,$F3,$03,$F9,$03,$FC,$02,$FE,$83,$7E,$7F,$7F,$03,$3F ; ROM 1B868
    db $02,$1F,$85,$18,$00,$00,$03,$0F,$03,$07,$03,$03,$03,$01,$05,$00 ; ROM 1B878
    db $82,$C0,$FC,$0B,$FF,$85,$BF,$8F,$83,$81,$80,$05,$00,$05,$10,$02 ; ROM 1B888
    db $18,$02,$08,$84,$30,$38,$3C,$3E,$05,$3F,$85,$7F,$73,$73,$F3,$F3 ; ROM 1B898
    db $15,$FF,$96,$FC,$00,$01,$03,$07,$0F,$8F,$9F,$9F,$DF,$DF,$1F,$1F ; ROM 1B8A8
    db $9F,$DF,$DF,$FF,$FF,$EF,$F3,$F0,$F0,$03,$F8,$02,$FC,$84,$7C,$7E ; ROM 1B8B8
    db $7E,$3E,$16,$FF,$02,$3F,$02,$0F,$02,$03,$02,$0F,$05,$00,$8A,$80 ; ROM 1B8C8
    db $C0,$E0,$F0,$F8,$F8,$FC,$FC,$FE,$FE,$0B,$FF,$06,$CF,$02,$8F,$90 ; ROM 1B8D8
    db $1F,$7D,$FB,$F7,$EF,$DF,$DF,$FF,$CF,$CF,$C7,$C7,$C6,$C0,$E3,$E3 ; ROM 1B8E8
    db $06,$C3,$0A,$03,$02,$C3,$82,$E0,$F8,$08,$FF,$02,$F0,$02,$FC,$0E ; ROM 1B8F8
    db $FF,$12,$00,$04,$80,$0F,$C0,$05,$80,$84,$0F,$1F,$3F,$7F,$16,$FF ; ROM 1B908
    db $02,$00,$08,$FF,$04,$00,$81,$07,$06,$1F,$87,$0F,$8F,$87,$C7,$C3 ; ROM 1B918
    db $C3,$C1,$22,$00,$85,$01,$03,$03,$01,$01,$05,$00,$02,$C0,$02,$F0 ; ROM 1B928
    db $02,$FC,$04,$FF,$02,$FB,$83,$F1,$F0,$F8,$07,$FF,$02,$FC,$82,$00 ; ROM 1B938
    db $03,$08,$FF,$04,$0F,$0E,$FF,$22,$00,$8A,$80,$E0,$F0,$F8,$FC,$FE ; ROM 1B948
    db $FF,$FF,$7F,$7F,$05,$3F,$81,$7F,$04,$FF,$86,$FE,$FD,$F1,$02,$0C ; ROM 1B958
    db $F0,$06,$00,$02,$7F,$1C,$FF,$2A,$00,$02,$80,$09,$C0,$02,$80,$0B ; ROM 1B968
    db $00,$15,$FF,$05,$FE,$02,$FC,$02,$F0,$40,$00,$81,$03,$0B,$FF,$02 ; ROM 1B978
    db $9F,$08,$0F,$06,$07,$03,$03,$81,$01,$3D,$00,$97,$03,$0F,$7F,$FF ; ROM 1B988
    db $FE,$FC,$F9,$F2,$E4,$FF,$FF,$C0,$C1,$C2,$CC,$F0,$F0,$F8,$F8,$FC ; ROM 1B998
    db $FC,$FE,$FE,$0C,$FF,$3C,$00,$87,$70,$F0,$E0,$A0,$40,$40,$80,$03 ; ROM 1B9A8
    db $00,$02,$C0,$81,$80,$0C,$00,$02,$80,$03,$C0,$02,$E0,$03,$F0,$81 ; ROM 1B9B8
    db $F8,$7F,$00,$41,$00,$00,$20,$41,$55,$54,$52,$45,$46,$4F,$49,$53 ; ROM 1B9C8
    db $2C,$20,$55,$4E,$45,$20,$52,$41,$43,$45,$20,$44,$45,$20,$47,$45 ; ROM 1B9D8
    db $41,$4E,$54,$53,$FF,$49,$4D,$50,$49,$54,$4F,$59,$41,$42,$4C,$45 ; ROM 1B9E8
    db $53,$20,$53,$45,$20,$52,$45,$42,$45,$4C,$4C,$41,$20,$43,$4F,$4E ; ROM 1B9F8
    db $54,$52,$45,$FF,$4C,$45,$20,$50,$4F,$55,$56,$4F,$49,$52,$20,$44 ; ROM 1BA08
    db $45,$53,$20,$41,$4E,$43,$49,$45,$4E,$53,$2E,$FF,$55,$53,$55,$52 ; ROM 1BA18
    db $50,$45,$53,$2C,$20,$49,$4C,$53,$20,$44,$55,$52,$45,$4E,$54,$20 ; ROM 1BA28
    db $4D,$45,$4E,$45,$52,$20,$55,$4E,$45,$FF,$47,$55,$45,$52,$52,$45 ; ROM 1BA38
    db $20,$42,$52,$55,$54,$41,$4C,$45,$2C,$20,$45,$54,$20,$54,$4F,$4D ; ROM 1BA48
    db $42,$45,$52,$45,$4E,$54,$FF,$4E,$4F,$4D,$42,$52,$45,$55,$58,$20 ; ROM 1BA58
    db $53,$55,$52,$20,$4C,$45,$20,$43,$48,$41,$4D,$50,$20,$44,$45,$FF ; ROM 1BA68
    db $42,$41,$54,$41,$49,$4C,$4C,$45,$2E,$20,$4C,$45,$55,$52,$53,$20 ; ROM 1BA78
    db $41,$44,$4F,$52,$41,$54,$45,$55,$52,$53,$FF,$43,$4F,$4D,$4D,$45 ; ROM 1BA88
    db $4E,$43,$45,$52,$45,$4E,$54,$20,$41,$20,$50,$45,$4E,$53,$45,$52 ; ROM 1BA98
    db $20,$51,$55,$45,$20,$4C,$45,$FF,$54,$45,$4D,$50,$53,$20,$44,$45 ; ROM 1BAA8
    db $53,$20,$41,$4E,$43,$49,$45,$4E,$53,$20,$45,$54,$41,$49,$54,$20 ; ROM 1BAB8
    db $46,$49,$4E,$49,$2E,$FF,$44,$41,$4E,$53,$20,$43,$45,$54,$54,$45 ; ROM 1BAC8
    db $20,$43,$4F,$4E,$46,$55,$53,$49,$4F,$4E,$2C,$20,$55,$4E,$20,$42 ; ROM 1BAD8
    db $52,$41,$56,$45,$FF,$47,$55,$45,$52,$52,$49,$45,$52,$20,$4A,$55 ; ROM 1BAE8
    db $52,$41,$20,$44,$45,$20,$46,$41,$49,$52,$45,$FF,$43,$45,$53,$53 ; ROM 1BAF8
    db $45,$52,$20,$4C,$41,$20,$52,$45,$42,$45,$4C,$4C,$49,$4F,$4E,$2E ; ROM 1BB08
    db $20,$49,$4C,$FF,$43,$4F,$4D,$42,$41,$54,$54,$49,$54,$20,$45,$54 ; ROM 1BB18
    db $20,$52,$45,$55,$53,$53,$49,$54,$2C,$20,$4D,$41,$49,$53,$FF,$53 ; ROM 1BB28
    db $45,$55,$4C,$45,$4D,$45,$4E,$54,$20,$50,$41,$52,$43,$45,$20,$51 ; ROM 1BB38
    db $55,$26,$49,$4C,$FF,$50,$4F,$53,$53,$45,$44,$41,$49,$54,$20,$4C ; ROM 1BB48
    db $41,$20,$48,$41,$43,$48,$45,$20,$44,$26,$4F,$52,$20,$2D,$FF,$55 ; ROM 1BB58
    db $4E,$20,$43,$41,$44,$45,$41,$55,$20,$44,$45,$20,$4C,$26,$45,$53 ; ROM 1BB68
    db $50,$52,$49,$54,$20,$44,$45,$FF,$46,$4F,$55,$44,$52,$45,$20,$44 ; ROM 1BB78
    db $45,$20,$54,$48,$4F,$52,$2E,$FF,$FF,$20,$44,$45,$20,$4E,$4F,$4D ; ROM 1BB88
    db $42,$52,$45,$55,$53,$45,$53,$20,$41,$4E,$4E,$45,$45,$53,$FF,$50 ; ROM 1BB98
    db $41,$53,$53,$45,$52,$45,$4E,$54,$2C,$20,$45,$54,$20,$4C,$26,$49 ; ROM 1BBA8
    db $4E,$43,$49,$44,$45,$4E,$54,$FF,$41,$4D,$45,$52,$20,$45,$54,$41 ; ROM 1BBB8
    db $49,$54,$20,$50,$52,$45,$53,$51,$55,$45,$20,$4F,$55,$42,$4C,$49 ; ROM 1BBC8
    db $45,$20,$2D,$FF,$4F,$55,$42,$4C,$49,$45,$20,$50,$41,$52,$20,$54 ; ROM 1BBD8
    db $4F,$55,$53,$2C,$20,$53,$41,$55,$46,$20,$50,$41,$52,$20,$4C,$45 ; ROM 1BBE8
    db $FF,$56,$49,$4C,$20,$47,$45,$41,$4E,$54,$2C,$20,$44,$45,$41,$54 ; ROM 1BBF8
    db $48,$20,$41,$44,$44,$45,$52,$2E,$20,$54,$4F,$55,$53,$FF,$56,$49 ; ROM 1BC08
    db $56,$41,$49,$45,$4E,$54,$20,$45,$4E,$20,$50,$41,$49,$58,$20,$45 ; ROM 1BC18
    db $54,$20,$44,$41,$4E,$53,$20,$4C,$41,$FF,$4A,$4F,$49,$45,$20,$44 ; ROM 1BC28
    db $41,$4E,$53,$20,$4C,$45,$20,$50,$41,$59,$53,$20,$44,$45,$20,$46 ; ROM 1BC38
    db $49,$52,$45,$57,$4F,$4F,$44,$2C,$FF,$55,$4E,$45,$20,$43,$4F,$4E ; ROM 1BC48
    db $54,$52,$45,$45,$20,$44,$49,$52,$49,$47,$45,$45,$20,$50,$41,$52 ; ROM 1BC58
    db $20,$55,$4E,$45,$FF,$46,$41,$4D,$49,$4C,$4C,$45,$20,$51,$55,$49 ; ROM 1BC68
    db $20,$41,$56,$41,$49,$54,$20,$4D,$41,$49,$54,$52,$49,$53,$45,$FF ; ROM 1BC78
    db $4C,$41,$20,$4D,$41,$47,$49,$45,$20,$44,$45,$53,$20,$4E,$45,$55 ; ROM 1BC88
    db $46,$20,$43,$52,$49,$53,$54,$41,$55,$58,$2C,$FF,$52,$45,$4C,$49 ; ROM 1BC98
    db $51,$55,$45,$53,$20,$45,$43,$41,$52,$54,$41,$4E,$54,$20,$4C,$45 ; ROM 1BCA8
    db $20,$4D,$41,$4C,$20,$45,$54,$FF,$50,$52,$45,$53,$45,$52,$56,$41 ; ROM 1BCB8
    db $4E,$54,$20,$4C,$41,$20,$50,$41,$49,$58,$2C,$20,$41,$49,$4E,$53 ; ROM 1BCC8
    db $49,$FF,$51,$55,$45,$20,$4C,$45,$53,$20,$53,$4F,$52,$54,$53,$20 ; ROM 1BCD8
    db $44,$45,$20,$4C,$41,$20,$46,$4F,$55,$44,$52,$45,$2C,$FF,$44,$45 ; ROM 1BCE8
    db $20,$4C,$41,$20,$54,$45,$52,$52,$45,$20,$45,$54,$20,$44,$55,$20 ; ROM 1BCF8
    db $46,$45,$55,$2E,$20,$4E,$45,$FF,$50,$4F,$55,$56,$41,$4E,$54,$20 ; ROM 1BD08
    db $41,$54,$54,$41,$51,$55,$45,$52,$20,$46,$49,$52,$45,$57,$4F,$4F ; ROM 1BD18
    db $44,$2C,$FF,$44,$45,$41,$54,$48,$20,$41,$44,$44,$45,$52,$20,$43 ; ROM 1BD28
    db $4F,$4E,$51,$55,$49,$54,$20,$4E,$45,$4E,$44,$4F,$52,$49,$41,$FF ; ROM 1BD38
    db $45,$54,$20,$41,$4C,$54,$4F,$52,$55,$4C,$49,$41,$2C,$20,$4D,$41 ; ROM 1BD48
    db $49,$53,$20,$41,$54,$54,$45,$4E,$44,$41,$49,$54,$FF,$4C,$45,$20 ; ROM 1BD58
    db $4A,$4F,$55,$52,$20,$4F,$55,$20,$49,$4C,$20,$50,$4F,$55,$52,$52 ; ROM 1BD68
    db $41,$49,$54,$20,$45,$4E,$46,$49,$4E,$FF,$56,$41,$49,$4E,$43,$52 ; ROM 1BD78
    db $45,$20,$46,$49,$52,$45,$57,$4F,$4F,$44,$2E,$FF,$FF,$46,$49,$4E ; ROM 1BD88
    db $41,$4C,$45,$4D,$45,$4E,$54,$2C,$20,$55,$4E,$20,$43,$55,$50,$49 ; ROM 1BD98
    db $44,$45,$20,$47,$52,$41,$4E,$44,$FF,$4D,$49,$4E,$49,$53,$54,$52 ; ROM 1BDA8
    db $45,$20,$44,$45,$20,$46,$49,$52,$45,$57,$4F,$4F,$44,$20,$54,$52 ; ROM 1BDB8
    db $41,$48,$49,$54,$FF,$4C,$45,$20,$52,$4F,$49,$20,$45,$4E,$20,$56 ; ROM 1BDC8
    db $45,$4E,$44,$41,$4E,$54,$20,$4C,$45,$53,$20,$47,$45,$4D,$4D,$45 ; ROM 1BDD8
    db $53,$FF,$41,$55,$20,$44,$45,$4D,$4F,$4E,$49,$41,$51,$55,$45,$20 ; ROM 1BDE8
    db $44,$45,$41,$54,$48,$20,$41,$44,$44,$45,$52,$2E,$FF,$46,$49,$52 ; ROM 1BDF8
    db $45,$57,$4F,$4F,$44,$20,$54,$4F,$4D,$42,$41,$20,$56,$49,$54,$45 ; ROM 1BE08
    db $20,$45,$54,$20,$46,$55,$54,$FF,$42,$52,$55,$4C,$45,$2E,$20,$44 ; ROM 1BE18
    db $45,$53,$20,$48,$45,$52,$4F,$53,$20,$44,$45,$20,$46,$49,$52,$45 ; ROM 1BE28
    db $57,$4F,$4F,$44,$FF,$56,$4F,$55,$4C,$55,$52,$45,$4E,$54,$20,$54 ; ROM 1BE38
    db $55,$45,$52,$20,$44,$45,$41,$54,$48,$20,$41,$44,$44,$45,$52,$2C ; ROM 1BE48
    db $FF,$4D,$41,$49,$53,$20,$53,$45,$53,$20,$4D,$4F,$4E,$53,$54,$52 ; ROM 1BE58
    db $45,$53,$20,$54,$45,$52,$52,$49,$46,$49,$41,$4E,$54,$53,$FF,$53 ; ROM 1BE68
    db $45,$4D,$42,$4C,$41,$49,$45,$4E,$54,$20,$45,$54,$52,$45,$20,$50 ; ROM 1BE78
    db $41,$52,$54,$4F,$55,$54,$2E,$FF,$4C,$41,$49,$53,$53,$45,$20,$41 ; ROM 1BE88
    db $20,$4C,$55,$49,$2D,$4D,$45,$4D,$45,$2C,$20,$4C,$45,$20,$4D,$4F ; ROM 1BE98
    db $4E,$44,$45,$FF,$53,$45,$52,$41,$49,$54,$20,$54,$4F,$4D,$42,$45 ; ROM 1BEA8
    db $20,$53,$4F,$55,$53,$20,$53,$4F,$4E,$20,$52,$45,$47,$4E,$45,$FF ; ROM 1BEB8
    db $44,$45,$4D,$4F,$4E,$49,$41,$51,$55,$45,$21,$20,$42,$49,$45,$4E ; ROM 1BEC8
    db $20,$53,$55,$52,$2C,$20,$4A,$55,$53,$51,$55,$26,$41,$FF,$43,$45 ; ROM 1BED8
    db $20,$51,$55,$26,$55,$4E,$20,$48,$45,$52,$4F,$53,$20,$45,$4D,$45 ; ROM 1BEE8
    db $52,$47,$45,$2C,$20,$41,$53,$53,$45,$5A,$FF,$42,$52,$41,$56,$45 ; ROM 1BEF8
    db $20,$50,$4F,$55,$52,$20,$46,$41,$49,$52,$45,$20,$43,$45,$53,$53 ; ROM 1BF08
    db $45,$52,$20,$4C,$45,$FF,$52,$45,$47,$4E,$45,$20,$44,$45,$20,$44 ; ROM 1BF18
    db $45,$41,$54,$48,$20,$41,$44,$44,$45,$52,$2E,$2E,$2E,$FF,$FF,$FF ; ROM 1BF28
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$00,$FF,$FF,$FF,$FF,$FF ; ROM 1BF38
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BF48
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BF58
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BF68
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BF78
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BF88
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BF98
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BFA8
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BFB8
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BFC8
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BFD8
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BFE8
    db $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; ROM 1BFF8
