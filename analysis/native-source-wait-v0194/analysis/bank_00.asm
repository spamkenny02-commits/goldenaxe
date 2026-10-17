; ROM bank 00; file offset $00000; CPU window $0000
; Fixed-window static reachability plus optional bank-aware execution observations.
; DB = unclassified data/code. No claim of complete decompilation.
    org $0000
    DI                             ; ROM 00000: f3
    IM 1                           ; ROM 00001: ed56
    JP $0089                       ; ROM 00003: c38900
    db $00,$00 ; ROM 00006
    ADD A,L                        ; ROM 00008: 85
    LD L,A                         ; ROM 00009: 6f
    JR nc,$000d                    ; ROM 0000A: 3001
    INC H                          ; ROM 0000C: 24
    LD A,(HL)                      ; ROM 0000D: 7e
    INC HL                         ; ROM 0000E: 23
    LD H,(HL)                      ; ROM 0000F: 66
    LD L,A                         ; ROM 00010: 6f
    RET                            ; ROM 00011: c9
    db $00,$00,$00,$00,$00,$00 ; ROM 00012
    ADD A,L                        ; ROM 00018: 85
    LD L,A                         ; ROM 00019: 6f
    JR nc,$001d                    ; ROM 0001A: 3001
    INC H                          ; ROM 0001C: 24
    LD A,(HL)                      ; ROM 0001D: 7e
    INC HL                         ; ROM 0001E: 23
    LD H,(HL)                      ; ROM 0001F: 66
    LD L,A                         ; ROM 00020: 6f
    JP (HL)                        ; ROM 00021: e9
    db $00,$00,$00,$00,$00,$00 ; ROM 00022
    DI                             ; ROM 00028: f3
    LD A,E                         ; ROM 00029: 7b
    OUT ($00bf),A                  ; ROM 0002A: d3bf
    LD A,D                         ; ROM 0002C: 7a
    OUT ($00bf),A                  ; ROM 0002D: d3bf
    EI                             ; ROM 0002F: fb
    RET                            ; ROM 00030: c9
    db $00,$00,$00,$00,$00,$00,$00 ; ROM 00031
    PUSH AF                        ; ROM 00038: f5
    IN A,($00bf)                   ; ROM 00039: dbbf
    OR A                           ; ROM 0003B: b7
    JP p,$025e                     ; ROM 0003C: f25e02
    LD ($c01b),A                   ; ROM 0003F: 321bc0
    JP $0137                       ; ROM 00042: c33701
    db $80,$40,$20,$10,$08,$04,$02,$01,$01,$02,$04,$08,$10,$20,$40,$80 ; ROM 00045
    db $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00 ; ROM 00055
    db $00 ; ROM 00065
    PUSH AF                        ; ROM 00066: f5
    LD A,($c01c)                   ; ROM 00067: 3a1cc0
    OR A                           ; ROM 0006A: b7
    JR nz,$0072                    ; ROM 0006B: 2005
    LD A,$14                       ; ROM 0006D: 3e14
    LD ($c01c),A                   ; ROM 0006F: 321cc0
    POP AF                         ; ROM 00072: f1
    RETN                           ; ROM 00073: ed45
    db $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00 ; ROM 00075
    JP $0a78                       ; ROM 00080: c3780a
    db $C3,$65,$03,$C3,$97,$03 ; ROM 00083
    LD SP,$dff0                    ; ROM 00089: 31f0df
    LD HL,$fffc                    ; ROM 0008C: 21fcff
    LD (HL),$80                    ; ROM 0008F: 3680
    INC HL                         ; ROM 00091: 23
    LD (HL),0                      ; ROM 00092: 3600
    INC HL                         ; ROM 00094: 23
    LD (HL),1                      ; ROM 00095: 3601
    INC HL                         ; ROM 00097: 23
    LD (HL),2                      ; ROM 00098: 3602
    DI                             ; ROM 0009A: f3
    LD SP,$dff0                    ; ROM 0009B: 31f0df
    LD HL,$c010                    ; ROM 0009E: 2110c0
    LD DE,$c011                    ; ROM 000A1: 1111c0
    LD BC,$1fdf                    ; ROM 000A4: 01df1f
    LD (HL),0                      ; ROM 000A7: 3600
    LDIR                           ; ROM 000A9: edb0
    LD BC,$9c6                     ; ROM 000AB: 01c609
    IN A,($00bf)                   ; ROM 000AE: dbbf
    IN A,($00bf)                   ; ROM 000B0: dbbf
    RLCA                           ; ROM 000B2: 07
    JR nc,$00b0                    ; ROM 000B3: 30fb
    DEC BC                         ; ROM 000B5: 0b
    LD A,C                         ; ROM 000B6: 79
    OR B                           ; ROM 000B7: b0
    JR nz,$00b5                    ; ROM 000B8: 20fb
    IN A,($00bf)                   ; ROM 000BA: dbbf
    AND $80                        ; ROM 000BC: e680
    LD ($de03),A                   ; ROM 000BE: 3203de
    CALL $0404                     ; ROM 000C1: cd0404
    CALL $03c0                     ; ROM 000C4: cdc003
    LD HL,$dd00                    ; ROM 000C7: 2100dd
    LD (HL),0                      ; ROM 000CA: 3600
    LD ($c034),HL                  ; ROM 000CC: 2234c0
    CALL $0b95                     ; ROM 000CF: cd950b
    LD A,($c01d)                   ; ROM 000D2: 3a1dc0
    LD HL,$dc                      ; ROM 000D5: 21dc00
    RST $18                        ; ROM 000D8: df
    JP $00d2                       ; ROM 000D9: c3d200
    db $6D,$14,$F4,$00,$33,$24,$6F,$24,$B6,$24,$C5,$24,$F3,$24,$BE,$6E ; ROM 000DC
    db $F2,$70,$01,$11,$7D,$25,$90,$73 ; ROM 000EC
    CALL $638d                     ; ROM 000F4: cd8d63
    LD HL,$12d                     ; ROM 000F7: 212d01
    LD DE,$db58                    ; ROM 000FA: 1158db
    CALL $0812                     ; ROM 000FD: cd1208
    CALL $229c                     ; ROM 00100: cd9c22
    CALL $0120                     ; ROM 00103: cd2001
    LD A,$80                       ; ROM 00106: 3e80
    LD ($de0a),A                   ; ROM 00108: 320ade
    CALL $0b95                     ; ROM 0010B: cd950b
    LD A,($c023)                   ; ROM 0010E: 3a23c0
    OR A                           ; ROM 00111: b7
    JR z,$010b                     ; ROM 00112: 28f7
    CALL $6384                     ; ROM 00114: cd8463
    XOR A                          ; ROM 00117: af
    LD ($de0a),A                   ; ROM 00118: 320ade
    LD A,12                        ; ROM 0011B: 3e0c
    LD ($c01d),A                   ; ROM 0011D: 321dc0
    LD A,$ac                       ; ROM 00120: 3eac
    LD ($de08),A                   ; ROM 00122: 3208de
    LD B,$14                       ; ROM 00125: 0614
    CALL $0b95                     ; ROM 00127: cd950b
    DJNZ $0127                     ; ROM 0012A: 10fb
    RET                            ; ROM 0012C: c9
    db $2D,$20,$50,$41,$55,$53,$45,$20,$2D,$00 ; ROM 0012D
    LD A,($c02e)                   ; ROM 00137: 3a2ec0
    OR A                           ; ROM 0013A: b7
    JP z,$01e3                     ; ROM 0013B: cae301
    LD HL,$c01a                    ; ROM 0013E: 211ac0
    LD BC,$8bbf                    ; ROM 00141: 01bf8b
    OUTD                           ; ROM 00144: edab
    OUT (C),B                      ; ROM 00146: ed41
    OUTD                           ; ROM 00148: edab
    OUT (C),B                      ; ROM 0014A: ed41
    OUTD                           ; ROM 0014C: edab
    OUT (C),B                      ; ROM 0014E: ed41
    LD A,4                         ; ROM 00150: 3e04
    LD ($ffff),A                   ; ROM 00152: 32ffff
    XOR A                          ; ROM 00155: af
    OUT ($00bf),A                  ; ROM 00156: d3bf
    LD A,$7f                       ; ROM 00158: 3e7f
    OUT ($00bf),A                  ; ROM 0015A: d3bf
    LD C,$be                       ; ROM 0015C: 0ebe
    LD HL,$dd40                    ; ROM 0015E: 2140dd
    CALL $8080                     ; ROM 00161: cd8080
    INC A                          ; ROM 00164: 3c
    OUT ($00bf),A                  ; ROM 00165: d3bf
    DEC A                          ; ROM 00167: 3d
    OUT ($00bf),A                  ; ROM 00168: d3bf
    CALL $8000                     ; ROM 0016A: cd0080
    CALL $3b07                     ; ROM 0016D: cd073b
    CALL $1f54                     ; ROM 00170: cd541f
    LD A,($c033)                   ; ROM 00173: 3a33c0
    OR A                           ; ROM 00176: b7
    JR nz,$0199                    ; ROM 00177: 2020
    LD HL,$e0f0                    ; ROM 00179: 21f0e0
    LD A,($de03)                   ; ROM 0017C: 3a03de
    OR A                           ; ROM 0017F: b7
    JR nz,$0183                    ; ROM 00180: 2001
    LD H,L                         ; ROM 00182: 65
    IN A,($007e)                   ; ROM 00183: db7e
    CP H                           ; ROM 00185: bc
    JR c,$0183                     ; ROM 00186: 38fb
    XOR A                          ; ROM 00188: af
    OUT ($00bf),A                  ; ROM 00189: d3bf
    LD A,$c0                       ; ROM 0018B: 3ec0
    OUT ($00bf),A                  ; ROM 0018D: d3bf
    LD HL,$dca0                    ; ROM 0018F: 21a0dc
    LD BC,$40be                    ; ROM 00192: 01be40
    OUTI                           ; ROM 00195: eda3
    DJNZ $0195                     ; ROM 00197: 10fc
    CALL $0293                     ; ROM 00199: cd9302
    EI                             ; ROM 0019C: fb
    LD A,6                         ; ROM 0019D: 3e06
    LD ($ffff),A                   ; ROM 0019F: 32ffff
    CALL $8000                     ; ROM 001A2: cd0080
    LD A,($c01c)                   ; ROM 001A5: 3a1cc0
    OR A                           ; ROM 001A8: b7
    JR z,$01b1                     ; ROM 001A9: 2806
    DEC A                          ; ROM 001AB: 3d
    LD ($c01c),A                   ; ROM 001AC: 321cc0
    LD A,1                         ; ROM 001AF: 3e01
    LD HL,$c022                    ; ROM 001B1: 2122c0
    LD B,A                         ; ROM 001B4: 47
    XOR (HL)                       ; ROM 001B5: ae
    LD (HL),B                      ; ROM 001B6: 70
    INC HL                         ; ROM 001B7: 23
    AND B                          ; ROM 001B8: a0
    LD (HL),A                      ; ROM 001B9: 77
    IN A,($00dc)                   ; ROM 001BA: dbdc
    CPL                            ; ROM 001BC: 2f
    AND $3f                        ; ROM 001BD: e63f
    LD HL,$c020                    ; ROM 001BF: 2120c0
    LD B,A                         ; ROM 001C2: 47
    XOR (HL)                       ; ROM 001C3: ae
    LD (HL),B                      ; ROM 001C4: 70
    INC HL                         ; ROM 001C5: 23
    AND B                          ; ROM 001C6: a0
    LD (HL),A                      ; ROM 001C7: 77
    IN A,($00dd)                   ; ROM 001C8: dbdd
    AND $10                        ; ROM 001CA: e610
    JP z,$009a                     ; ROM 001CC: ca9a00
    LD A,($c030)                   ; ROM 001CF: 3a30c0
    OR A                           ; ROM 001D2: b7
    JR z,$01d9                     ; ROM 001D3: 2804
    DEC A                          ; ROM 001D5: 3d
    LD ($c030),A                   ; ROM 001D6: 3230c0
    LD HL,$c02f                    ; ROM 001D9: 212fc0
    INC (HL)                       ; ROM 001DC: 34
    XOR A                          ; ROM 001DD: af
    LD ($c02e),A                   ; ROM 001DE: 322ec0
    POP AF                         ; ROM 001E1: f1
    RET                            ; ROM 001E2: c9
    PUSH BC                        ; ROM 001E3: c5
    PUSH DE                        ; ROM 001E4: d5
    PUSH HL                        ; ROM 001E5: e5
    EX AF,AF'                      ; ROM 001E6: 08
    EXX                            ; ROM 001E7: d9
    PUSH AF                        ; ROM 001E8: f5
    PUSH BC                        ; ROM 001E9: c5
    PUSH DE                        ; ROM 001EA: d5
    PUSH HL                        ; ROM 001EB: e5
    PUSH IX                        ; ROM 001EC: dde5
    PUSH IY                        ; ROM 001EE: fde5
    LD A,($ffff)                   ; ROM 001F0: 3affff
    PUSH AF                        ; ROM 001F3: f5
    LD A,($fffc)                   ; ROM 001F4: 3afcff
    PUSH AF                        ; ROM 001F7: f5
    AND $f7                        ; ROM 001F8: e6f7
    LD ($fffc),A                   ; ROM 001FA: 32fcff
    LD A,6                         ; ROM 001FD: 3e06
    LD ($ffff),A                   ; ROM 001FF: 32ffff
    CALL $8000                     ; ROM 00202: cd0080
    LD A,($c030)                   ; ROM 00205: 3a30c0
    OR A                           ; ROM 00208: b7
    JR z,$020f                     ; ROM 00209: 2804
    DEC A                          ; ROM 0020B: 3d
    LD ($c030),A                   ; ROM 0020C: 3230c0
    POP AF                         ; ROM 0020F: f1
    LD ($fffc),A                   ; ROM 00210: 32fcff
    POP AF                         ; ROM 00213: f1
    LD ($ffff),A                   ; ROM 00214: 32ffff
    POP IY                         ; ROM 00217: fde1
    POP IX                         ; ROM 00219: dde1
    POP HL                         ; ROM 0021B: e1
    POP DE                         ; ROM 0021C: d1
    POP BC                         ; ROM 0021D: c1
    POP AF                         ; ROM 0021E: f1
    EXX                            ; ROM 0021F: d9
    EX AF,AF'                      ; ROM 00220: 08
    POP HL                         ; ROM 00221: e1
    POP DE                         ; ROM 00222: d1
    POP BC                         ; ROM 00223: c1
    POP AF                         ; ROM 00224: f1
    EI                             ; ROM 00225: fb
    RET                            ; ROM 00226: c9
    XOR A                          ; ROM 00227: af
    LD ($c018),A                   ; ROM 00228: 3218c0
    LD HL,$263                     ; ROM 0022B: 216302
    LD A,($c010)                   ; ROM 0022E: 3a10c0
    AND $ef                        ; ROM 00231: e6ef
    LD ($c02c),HL                  ; ROM 00233: 222cc0
    LD ($c010),A                   ; ROM 00236: 3210c0
    OUT ($00bf),A                  ; ROM 00239: d3bf
    LD A,$80                       ; ROM 0023B: 3e80
    OUT ($00bf),A                  ; ROM 0023D: d3bf
    RET                            ; ROM 0023F: c9
    LD A,$9f                       ; ROM 00240: 3e9f
    LD ($c01a),A                   ; ROM 00242: 321ac0
    LD HL,$275                     ; ROM 00245: 217502
    LD A,($c010)                   ; ROM 00248: 3a10c0
    OR $10                         ; ROM 0024B: f610
    JR $0233                       ; ROM 0024D: 18e4
    LD A,$bb                       ; ROM 0024F: 3ebb
    LD ($c01a),A                   ; ROM 00251: 321ac0
    LD HL,$280                     ; ROM 00254: 218002
    LD A,($c010)                   ; ROM 00257: 3a10c0
    OR $10                         ; ROM 0025A: f610
    JR $0233                       ; ROM 0025C: 18d5
    PUSH HL                        ; ROM 0025E: e5
    LD HL,($c02c)                  ; ROM 0025F: 2a2cc0
    JP (HL)                        ; ROM 00262: e9
    db $3A,$10,$C0,$E6,$EF,$32,$10,$C0,$D3,$BF,$3E,$80,$D3,$BF,$E1,$F1 ; ROM 00263
    db $FB,$C9 ; ROM 00273
    XOR A                          ; ROM 00275: af
    OUT ($00bf),A                  ; ROM 00276: d3bf
    LD A,$88                       ; ROM 00278: 3e88
    OUT ($00bf),A                  ; ROM 0027A: d3bf
    POP HL                         ; ROM 0027C: e1
    POP AF                         ; ROM 0027D: f1
    EI                             ; ROM 0027E: fb
    RET                            ; ROM 0027F: c9
    LD A,$10                       ; ROM 00280: 3e10
    OUT ($00bf),A                  ; ROM 00282: d3bf
    LD A,$c0                       ; ROM 00284: 3ec0
    OUT ($00bf),A                  ; ROM 00286: d3bf
    LD A,$21                       ; ROM 00288: 3e21
    DEC A                          ; ROM 0028A: 3d
    JR nz,$028a                    ; ROM 0028B: 20fd
    OUT ($00be),A                  ; ROM 0028D: d3be
    POP HL                         ; ROM 0028F: e1
    POP AF                         ; ROM 00290: f1
    EI                             ; ROM 00291: fb
    RET                            ; ROM 00292: c9
    LD HL,($c034)                  ; ROM 00293: 2a34c0
    LD (HL),0                      ; ROM 00296: 3600
    LD IY,$dd00                    ; ROM 00298: fd2100dd
    LD A,(IY)                      ; ROM 0029C: fd7e00
    CP 1                           ; ROM 0029F: fe01
    JP z,$02af                     ; ROM 002A1: caaf02
    JP nc,$02f7                    ; ROM 002A4: d2f702
    LD HL,$dd00                    ; ROM 002A7: 2100dd
    LD ($c034),HL                  ; ROM 002AA: 2234c0
    LD (HL),A                      ; ROM 002AD: 77
    RET                            ; ROM 002AE: c9
    LD C,$be                       ; ROM 002AF: 0ebe
    LD A,(IY+4)                    ; ROM 002B1: fd7e04
    OUT ($00bf),A                  ; ROM 002B4: d3bf
    LD A,(IY+5)                    ; ROM 002B6: fd7e05
    OUT ($00bf),A                  ; ROM 002B9: d3bf
    LD L,(IY+2)                    ; ROM 002BB: fd6e02
    LD H,(IY+3)                    ; ROM 002BE: fd6603
    LD A,(IY+1)                    ; ROM 002C1: fd7e01
    OR A                           ; ROM 002C4: b7
    JP m,$02de                     ; ROM 002C5: fade02
    LD ($ffff),A                   ; ROM 002C8: 32ffff
    LD A,(IY+6)                    ; ROM 002CB: fd7e06
    LD B,$40                       ; ROM 002CE: 0640
    OUTI                           ; ROM 002D0: eda3
    DJNZ $02d0                     ; ROM 002D2: 10fc
    DEC A                          ; ROM 002D4: 3d
    JR nz,$02ce                    ; ROM 002D5: 20f7
    LD DE,7                        ; ROM 002D7: 110700
    ADD IY,DE                      ; ROM 002DA: fd19
    JR $029c                       ; ROM 002DC: 18be
    CALL $0444                     ; ROM 002DE: cd4404
    LD A,(IY+6)                    ; ROM 002E1: fd7e06
    LD B,$40                       ; ROM 002E4: 0640
    OUTI                           ; ROM 002E6: eda3
    DJNZ $02e6                     ; ROM 002E8: 10fc
    DEC A                          ; ROM 002EA: 3d
    JR nz,$02e4                    ; ROM 002EB: 20f7
    LD DE,7                        ; ROM 002ED: 110700
    ADD IY,DE                      ; ROM 002F0: fd19
    CALL $043a                     ; ROM 002F2: cd3a04
    JR $029c                       ; ROM 002F5: 18a5
    LD C,$be                       ; ROM 002F7: 0ebe
    LD L,(IY+3)                    ; ROM 002F9: fd6e03
    LD H,(IY+4)                    ; ROM 002FC: fd6604
    EX DE,HL                       ; ROM 002FF: eb
    LD HL,$a200                    ; ROM 00300: 2100a2
    ADD HL,DE                      ; ROM 00303: 19
    LD A,L                         ; ROM 00304: 7d
    OUT ($00bf),A                  ; ROM 00305: d3bf
    LD A,H                         ; ROM 00307: 7c
    OUT ($00bf),A                  ; ROM 00308: d3bf
    LD L,E                         ; ROM 0030A: 6b
    LD H,D                         ; ROM 0030B: 62
    LD A,(IY+2)                    ; ROM 0030C: fd7e02
    ADD A,A                        ; ROM 0030F: 87
    OUTI                           ; ROM 00310: eda3
    DEC A                          ; ROM 00312: 3d
    JP nz,$0310                    ; ROM 00313: c21003
    LD HL,$40                      ; ROM 00316: 214000
    ADD HL,DE                      ; ROM 00319: 19
    DEC (IY+1)                     ; ROM 0031A: fd3501
    JR nz,$02ff                    ; ROM 0031D: 20e0
    LD DE,5                        ; ROM 0031F: 110500
    ADD IY,DE                      ; ROM 00322: fd19
    JP $029c                       ; ROM 00324: c39c02
    LD ($ffff),A                   ; ROM 00327: 32ffff
    LD C,4                         ; ROM 0032A: 0e04
    LD B,C                         ; ROM 0032C: 41
    PUSH BC                        ; ROM 0032D: c5
    PUSH DE                        ; ROM 0032E: d5
    LD A,(HL)                      ; ROM 0032F: 7e
    INC HL                         ; ROM 00330: 23
    OR A                           ; ROM 00331: b7
    JR z,$0350                     ; ROM 00332: 281c
    LD B,A                         ; ROM 00334: 47
    RES 7,B                        ; ROM 00335: cbb8
    RLCA                           ; ROM 00337: 07
    EX AF,AF'                      ; ROM 00338: 08
    RST $28                        ; ROM 00339: ef
    LD A,(HL)                      ; ROM 0033A: 7e
    OUT ($00be),A                  ; ROM 0033B: d3be
    EX AF,AF'                      ; ROM 0033D: 08
    JR nc,$0341                    ; ROM 0033E: 3001
    INC HL                         ; ROM 00340: 23
    EX AF,AF'                      ; ROM 00341: 08
    LD A,C                         ; ROM 00342: 79
    ADD A,E                        ; ROM 00343: 83
    LD E,A                         ; ROM 00344: 5f
    JR nc,$0348                    ; ROM 00345: 3001
    INC D                          ; ROM 00347: 14
    DJNZ $0339                     ; ROM 00348: 10ef
    EX AF,AF'                      ; ROM 0034A: 08
    JR c,$032f                     ; ROM 0034B: 38e2
    INC HL                         ; ROM 0034D: 23
    JR $032f                       ; ROM 0034E: 18df
    LD ($c031),DE                  ; ROM 00350: ed5331c0
    POP DE                         ; ROM 00354: d1
    INC DE                         ; ROM 00355: 13
    POP BC                         ; ROM 00356: c1
    DJNZ $032d                     ; ROM 00357: 10d4
    LD DE,($c031)                  ; ROM 00359: ed5b31c0
    INC DE                         ; ROM 0035D: 13
    LD A,E                         ; ROM 0035E: 7b
    SUB C                          ; ROM 0035F: 91
    LD E,A                         ; ROM 00360: 5f
    JR nc,$0364                    ; ROM 00361: 3001
    DEC D                          ; ROM 00363: 15
    RET                            ; ROM 00364: c9
    LD ($c01f),A                   ; ROM 00365: 321fc0
    RST $28                        ; ROM 00368: ef
    LD A,(HL)                      ; ROM 00369: 7e
    EXX                            ; ROM 0036A: d9
    LD BC,$4be                     ; ROM 0036B: 01be04
    LD H,A                         ; ROM 0036E: 67
    LD A,($c01f)                   ; ROM 0036F: 3a1fc0
    RRA                            ; ROM 00372: 1f
    LD D,H                         ; ROM 00373: 54
    JR c,$0378                     ; ROM 00374: 3802
    LD D,0                         ; ROM 00376: 1600
    OUT (C),D                      ; ROM 00378: ed51
    DJNZ $0372                     ; ROM 0037A: 10f6
    EXX                            ; ROM 0037C: d9
    INC HL                         ; ROM 0037D: 23
    DEC BC                         ; ROM 0037E: 0b
    LD A,B                         ; ROM 0037F: 78
    OR C                           ; ROM 00380: b1
    JR nz,$0369                    ; ROM 00381: 20e6
    RET                            ; ROM 00383: c9
    RST $28                        ; ROM 00384: ef
    LD A,C                         ; ROM 00385: 79
    OR A                           ; ROM 00386: b7
    JR z,$038a                     ; ROM 00387: 2801
    INC B                          ; ROM 00389: 04
    LD A,B                         ; ROM 0038A: 78
    LD B,C                         ; ROM 0038B: 41
    LD C,$be                       ; ROM 0038C: 0ebe
    OUTI                           ; ROM 0038E: eda3
    NOP                            ; ROM 00390: 00
    JR nz,$038e                    ; ROM 00391: 20fb
    DEC A                          ; ROM 00393: 3d
    JR nz,$038e                    ; ROM 00394: 20f8
    RET                            ; ROM 00396: c9
    RST $28                        ; ROM 00397: ef
    LD A,C                         ; ROM 00398: 79
    OR A                           ; ROM 00399: b7
    JR z,$039d                     ; ROM 0039A: 2801
    INC B                          ; ROM 0039C: 04
    LD A,L                         ; ROM 0039D: 7d
    OUT ($00be),A                  ; ROM 0039E: d3be
    PUSH AF                        ; ROM 003A0: f5
    POP AF                         ; ROM 003A1: f1
    LD A,H                         ; ROM 003A2: 7c
    OUT ($00be),A                  ; ROM 003A3: d3be
    DEC C                          ; ROM 003A5: 0d
    JR nz,$039d                    ; ROM 003A6: 20f5
    DJNZ $039d                     ; ROM 003A8: 10f3
    RET                            ; ROM 003AA: c9
    PUSH BC                        ; ROM 003AB: c5
    RST $28                        ; ROM 003AC: ef
    LD B,C                         ; ROM 003AD: 41
    LD C,$be                       ; ROM 003AE: 0ebe
    OUTI                           ; ROM 003B0: eda3
    NOP                            ; ROM 003B2: 00
    JR nz,$03b0                    ; ROM 003B3: 20fb
    LD A,$40                       ; ROM 003B5: 3e40
    ADD A,E                        ; ROM 003B7: 83
    LD E,A                         ; ROM 003B8: 5f
    JR nc,$03bc                    ; ROM 003B9: 3001
    INC D                          ; ROM 003BB: 14
    POP BC                         ; ROM 003BC: c1
    DJNZ $03ab                     ; ROM 003BD: 10ec
    RET                            ; ROM 003BF: c9
    LD HL,$3df                     ; ROM 003C0: 21df03
    LD DE,$c010                    ; ROM 003C3: 1110c0
    LD BC,$b80                     ; ROM 003C6: 01800b
    LD A,(HL)                      ; ROM 003C9: 7e
    LD (DE),A                      ; ROM 003CA: 12
    OUT ($00bf),A                  ; ROM 003CB: d3bf
    LD A,C                         ; ROM 003CD: 79
    OUT ($00bf),A                  ; ROM 003CE: d3bf
    INC HL                         ; ROM 003D0: 23
    INC DE                         ; ROM 003D1: 13
    INC C                          ; ROM 003D2: 0c
    DJNZ $03c9                     ; ROM 003D3: 10f4
    LD DE,$c010                    ; ROM 003D5: 1110c0
    XOR A                          ; ROM 003D8: af
    PUSH AF                        ; ROM 003D9: f5
    RST $28                        ; ROM 003DA: ef
    POP AF                         ; ROM 003DB: f1
    OUT ($00be),A                  ; ROM 003DC: d3be
    RET                            ; ROM 003DE: c9
    db $06,$A0,$FF,$FF,$FF,$FF,$FF,$00,$00,$00,$00,$47,$6F,$6C,$64,$65 ; ROM 003DF
    db $6E,$20,$41,$78,$65,$20,$57,$61,$72,$72,$69,$6F,$72,$20,$56,$65 ; ROM 003EF
    db $72,$20,$31,$2E,$30 ; ROM 003FF
    CALL $0444                     ; ROM 00404: cd4404
    LD HL,$3ea                     ; ROM 00407: 21ea03
    LD DE,$8010                    ; ROM 0040A: 111080
    LD B,$1a                       ; ROM 0040D: 061a
    LD A,(DE)                      ; ROM 0040F: 1a
    CP (HL)                        ; ROM 00410: be
    JR nz,$041f                    ; ROM 00411: 200c
    INC HL                         ; ROM 00413: 23
    INC DE                         ; ROM 00414: 13
    DJNZ $040f                     ; ROM 00415: 10f8
    LD A,($8030)                   ; ROM 00417: 3a3080
    LD ($c036),A                   ; ROM 0041A: 3236c0
    JR $043a                       ; ROM 0041D: 181b
    XOR A                          ; ROM 0041F: af
    LD HL,$8010                    ; ROM 00420: 211080
    LD DE,$8011                    ; ROM 00423: 111180
    LD BC,$1fee                    ; ROM 00426: 01ee1f
    LD (HL),A                      ; ROM 00429: 77
    LDIR                           ; ROM 0042A: edb0
    LD HL,$3ea                     ; ROM 0042C: 21ea03
    LD DE,$8010                    ; ROM 0042F: 111080
    LD BC,$1a                      ; ROM 00432: 011a00
    LDIR                           ; ROM 00435: edb0
    LD ($8030),A                   ; ROM 00437: 323080
    LD A,($fffc)                   ; ROM 0043A: 3afcff
    AND $f7                        ; ROM 0043D: e6f7
    LD ($fffc),A                   ; ROM 0043F: 32fcff
    EI                             ; ROM 00442: fb
    RET                            ; ROM 00443: c9
    DI                             ; ROM 00444: f3
    LD A,($fffc)                   ; ROM 00445: 3afcff
    OR 8                           ; ROM 00448: f608
    LD ($fffc),A                   ; ROM 0044A: 32fcff
    RET                            ; ROM 0044D: c9
    ADD A,$40                      ; ROM 0044E: c640
    LD H,$80                       ; ROM 00450: 2680
    LD L,A                         ; ROM 00452: 6f
    LD A,2                         ; ROM 00453: 3e02
    LD ($ffff),A                   ; ROM 00455: 32ffff
    LD A,(HL)                      ; ROM 00458: 7e
    LD HL,0                        ; ROM 00459: 210000
    LD D,H                         ; ROM 0045C: 54
    ADD A,A                        ; ROM 0045D: 87
    JR nc,$0461                    ; ROM 0045E: 3001
    DEC D                          ; ROM 00460: 15
    LD E,A                         ; ROM 00461: 5f
    LD A,C                         ; ROM 00462: 79
    RLCA                           ; ROM 00463: 07
    JR nc,$0468                    ; ROM 00464: 3002
    ADD HL,DE                      ; ROM 00466: 19
    ADD HL,HL                      ; ROM 00467: 29
    RLCA                           ; ROM 00468: 07
    JR nc,$046c                    ; ROM 00469: 3001
    ADD HL,DE                      ; ROM 0046B: 19
    ADD HL,HL                      ; ROM 0046C: 29
    RLCA                           ; ROM 0046D: 07
    JR nc,$0471                    ; ROM 0046E: 3001
    ADD HL,DE                      ; ROM 00470: 19
    ADD HL,HL                      ; ROM 00471: 29
    RLCA                           ; ROM 00472: 07
    JR nc,$0476                    ; ROM 00473: 3001
    ADD HL,DE                      ; ROM 00475: 19
    ADD HL,HL                      ; ROM 00476: 29
    RLCA                           ; ROM 00477: 07
    JR nc,$047b                    ; ROM 00478: 3001
    ADD HL,DE                      ; ROM 0047A: 19
    ADD HL,HL                      ; ROM 0047B: 29
    RLCA                           ; ROM 0047C: 07
    JR nc,$0480                    ; ROM 0047D: 3001
    ADD HL,DE                      ; ROM 0047F: 19
    ADD HL,HL                      ; ROM 00480: 29
    RLCA                           ; ROM 00481: 07
    JR nc,$0485                    ; ROM 00482: 3001
    ADD HL,DE                      ; ROM 00484: 19
    ADD HL,HL                      ; ROM 00485: 29
    RLCA                           ; ROM 00486: 07
    JR nc,$048a                    ; ROM 00487: 3001
    ADD HL,DE                      ; ROM 00489: 19
    RET                            ; ROM 0048A: c9
    db $C6,$40,$26,$80,$6F,$3E,$02,$32,$FF,$FF,$7E,$C9 ; ROM 0048B
    LD D,0                         ; ROM 00497: 1600
    LD HL,0                        ; ROM 00499: 210000
    RLCA                           ; ROM 0049C: 07
    JR nc,$04a1                    ; ROM 0049D: 3002
    ADD HL,DE                      ; ROM 0049F: 19
    ADD HL,HL                      ; ROM 004A0: 29
    RLCA                           ; ROM 004A1: 07
    JR nc,$04a5                    ; ROM 004A2: 3001
    ADD HL,DE                      ; ROM 004A4: 19
    ADD HL,HL                      ; ROM 004A5: 29
    RLCA                           ; ROM 004A6: 07
    JR nc,$04aa                    ; ROM 004A7: 3001
    ADD HL,DE                      ; ROM 004A9: 19
    ADD HL,HL                      ; ROM 004AA: 29
    RLCA                           ; ROM 004AB: 07
    JR nc,$04af                    ; ROM 004AC: 3001
    ADD HL,DE                      ; ROM 004AE: 19
    ADD HL,HL                      ; ROM 004AF: 29
    RLCA                           ; ROM 004B0: 07
    JR nc,$04b4                    ; ROM 004B1: 3001
    ADD HL,DE                      ; ROM 004B3: 19
    ADD HL,HL                      ; ROM 004B4: 29
    RLCA                           ; ROM 004B5: 07
    JR nc,$04b9                    ; ROM 004B6: 3001
    ADD HL,DE                      ; ROM 004B8: 19
    ADD HL,HL                      ; ROM 004B9: 29
    RLCA                           ; ROM 004BA: 07
    JR nc,$04be                    ; ROM 004BB: 3001
    ADD HL,DE                      ; ROM 004BD: 19
    ADD HL,HL                      ; ROM 004BE: 29
    RLCA                           ; ROM 004BF: 07
    JR nc,$04c3                    ; ROM 004C0: 3001
    ADD HL,DE                      ; ROM 004C2: 19
    RET                            ; ROM 004C3: c9
    db $AF,$06,$10,$29,$8F,$38,$03,$B9,$38,$02,$91,$B7,$3F,$ED,$6A,$10 ; ROM 004C4
    db $F3,$C9,$B7,$ED,$52,$E0,$7C,$1F,$EE,$40,$37,$8F,$C9 ; ROM 004D4
    LD HL,($c028)                  ; ROM 004E1: 2a28c0
    LD A,H                         ; ROM 004E4: 7c
    RRCA                           ; ROM 004E5: 0f
    RRCA                           ; ROM 004E6: 0f
    XOR H                          ; ROM 004E7: ac
    RRCA                           ; ROM 004E8: 0f
    XOR L                          ; ROM 004E9: ad
    RRCA                           ; ROM 004EA: 0f
    RRCA                           ; ROM 004EB: 0f
    RRCA                           ; ROM 004EC: 0f
    RRCA                           ; ROM 004ED: 0f
    XOR L                          ; ROM 004EE: ad
    RRA                            ; ROM 004EF: 1f
    ADC HL,HL                      ; ROM 004F0: ed6a
    JR nz,$04f7                    ; ROM 004F2: 2003
    LD HL,$733c                    ; ROM 004F4: 213c73
    LD A,R                         ; ROM 004F7: ed5f
    XOR L                          ; ROM 004F9: ad
    LD ($c028),HL                  ; ROM 004FA: 2228c0
    RET                            ; ROM 004FD: c9
    db $D5,$7B,$92,$5F,$1C,$CD,$E1,$04,$CD,$97,$04,$F1,$84,$C9,$CD,$C6 ; ROM 004FE
    db $0B,$E5,$11,$00,$38,$EF,$21,$00,$D6,$01,$00,$06,$DB,$BE,$77,$23 ; ROM 0050E
    db $0B,$78,$B1,$20,$F7,$E1 ; ROM 0051E
    LD A,3                         ; ROM 00524: 3e03
    LD ($ffff),A                   ; ROM 00526: 32ffff
    LD ($dcc0),HL                  ; ROM 00529: 22c0dc
    LD ($dcc4),HL                  ; ROM 0052C: 22c4dc
    LD HL,$dce0                    ; ROM 0052F: 21e0dc
    LD ($dcc2),HL                  ; ROM 00532: 22c2dc
    LD HL,0                        ; ROM 00535: 210000
    LD ($dcc8),HL                  ; ROM 00538: 22c8dc
    LD ($dcca),HL                  ; ROM 0053B: 22cadc
    XOR A                          ; ROM 0053E: af
    LD ($dccd),A                   ; ROM 0053F: 32cddc
    LD A,$ff                       ; ROM 00542: 3eff
    LD ($dcc6),A                   ; ROM 00544: 32c6dc
    LD HL,$d100                    ; ROM 00547: 2100d1
    LD DE,$d101                    ; ROM 0054A: 1101d1
    LD BC,$40f                     ; ROM 0054D: 010f04
    LD (HL),0                      ; ROM 00550: 3600
    LDIR                           ; ROM 00552: edb0
    LD DE,$d944                    ; ROM 00554: 1144d9
    LD BC,$1c07                    ; ROM 00557: 01071c
    CALL $0877                     ; ROM 0055A: cd7708
    LD HL,$d986                    ; ROM 0055D: 2186d9
    LD DE,$1900                    ; ROM 00560: 110019
    LD C,$1a                       ; ROM 00563: 0e1a
    LD B,5                         ; ROM 00565: 0605
    LD (HL),E                      ; ROM 00567: 73
    INC HL                         ; ROM 00568: 23
    LD (HL),D                      ; ROM 00569: 72
    LD A,$3f                       ; ROM 0056A: 3e3f
    ADD A,L                        ; ROM 0056C: 85
    LD L,A                         ; ROM 0056D: 6f
    JR nc,$0571                    ; ROM 0056E: 3001
    INC H                          ; ROM 00570: 24
    INC DE                         ; ROM 00571: 13
    DJNZ $0567                     ; ROM 00572: 10f3
    PUSH DE                        ; ROM 00574: d5
    LD DE,$fec2                    ; ROM 00575: 11c2fe
    ADD HL,DE                      ; ROM 00578: 19
    POP DE                         ; ROM 00579: d1
    DEC C                          ; ROM 0057A: 0d
    JR nz,$0565                    ; ROM 0057B: 20e8
    LD DE,$6000                    ; ROM 0057D: 110060
    RST $28                        ; ROM 00580: ef
    LD D,$82                       ; ROM 00581: 1682
    LD E,8                         ; ROM 00583: 1e08
    LD A,$ff                       ; ROM 00585: 3eff
    LD B,4                         ; ROM 00587: 0604
    OUT ($00be),A                  ; ROM 00589: d3be
    LD A,0                         ; ROM 0058B: 3e00
    DJNZ $0589                     ; ROM 0058D: 10fa
    DEC E                          ; ROM 0058F: 1d
    JR nz,$0585                    ; ROM 00590: 20f3
    DEC D                          ; ROM 00592: 15
    JR nz,$0583                    ; ROM 00593: 20ee
    CALL $0bc6                     ; ROM 00595: cdc60b
    CALL $0914                     ; ROM 00598: cd1409
    LD HL,($dcc8)                  ; ROM 0059B: 2ac8dc
    LD ($dcca),HL                  ; ROM 0059E: 22cadc
    LD HL,($dcc0)                  ; ROM 005A1: 2ac0dc
    LD A,(HL)                      ; ROM 005A4: 7e
    INC HL                         ; ROM 005A5: 23
    LD ($dcc0),HL                  ; ROM 005A6: 22c0dc
    CP $b0                         ; ROM 005A9: feb0
    JR nz,$05af                    ; ROM 005AB: 2002
    LD A,$2d                       ; ROM 005AD: 3e2d
    LD ($dcc7),A                   ; ROM 005AF: 32c7dc
    OR A                           ; ROM 005B2: b7
    JP z,$06d6                     ; ROM 005B3: cad606
    CP $ff                         ; ROM 005B6: feff
    JP z,$0677                     ; ROM 005B8: ca7706
    CP $20                         ; ROM 005BB: fe20
    JP z,$066b                     ; ROM 005BD: ca6b06
    CP $5c                         ; ROM 005C0: fe5c
    JR z,$0631                     ; ROM 005C2: 286d
    CP $25                         ; ROM 005C4: fe25
    JP z,$06e4                     ; ROM 005C6: cae406
    CP $23                         ; ROM 005C9: fe23
    JP z,$0709                     ; ROM 005CB: ca0907
    CP $24                         ; ROM 005CE: fe24
    JP z,$076b                     ; ROM 005D0: ca6b07
    LD DE,($dcca)                  ; ROM 005D3: ed5bcadc
    LD HL,$8994                    ; ROM 005D7: 219489
    LD BC,$bf                      ; ROM 005DA: 01bf00
    CPDR                           ; ROM 005DD: edb9
    LD A,($dcc6)                   ; ROM 005DF: 3ac6dc
    RRCA                           ; ROM 005E2: 0f
    JR nc,$05f1                    ; ROM 005E3: 300c
    LD A,C                         ; ROM 005E5: 79
    CP $88                         ; ROM 005E6: fe88
    JR c,$05f1                     ; ROM 005E8: 3807
    CP $bf                         ; ROM 005EA: febf
    JR nc,$05f1                    ; ROM 005EC: 3003
    SUB $37                        ; ROM 005EE: d637
    LD C,A                         ; ROM 005F0: 4f
    LD HL,$8995                    ; ROM 005F1: 219589
    ADD HL,BC                      ; ROM 005F4: 09
    LD A,($dccb)                   ; ROM 005F5: 3acbdc
    ADD A,(HL)                     ; ROM 005F8: 86
    INC A                          ; ROM 005F9: 3c
    LD ($dccb),A                   ; ROM 005FA: 32cbdc
    CP $d0                         ; ROM 005FD: fed0
    JR nc,$063c                    ; ROM 005FF: 303b
    LD L,C                         ; ROM 00601: 69
    LD H,B                         ; ROM 00602: 60
    ADD HL,HL                      ; ROM 00603: 29
    ADD HL,HL                      ; ROM 00604: 29
    ADD HL,HL                      ; ROM 00605: 29
    ADD HL,BC                      ; ROM 00606: 09
    ADD HL,BC                      ; ROM 00607: 09
    LD BC,$8000                    ; ROM 00608: 010080
    ADD HL,BC                      ; ROM 0060B: 09
    LD C,10                        ; ROM 0060C: 0e0a
    LD A,(HL)                      ; ROM 0060E: 7e
    LD B,8                         ; ROM 0060F: 0608
    RLCA                           ; ROM 00611: 07
    CALL c,$07b4                   ; ROM 00612: dcb407
    INC D                          ; ROM 00615: 14
    DJNZ $0611                     ; ROM 00616: 10f9
    LD A,D                         ; ROM 00618: 7a
    SUB 8                          ; ROM 00619: d608
    LD D,A                         ; ROM 0061B: 57
    INC E                          ; ROM 0061C: 1c
    DEC C                          ; ROM 0061D: 0d
    INC HL                         ; ROM 0061E: 23
    JR nz,$060e                    ; ROM 0061F: 20ed
    LD A,($dcc7)                   ; ROM 00621: 3ac7dc
    LD HL,$8a54                    ; ROM 00624: 21548a
    LD BC,10                       ; ROM 00627: 010a00
    CPIR                           ; ROM 0062A: edb1
    JR z,$0666                     ; ROM 0062C: 2838
    JP $05a1                       ; ROM 0062E: c3a105
    LD A,($dcc6)                   ; ROM 00631: 3ac6dc
    XOR 1                          ; ROM 00634: ee01
    LD ($dcc6),A                   ; ROM 00636: 32c6dc
    JP $05a1                       ; ROM 00639: c3a105
    LD A,$ff                       ; ROM 0063C: 3eff
    LD ($dcc7),A                   ; ROM 0063E: 32c7dc
    LD A,($dcc6)                   ; ROM 00641: 3ac6dc
    RRCA                           ; ROM 00644: 0f
    LD ($dcc6),A                   ; ROM 00645: 32c6dc
    LD HL,($dcc4)                  ; ROM 00648: 2ac4dc
    LD ($dcc0),HL                  ; ROM 0064B: 22c0dc
    LD DE,($dcc8)                  ; ROM 0064E: ed5bc8dc
    LD B,10                        ; ROM 00652: 060a
    CALL $07c0                     ; ROM 00654: cdc007
    INC D                          ; ROM 00657: 14
    LD A,D                         ; ROM 00658: 7a
    CP $d0                         ; ROM 00659: fed0
    JR c,$0654                     ; ROM 0065B: 38f7
    LD A,($dcc9)                   ; ROM 0065D: 3ac9dc
    LD D,A                         ; ROM 00660: 57
    INC E                          ; ROM 00661: 1c
    DJNZ $0654                     ; ROM 00662: 10f0
    JR $0677                       ; ROM 00664: 1811
    LD HL,($dcca)                  ; ROM 00666: 2acadc
    JR $0672                       ; ROM 00669: 1807
    LD HL,($dcca)                  ; ROM 0066B: 2acadc
    LD A,H                         ; ROM 0066E: 7c
    ADD A,6                        ; ROM 0066F: c606
    LD H,A                         ; ROM 00671: 67
    LD ($dcc8),HL                  ; ROM 00672: 22c8dc
    JR $06c4                       ; ROM 00675: 184d
    LD HL,$dccd                    ; ROM 00677: 21cddc
    INC (HL)                       ; ROM 0067A: 34
    LD A,($dcc8)                   ; ROM 0067B: 3ac8dc
    ADD A,10                       ; ROM 0067E: c60a
    CP $28                         ; ROM 00680: fe28
    JR c,$06bd                     ; ROM 00682: 3839
    LD A,(HL)                      ; ROM 00684: 7e
    AND 3                          ; ROM 00685: e603
    CALL z,$07ee                   ; ROM 00687: ccee07
    LD HL,$6b8                     ; ROM 0068A: 21b806
    LD A,(HL)                      ; ROM 0068D: 7e
    INC HL                         ; ROM 0068E: 23
    OR A                           ; ROM 0068F: b7
    JR z,$06c0                     ; ROM 00690: 282e
    PUSH HL                        ; ROM 00692: e5
    LD L,A                         ; ROM 00693: 6f
    LD H,0                         ; ROM 00694: 2600
    LD DE,$d100                    ; ROM 00696: 1100d1
    ADD HL,DE                      ; ROM 00699: 19
    LD BC,$410                     ; ROM 0069A: 011004
    LDIR                           ; ROM 0069D: edb0
    LD HL,$d127                    ; ROM 0069F: 2127d1
    LD DE,$28                      ; ROM 006A2: 112800
    LD B,$1a                       ; ROM 006A5: 061a
    LD (HL),C                      ; ROM 006A7: 71
    ADD HL,DE                      ; ROM 006A8: 19
    DJNZ $06a7                     ; ROM 006A9: 10fc
    LD DE,$fbef                    ; ROM 006AB: 11effb
    ADD HL,DE                      ; ROM 006AE: 19
    DEC A                          ; ROM 006AF: 3d
    JR nz,$06a2                    ; ROM 006B0: 20f0
    CALL $0786                     ; ROM 006B2: cd8607
    POP HL                         ; ROM 006B5: e1
    JR $068d                       ; ROM 006B6: 18d5
    db $02,$03,$03,$02,$00 ; ROM 006B8
    LD ($dcc8),A                   ; ROM 006BD: 32c8dc
    XOR A                          ; ROM 006C0: af
    LD ($dcc9),A                   ; ROM 006C1: 32c9dc
    LD A,($dcc6)                   ; ROM 006C4: 3ac6dc
    LD C,A                         ; ROM 006C7: 4f
    AND 1                          ; ROM 006C8: e601
    SLA C                          ; ROM 006CA: cb21
    OR C                           ; ROM 006CC: b1
    LD ($dcc6),A                   ; ROM 006CD: 32c6dc
    LD HL,($dcc0)                  ; ROM 006D0: 2ac0dc
    LD ($dcc4),HL                  ; ROM 006D3: 22c4dc
    CALL $0786                     ; ROM 006D6: cd8607
    LD A,($dcc7)                   ; ROM 006D9: 3ac7dc
    OR A                           ; ROM 006DC: b7
    JP nz,$059b                    ; ROM 006DD: c29b05
    LD HL,($dcc0)                  ; ROM 006E0: 2ac0dc
    RET                            ; ROM 006E3: c9
    LD HL,($dcca)                  ; ROM 006E4: 2acadc
    LD ($dcc8),HL                  ; ROM 006E7: 22c8dc
    LD HL,($dcc0)                  ; ROM 006EA: 2ac0dc
    LD DE,($dcc6)                  ; ROM 006ED: ed5bc6dc
    PUSH HL                        ; ROM 006F1: e5
    PUSH DE                        ; ROM 006F2: d5
    LD A,E                         ; ROM 006F3: 7b
    OR 1                           ; ROM 006F4: f601
    LD ($dcc6),A                   ; ROM 006F6: 32c6dc
    LD HL,($dcc2)                  ; ROM 006F9: 2ac2dc
    LD E,(HL)                      ; ROM 006FC: 5e
    INC HL                         ; ROM 006FD: 23
    LD D,(HL)                      ; ROM 006FE: 56
    INC HL                         ; ROM 006FF: 23
    LD ($dcc2),HL                  ; ROM 00700: 22c2dc
    LD ($dcc0),DE                  ; ROM 00703: ed53c0dc
    JR $0756                       ; ROM 00707: 184d
    LD HL,($dcca)                  ; ROM 00709: 2acadc
    LD ($dcc8),HL                  ; ROM 0070C: 22c8dc
    LD HL,($dcc0)                  ; ROM 0070F: 2ac0dc
    LD DE,($dcc6)                  ; ROM 00712: ed5bc6dc
    PUSH HL                        ; ROM 00716: e5
    PUSH DE                        ; ROM 00717: d5
    LD HL,($dcc2)                  ; ROM 00718: 2ac2dc
    LD E,(HL)                      ; ROM 0071B: 5e
    INC HL                         ; ROM 0071C: 23
    LD D,(HL)                      ; ROM 0071D: 56
    INC HL                         ; ROM 0071E: 23
    LD ($dcc2),HL                  ; ROM 0071F: 22c2dc
    LD HL,$d510                    ; ROM 00722: 2110d5
    LD ($dcc0),HL                  ; ROM 00725: 22c0dc
    EX DE,HL                       ; ROM 00728: eb
    LD A,(HL)                      ; ROM 00729: 7e
    INC HL                         ; ROM 0072A: 23
    LD H,(HL)                      ; ROM 0072B: 66
    LD L,A                         ; ROM 0072C: 6f
    LD IX,$d510                    ; ROM 0072D: dd2110d5
    LD C,0                         ; ROM 00731: 0e00
    LD DE,$d8f0                    ; ROM 00733: 11f0d8
    CALL $0771                     ; ROM 00736: cd7107
    LD DE,$fc18                    ; ROM 00739: 1118fc
    CALL $0771                     ; ROM 0073C: cd7107
    LD DE,$ff9c                    ; ROM 0073F: 119cff
    CALL $0771                     ; ROM 00742: cd7107
    LD DE,$fff6                    ; ROM 00745: 11f6ff
    CALL $0771                     ; ROM 00748: cd7107
    LD DE,$ffff                    ; ROM 0074B: 11ffff
    LD C,E                         ; ROM 0074E: 4b
    CALL $0771                     ; ROM 0074F: cd7107
    LD (IX),0                      ; ROM 00752: dd360000
    CALL $059b                     ; ROM 00756: cd9b05
    POP DE                         ; ROM 00759: d1
    POP HL                         ; ROM 0075A: e1
    LD ($dcc0),HL                  ; ROM 0075B: 22c0dc
    LD ($dcc6),DE                  ; ROM 0075E: ed53c6dc
    LD HL,($dcca)                  ; ROM 00762: 2acadc
    LD ($dcc8),HL                  ; ROM 00765: 22c8dc
    JP $06d9                       ; ROM 00768: c3d906
    CALL $07ee                     ; ROM 0076B: cdee07
    JP $05a1                       ; ROM 0076E: c3a105
    LD A,$30                       ; ROM 00771: 3e30
    ADD HL,DE                      ; ROM 00773: 19
    JR nc,$077b                    ; ROM 00774: 3005
    INC A                          ; ROM 00776: 3c
    SET 0,C                        ; ROM 00777: cbc1
    JR $0773                       ; ROM 00779: 18f8
    SBC HL,DE                      ; ROM 0077B: ed52
    BIT 0,C                        ; ROM 0077D: cb41
    RET z                          ; ROM 0077F: c8
    LD (IX),A                      ; ROM 00780: dd7700
    INC IX                         ; ROM 00783: dd23
    RET                            ; ROM 00785: c9
    LD A,$9f                       ; ROM 00786: 3e9f
    LD ($de08),A                   ; ROM 00788: 3208de
    CALL $0bc6                     ; ROM 0078B: cdc60b
    LD HL,$6001                    ; ROM 0078E: 210160
    LD DE,4                        ; ROM 00791: 110400
    LD C,$bf                       ; ROM 00794: 0ebf
    EXX                            ; ROM 00796: d9
    LD HL,$d100                    ; ROM 00797: 2100d1
    LD C,$be                       ; ROM 0079A: 0ebe
    DI                             ; ROM 0079C: f3
    LD A,$82                       ; ROM 0079D: 3e82
    LD B,$10                       ; ROM 0079F: 0610
    EXX                            ; ROM 007A1: d9
    OUT (C),L                      ; ROM 007A2: ed69
    OUT (C),H                      ; ROM 007A4: ed61
    ADD HL,DE                      ; ROM 007A6: 19
    EXX                            ; ROM 007A7: d9
    NOP                            ; ROM 007A8: 00
    OUTI                           ; ROM 007A9: eda3
    NOP                            ; ROM 007AB: 00
    DJNZ $07a1                     ; ROM 007AC: 10f3
    DEC A                          ; ROM 007AE: 3d
    JP nz,$079f                    ; ROM 007AF: c29f07
    EI                             ; ROM 007B2: fb
    RET                            ; ROM 007B3: c9
    PUSH AF                        ; ROM 007B4: f5
    PUSH BC                        ; ROM 007B5: c5
    PUSH HL                        ; ROM 007B6: e5
    CALL $07cd                     ; ROM 007B7: cdcd07
    OR (HL)                        ; ROM 007BA: b6
    LD (HL),A                      ; ROM 007BB: 77
    POP HL                         ; ROM 007BC: e1
    POP BC                         ; ROM 007BD: c1
    POP AF                         ; ROM 007BE: f1
    RET                            ; ROM 007BF: c9
    PUSH AF                        ; ROM 007C0: f5
    PUSH BC                        ; ROM 007C1: c5
    PUSH HL                        ; ROM 007C2: e5
    CALL $07cd                     ; ROM 007C3: cdcd07
    CPL                            ; ROM 007C6: 2f
    AND (HL)                       ; ROM 007C7: a6
    LD (HL),A                      ; ROM 007C8: 77
    POP HL                         ; ROM 007C9: e1
    POP BC                         ; ROM 007CA: c1
    POP AF                         ; ROM 007CB: f1
    RET                            ; ROM 007CC: c9
    LD A,D                         ; ROM 007CD: 7a
    AND $f8                        ; ROM 007CE: e6f8
    LD L,A                         ; ROM 007D0: 6f
    LD H,0                         ; ROM 007D1: 2600
    ADD HL,HL                      ; ROM 007D3: 29
    ADD HL,HL                      ; ROM 007D4: 29
    ADD A,L                        ; ROM 007D5: 85
    LD L,A                         ; ROM 007D6: 6f
    JR nc,$07da                    ; ROM 007D7: 3001
    INC H                          ; ROM 007D9: 24
    LD A,E                         ; ROM 007DA: 7b
    ADD A,L                        ; ROM 007DB: 85
    LD L,A                         ; ROM 007DC: 6f
    JR nc,$07e0                    ; ROM 007DD: 3001
    INC H                          ; ROM 007DF: 24
    LD BC,$45                      ; ROM 007E0: 014500
    LD A,D                         ; ROM 007E3: 7a
    AND 7                          ; ROM 007E4: e607
    ADD A,C                        ; ROM 007E6: 81
    LD C,A                         ; ROM 007E7: 4f
    LD A,(BC)                      ; ROM 007E8: 0a
    LD BC,$d100                    ; ROM 007E9: 0100d1
    ADD HL,BC                      ; ROM 007EC: 09
    RET                            ; ROM 007ED: c9
    CALL $0786                     ; ROM 007EE: cd8607
    LD HL,$c02f                    ; ROM 007F1: 212fc0
    LD (HL),0                      ; ROM 007F4: 3600
    CALL $0bc6                     ; ROM 007F6: cdc60b
    CALL $0805                     ; ROM 007F9: cd0508
    LD A,($c021)                   ; ROM 007FC: 3a21c0
    AND $30                        ; ROM 007FF: e630
    JR z,$07f6                     ; ROM 00801: 28f3
    LD (HL),$ff                    ; ROM 00803: 36ff
    LD DE,$7cde                    ; ROM 00805: 11de7c
    LD A,$fc                       ; ROM 00808: 3efc
    BIT 3,(HL)                     ; ROM 0080A: cb5e
    JR nz,$080f                    ; ROM 0080C: 2001
    INC A                          ; ROM 0080E: 3c
    JP $03d9                       ; ROM 0080F: c3d903
    LD IX,$8a8e                    ; ROM 00812: dd218e8a
    JR $081c                       ; ROM 00816: 1804
    LD IX,$8ae4                    ; ROM 00818: dd21e48a
    LD A,3                         ; ROM 0081C: 3e03
    LD ($ffff),A                   ; ROM 0081E: 32ffff
    LD ($dcc0),DE                  ; ROM 00821: ed53c0dc
    LD A,(HL)                      ; ROM 00825: 7e
    INC HL                         ; ROM 00826: 23
    OR A                           ; ROM 00827: b7
    RET z                          ; ROM 00828: c8
    CP $ff                         ; ROM 00829: feff
    JR nz,$083e                    ; ROM 0082B: 2011
    LD DE,($dcc0)                  ; ROM 0082D: ed5bc0dc
    LD A,$40                       ; ROM 00831: 3e40
    ADD A,E                        ; ROM 00833: 83
    LD E,A                         ; ROM 00834: 5f
    JR nc,$0838                    ; ROM 00835: 3001
    INC D                          ; ROM 00837: 14
    LD ($dcc0),DE                  ; ROM 00838: ed53c0dc
    JR $0825                       ; ROM 0083C: 18e7
    PUSH HL                        ; ROM 0083E: e5
    LD L,(IX)                      ; ROM 0083F: dd6e00
    LD H,(IX+1)                    ; ROM 00842: dd6601
    LD C,(IX+2)                    ; ROM 00845: dd4e02
    LD B,(IX+3)                    ; ROM 00848: dd4603
    CPDR                           ; ROM 0084B: edb9
    LD A,C                         ; ROM 0084D: 79
    ADD A,(IX+4)                   ; ROM 0084E: dd8604
    LD (DE),A                      ; ROM 00851: 12
    INC DE                         ; ROM 00852: 13
    LD A,(IX+5)                    ; ROM 00853: dd7e05
    LD (DE),A                      ; ROM 00856: 12
    INC DE                         ; ROM 00857: 13
    POP HL                         ; ROM 00858: e1
    JR $0825                       ; ROM 00859: 18ca
    LD C,$64                       ; ROM 0085B: 0e64
    CALL $086a                     ; ROM 0085D: cd6a08
    LD C,10                        ; ROM 00860: 0e0a
    CALL $086a                     ; ROM 00862: cd6a08
    ADD A,$f0                      ; ROM 00865: c6f0
    LD (HL),A                      ; ROM 00867: 77
    JR $0872                       ; ROM 00868: 1808
    LD B,$ef                       ; ROM 0086A: 06ef
    INC B                          ; ROM 0086C: 04
    SUB C                          ; ROM 0086D: 91
    JR nc,$086c                    ; ROM 0086E: 30fc
    ADD A,C                        ; ROM 00870: 81
    LD (HL),B                      ; ROM 00871: 70
    INC HL                         ; ROM 00872: 23
    LD (HL),$18                    ; ROM 00873: 3618
    INC HL                         ; ROM 00875: 23
    RET                            ; ROM 00876: c9
    PUSH IX                        ; ROM 00877: dde5
    LD IX,$902                     ; ROM 00879: dd210209
    PUSH AF                        ; ROM 0087D: f5
    PUSH BC                        ; ROM 0087E: c5
    PUSH DE                        ; ROM 0087F: d5
    PUSH HL                        ; ROM 00880: e5
    EX DE,HL                       ; ROM 00881: eb
    DEC B                          ; ROM 00882: 05
    DEC B                          ; ROM 00883: 05
    DEC C                          ; ROM 00884: 0d
    DEC C                          ; ROM 00885: 0d
    LD D,B                         ; ROM 00886: 50
    PUSH HL                        ; ROM 00887: e5
    LD A,(IX)                      ; ROM 00888: dd7e00
    LD (HL),A                      ; ROM 0088B: 77
    INC HL                         ; ROM 0088C: 23
    LD A,(IX+1)                    ; ROM 0088D: dd7e01
    LD (HL),A                      ; ROM 00890: 77
    INC HL                         ; ROM 00891: 23
    LD A,(IX+2)                    ; ROM 00892: dd7e02
    LD (HL),A                      ; ROM 00895: 77
    INC HL                         ; ROM 00896: 23
    LD A,(IX+3)                    ; ROM 00897: dd7e03
    LD (HL),A                      ; ROM 0089A: 77
    INC HL                         ; ROM 0089B: 23
    DJNZ $0892                     ; ROM 0089C: 10f4
    LD A,(IX+4)                    ; ROM 0089E: dd7e04
    LD (HL),A                      ; ROM 008A1: 77
    INC HL                         ; ROM 008A2: 23
    LD A,(IX+5)                    ; ROM 008A3: dd7e05
    LD (HL),A                      ; ROM 008A6: 77
    POP HL                         ; ROM 008A7: e1
    LD A,$40                       ; ROM 008A8: 3e40
    ADD A,L                        ; ROM 008AA: 85
    LD L,A                         ; ROM 008AB: 6f
    JR nc,$08af                    ; ROM 008AC: 3001
    INC H                          ; ROM 008AE: 24
    PUSH HL                        ; ROM 008AF: e5
    LD A,(IX+6)                    ; ROM 008B0: dd7e06
    LD (HL),A                      ; ROM 008B3: 77
    INC HL                         ; ROM 008B4: 23
    LD A,(IX+7)                    ; ROM 008B5: dd7e07
    LD (HL),A                      ; ROM 008B8: 77
    INC HL                         ; ROM 008B9: 23
    LD B,D                         ; ROM 008BA: 42
    LD A,(IX+8)                    ; ROM 008BB: dd7e08
    LD (HL),A                      ; ROM 008BE: 77
    INC HL                         ; ROM 008BF: 23
    LD A,(IX+9)                    ; ROM 008C0: dd7e09
    LD (HL),A                      ; ROM 008C3: 77
    INC HL                         ; ROM 008C4: 23
    DJNZ $08bb                     ; ROM 008C5: 10f4
    LD A,(IX+10)                   ; ROM 008C7: dd7e0a
    LD (HL),A                      ; ROM 008CA: 77
    INC HL                         ; ROM 008CB: 23
    LD A,(IX+11)                   ; ROM 008CC: dd7e0b
    LD (HL),A                      ; ROM 008CF: 77
    POP HL                         ; ROM 008D0: e1
    LD A,$40                       ; ROM 008D1: 3e40
    ADD A,L                        ; ROM 008D3: 85
    LD L,A                         ; ROM 008D4: 6f
    JR nc,$08d8                    ; ROM 008D5: 3001
    INC H                          ; ROM 008D7: 24
    DEC C                          ; ROM 008D8: 0d
    JR nz,$08af                    ; ROM 008D9: 20d4
    LD A,(IX+12)                   ; ROM 008DB: dd7e0c
    LD (HL),A                      ; ROM 008DE: 77
    INC HL                         ; ROM 008DF: 23
    LD A,(IX+13)                   ; ROM 008E0: dd7e0d
    LD (HL),A                      ; ROM 008E3: 77
    INC HL                         ; ROM 008E4: 23
    LD B,D                         ; ROM 008E5: 42
    LD A,(IX+14)                   ; ROM 008E6: dd7e0e
    LD (HL),A                      ; ROM 008E9: 77
    INC HL                         ; ROM 008EA: 23
    LD A,(IX+15)                   ; ROM 008EB: dd7e0f
    LD (HL),A                      ; ROM 008EE: 77
    INC HL                         ; ROM 008EF: 23
    DJNZ $08e6                     ; ROM 008F0: 10f4
    LD A,(IX+$10)                  ; ROM 008F2: dd7e10
    LD (HL),A                      ; ROM 008F5: 77
    INC HL                         ; ROM 008F6: 23
    LD A,(IX+$11)                  ; ROM 008F7: dd7e11
    LD (HL),A                      ; ROM 008FA: 77
    POP HL                         ; ROM 008FB: e1
    POP DE                         ; ROM 008FC: d1
    POP BC                         ; ROM 008FD: c1
    POP AF                         ; ROM 008FE: f1
    POP IX                         ; ROM 008FF: dde1
    RET                            ; ROM 00901: c9
    db $FA,$18,$FC,$1C,$FA,$1A,$FB,$18,$FF,$18,$FB,$1A,$FA,$1C,$FC,$18 ; ROM 00902
    db $FA,$1E ; ROM 00912
    PUSH AF                        ; ROM 00914: f5
    PUSH BC                        ; ROM 00915: c5
    PUSH DE                        ; ROM 00916: d5
    PUSH HL                        ; ROM 00917: e5
    DI                             ; ROM 00918: f3
    XOR A                          ; ROM 00919: af
    OUT ($00bf),A                  ; ROM 0091A: d3bf
    LD A,$78                       ; ROM 0091C: 3e78
    OUT ($00bf),A                  ; ROM 0091E: d3bf
    LD HL,$d600                    ; ROM 00920: 2100d6
    LD BC,$be                      ; ROM 00923: 01be00
    LD E,12                        ; ROM 00926: 1e0c
    OUTI                           ; ROM 00928: eda3
    DJNZ $0928                     ; ROM 0092A: 10fc
    DEC E                          ; ROM 0092C: 1d
    JP nz,$0928                    ; ROM 0092D: c22809
    IN A,($00bf)                   ; ROM 00930: dbbf
    EI                             ; ROM 00932: fb
    POP HL                         ; ROM 00933: e1
    POP DE                         ; ROM 00934: d1
    POP BC                         ; ROM 00935: c1
    POP AF                         ; ROM 00936: f1
    RET                            ; ROM 00937: c9
    LD A,($c303)                   ; ROM 00938: 3a03c3
    OR 1                           ; ROM 0093B: f601
    LD ($c303),A                   ; ROM 0093D: 3203c3
    CALL $0a60                     ; ROM 00940: cd600a
    LD A,($c047)                   ; ROM 00943: 3a47c0
    CP 8                           ; ROM 00946: fe08
    JR nc,$0951                    ; ROM 00948: 3007
    LD A,($c01b)                   ; ROM 0094A: 3a1bc0
    AND $40                        ; ROM 0094D: e640
    JR z,$097e                     ; ROM 0094F: 282d
    LD A,($c02f)                   ; ROM 00951: 3a2fc0
    AND 3                          ; ROM 00954: e603
    RRCA                           ; ROM 00956: 0f
    RRCA                           ; ROM 00957: 0f
    RRCA                           ; ROM 00958: 0f
    LD L,A                         ; ROM 00959: 6f
    LD H,$80                       ; ROM 0095A: 2680
    LD B,$20                       ; ROM 0095C: 0620
    LD E,(HL)                      ; ROM 0095E: 5e
    INC HL                         ; ROM 0095F: 23
    LD D,(HL)                      ; ROM 00960: 56
    INC HL                         ; ROM 00961: 23
    LD A,(DE)                      ; ROM 00962: 1a
    OR A                           ; ROM 00963: b7
    JR z,$0976                     ; ROM 00964: 2810
    PUSH DE                        ; ROM 00966: d5
    POP IX                         ; ROM 00967: dde1
    BIT 0,(IX+3)                   ; ROM 00969: ddcb0346
    JR z,$0976                     ; ROM 0096D: 2807
    PUSH HL                        ; ROM 0096F: e5
    PUSH BC                        ; ROM 00970: c5
    CALL $09ee                     ; ROM 00971: cdee09
    POP BC                         ; ROM 00974: c1
    POP HL                         ; ROM 00975: e1
    DJNZ $095e                     ; ROM 00976: 10e6
    LD HL,($c024)                  ; ROM 00978: 2a24c0
    LD (HL),$d0                    ; ROM 0097B: 36d0
    RET                            ; ROM 0097D: c9
    LD IX,$c8d0                    ; ROM 0097E: dd21d0c8
    LD IY,$d100                    ; ROM 00982: fd2100d1
    LD DE,$ffd0                    ; ROM 00986: 11d0ff
    LD HL,$1f                      ; ROM 00989: 211f00
    BIT 0,(IX+3)                   ; ROM 0098C: ddcb0346
    JR z,$09bf                     ; ROM 00990: 282d
    LD A,H                         ; ROM 00992: 7c
    OR A                           ; ROM 00993: b7
    LD A,(IX+$11)                  ; ROM 00994: dd7e11
    LD C,L                         ; ROM 00997: 4d
    JR z,$09b6                     ; ROM 00998: 281c
    LD IY,$d100                    ; ROM 0099A: fd2100d1
    LD B,H                         ; ROM 0099E: 44
    CP (IY+$40)                    ; ROM 0099F: fdbe40
    JR c,$09b2                     ; ROM 009A2: 380e
    LD E,(IY+$40)                  ; ROM 009A4: fd5e40
    LD (IY+$40),A                  ; ROM 009A7: fd7740
    LD A,E                         ; ROM 009AA: 7b
    LD E,(IY)                      ; ROM 009AB: fd5e00
    LD (IY),C                      ; ROM 009AE: fd7100
    LD C,E                         ; ROM 009B1: 4b
    INC IY                         ; ROM 009B2: fd23
    DJNZ $099f                     ; ROM 009B4: 10e9
    INC H                          ; ROM 009B6: 24
    LD (IY+$40),A                  ; ROM 009B7: fd7740
    LD (IY),C                      ; ROM 009BA: fd7100
    INC IY                         ; ROM 009BD: fd23
    LD E,$d0                       ; ROM 009BF: 1ed0
    ADD IX,DE                      ; ROM 009C1: dd19
    DEC L                          ; ROM 009C3: 2d
    JP p,$098c                     ; ROM 009C4: f28c09
    LD (IY),$ff                    ; ROM 009C7: fd3600ff
    LD IY,$d100                    ; ROM 009CB: fd2100d1
    LD A,(IY)                      ; ROM 009CF: fd7e00
    LD L,A                         ; ROM 009D2: 6f
    ADD A,A                        ; ROM 009D3: 87
    JP c,$0978                     ; ROM 009D4: da7809
    ADD A,L                        ; ROM 009D7: 85
    ADD A,A                        ; ROM 009D8: 87
    LD L,A                         ; ROM 009D9: 6f
    LD H,0                         ; ROM 009DA: 2600
    ADD HL,HL                      ; ROM 009DC: 29
    ADD HL,HL                      ; ROM 009DD: 29
    ADD HL,HL                      ; ROM 009DE: 29
    EX DE,HL                       ; ROM 009DF: eb
    LD IX,$c300                    ; ROM 009E0: dd2100c3
    ADD IX,DE                      ; ROM 009E4: dd19
    CALL $09ee                     ; ROM 009E6: cdee09
    INC IY                         ; ROM 009E9: fd23
    JP $09cf                       ; ROM 009EB: c3cf09
    LD H,(IX+9)                    ; ROM 009EE: dd6609
    LD A,(IX+10)                   ; ROM 009F1: dd7e0a
    ADD A,A                        ; ROM 009F4: 87
    ADD A,(IX+8)                   ; ROM 009F5: dd8608
    JR nc,$09fb                    ; ROM 009F8: 3001
    INC H                          ; ROM 009FA: 24
    LD L,A                         ; ROM 009FB: 6f
    LD A,(HL)                      ; ROM 009FC: 7e
    INC HL                         ; ROM 009FD: 23
    LD H,(HL)                      ; ROM 009FE: 66
    LD L,A                         ; ROM 009FF: 6f
    LD A,(IX+11)                   ; ROM 00A00: dd7e0b
    ADD A,A                        ; ROM 00A03: 87
    ADD A,L                        ; ROM 00A04: 85
    LD L,A                         ; ROM 00A05: 6f
    JR nc,$0a09                    ; ROM 00A06: 3001
    INC H                          ; ROM 00A08: 24
    LD A,(HL)                      ; ROM 00A09: 7e
    INC HL                         ; ROM 00A0A: 23
    LD H,(HL)                      ; ROM 00A0B: 66
    LD L,A                         ; ROM 00A0C: 6f
    LD A,(HL)                      ; ROM 00A0D: 7e
    LD C,A                         ; ROM 00A0E: 4f
    RES 7,C                        ; ROM 00A0F: cbb9
    EX AF,AF'                      ; ROM 00A11: 08
    INC HL                         ; ROM 00A12: 23
    LD A,(HL)                      ; ROM 00A13: 7e
    INC HL                         ; ROM 00A14: 23
    LD (IX+$1b),A                  ; ROM 00A15: dd771b
    LD A,(HL)                      ; ROM 00A18: 7e
    INC HL                         ; ROM 00A19: 23
    LD (IX+$1c),A                  ; ROM 00A1A: dd771c
    LD DE,($c024)                  ; ROM 00A1D: ed5b24c0
    LD A,(IX+$11)                  ; ROM 00A21: dd7e11
    LD B,C                         ; ROM 00A24: 41
    ADD A,(HL)                     ; ROM 00A25: 86
    LD (DE),A                      ; ROM 00A26: 12
    INC HL                         ; ROM 00A27: 23
    INC DE                         ; ROM 00A28: 13
    DJNZ $0a25                     ; ROM 00A29: 10fa
    LD ($c024),DE                  ; ROM 00A2B: ed5324c0
    LD DE,($c026)                  ; ROM 00A2F: ed5b26c0
    LD B,C                         ; ROM 00A33: 41
    EX AF,AF'                      ; ROM 00A34: 08
    RLCA                           ; ROM 00A35: 07
    JR c,$0a50                     ; ROM 00A36: 3818
    LD A,(IX+$13)                  ; ROM 00A38: dd7e13
    LD C,(IX+2)                    ; ROM 00A3B: dd4e02
    ADD A,(HL)                     ; ROM 00A3E: 86
    LD (DE),A                      ; ROM 00A3F: 12
    INC HL                         ; ROM 00A40: 23
    INC DE                         ; ROM 00A41: 13
    EX AF,AF'                      ; ROM 00A42: 08
    LD A,(HL)                      ; ROM 00A43: 7e
    ADD A,C                        ; ROM 00A44: 81
    LD (DE),A                      ; ROM 00A45: 12
    EX AF,AF'                      ; ROM 00A46: 08
    INC HL                         ; ROM 00A47: 23
    INC DE                         ; ROM 00A48: 13
    DJNZ $0a3e                     ; ROM 00A49: 10f3
    LD ($c026),DE                  ; ROM 00A4B: ed5326c0
    RET                            ; ROM 00A4F: c9
    LD A,(IX+$13)                  ; ROM 00A50: dd7e13
    ADD A,(HL)                     ; ROM 00A53: 86
    LD (DE),A                      ; ROM 00A54: 12
    INC HL                         ; ROM 00A55: 23
    INC DE                         ; ROM 00A56: 13
    LDI                            ; ROM 00A57: eda0
    DJNZ $0a53                     ; ROM 00A59: 10f8
    LD ($c026),DE                  ; ROM 00A5B: ed5326c0
    RET                            ; ROM 00A5F: c9
    LD HL,$dd40                    ; ROM 00A60: 2140dd
    LD ($c024),HL                  ; ROM 00A63: 2224c0
    LD HL,$dd80                    ; ROM 00A66: 2180dd
    LD ($c026),HL                  ; ROM 00A69: 2226c0
    LD A,12                        ; ROM 00A6C: 3e0c
    LD ($ffff),A                   ; ROM 00A6E: 32ffff
    RET                            ; ROM 00A71: c9
    db $DD,$6E,$08,$DD,$66,$09 ; ROM 00A72
    LD C,(HL)                      ; ROM 00A78: 4e
    INC HL                         ; ROM 00A79: 23
    LD DE,($c024)                  ; ROM 00A7A: ed5b24c0
    LD A,(IX+$11)                  ; ROM 00A7E: dd7e11
    LD B,C                         ; ROM 00A81: 41
    ADD A,(HL)                     ; ROM 00A82: 86
    LD (DE),A                      ; ROM 00A83: 12
    INC HL                         ; ROM 00A84: 23
    INC DE                         ; ROM 00A85: 13
    DJNZ $0a82                     ; ROM 00A86: 10fa
    LD A,$d0                       ; ROM 00A88: 3ed0
    LD (DE),A                      ; ROM 00A8A: 12
    LD ($c024),DE                  ; ROM 00A8B: ed5324c0
    LD DE,($c026)                  ; ROM 00A8F: ed5b26c0
    LD A,(IX+$13)                  ; ROM 00A93: dd7e13
    LD B,C                         ; ROM 00A96: 41
    ADD A,(HL)                     ; ROM 00A97: 86
    LD (DE),A                      ; ROM 00A98: 12
    INC HL                         ; ROM 00A99: 23
    INC DE                         ; ROM 00A9A: 13
    LDI                            ; ROM 00A9B: eda0
    DJNZ $0a97                     ; ROM 00A9D: 10f8
    LD ($c026),DE                  ; ROM 00A9F: ed5326c0
    RET                            ; ROM 00AA3: c9
    LD HL,$dca0                    ; ROM 00AA4: 21a0dc
    LD DE,$dcc0                    ; ROM 00AA7: 11c0dc
    LD BC,$20                      ; ROM 00AAA: 012000
    LDIR                           ; ROM 00AAD: edb0
    CALL $0b85                     ; ROM 00AAF: cd850b
    LD A,($c011)                   ; ROM 00AB2: 3a11c0
    LD E,A                         ; ROM 00AB5: 5f
    LD D,$81                       ; ROM 00AB6: 1681
    SET 5,E                        ; ROM 00AB8: cbeb
    RST $28                        ; ROM 00ABA: ef
    IN A,($00bf)                   ; ROM 00ABB: dbbf
    CALL $0b95                     ; ROM 00ABD: cd950b
    SET 6,E                        ; ROM 00AC0: cbf3
    RST $28                        ; ROM 00AC2: ef
    LD A,E                         ; ROM 00AC3: 7b
    LD ($c011),A                   ; ROM 00AC4: 3211c0
    LD A,($c010)                   ; ROM 00AC7: 3a10c0
    LD E,A                         ; ROM 00ACA: 5f
    LD D,$80                       ; ROM 00ACB: 1680
    RST $28                        ; ROM 00ACD: ef
    LD HL,$b0a                     ; ROM 00ACE: 210a0b
    LD A,(HL)                      ; ROM 00AD1: 7e
    ADD A,A                        ; ROM 00AD2: 87
    RET z                          ; ROM 00AD3: c8
    CALL $0ade                     ; ROM 00AD4: cdde0a
    JR z,$0ad1                     ; ROM 00AD7: 28f8
    CALL $0b92                     ; ROM 00AD9: cd920b
    JR $0ad1                       ; ROM 00ADC: 18f3
    OR (HL)                        ; ROM 00ADE: b6
    LD E,A                         ; ROM 00ADF: 5f
    LD IY,$dca0                    ; ROM 00AE0: fd21a0dc
    LD BC,$2000                    ; ROM 00AE4: 010020
    LD A,(IY+$20)                  ; ROM 00AE7: fd7e20
    AND E                          ; ROM 00AEA: a3
    LD D,A                         ; ROM 00AEB: 57
    LD A,(IY)                      ; ROM 00AEC: fd7e00
    AND E                          ; ROM 00AEF: a3
    CP D                           ; ROM 00AF0: ba
    LD A,(IY)                      ; ROM 00AF1: fd7e00
    JR z,$0b00                     ; ROM 00AF4: 280a
    JR c,$0afb                     ; ROM 00AF6: 3803
    SUB (HL)                       ; ROM 00AF8: 96
    JR $0afc                       ; ROM 00AF9: 1801
    ADD A,(HL)                     ; ROM 00AFB: 86
    INC C                          ; ROM 00AFC: 0c
    LD (IY),A                      ; ROM 00AFD: fd7700
    INC IY                         ; ROM 00B00: fd23
    DJNZ $0ae7                     ; ROM 00B02: 10e3
    LD A,C                         ; ROM 00B04: 79
    OR A                           ; ROM 00B05: b7
    JR nz,$0b09                    ; ROM 00B06: 2001
    INC HL                         ; ROM 00B08: 23
    RET                            ; ROM 00B09: c9
    db $10,$04,$01,$00,$01,$04,$10,$00 ; ROM 00B0A
    LD HL,$dcc0                    ; ROM 00B12: 21c0dc
    LD DE,$dcc1                    ; ROM 00B15: 11c1dc
    LD BC,$1f                      ; ROM 00B18: 011f00
    LD (HL),B                      ; ROM 00B1B: 70
    LDIR                           ; ROM 00B1C: edb0
    LD HL,$b0e                     ; ROM 00B1E: 210e0b
    CALL $0ad1                     ; ROM 00B21: cdd10a
    LD A,($c010)                   ; ROM 00B24: 3a10c0
    AND $ef                        ; ROM 00B27: e6ef
    LD E,A                         ; ROM 00B29: 5f
    LD D,$80                       ; ROM 00B2A: 1680
    RST $28                        ; ROM 00B2C: ef
    LD A,E                         ; ROM 00B2D: 7b
    LD ($c010),A                   ; ROM 00B2E: 3210c0
    LD A,($c011)                   ; ROM 00B31: 3a11c0
    AND $bf                        ; ROM 00B34: e6bf
    LD ($c011),A                   ; ROM 00B36: 3211c0
    LD E,A                         ; ROM 00B39: 5f
    LD D,$81                       ; ROM 00B3A: 1681
    RST $28                        ; ROM 00B3C: ef
    LD DE,$7f00                    ; ROM 00B3D: 11007f
    LD A,$d0                       ; ROM 00B40: 3ed0
    LD ($dd40),A                   ; ROM 00B42: 3240dd
    JP $03d9                       ; ROM 00B45: c3d903
    LD A,12                        ; ROM 00B48: 3e0c
    LD HL,$404                     ; ROM 00B4A: 210404
    LD ($de0b),A                   ; ROM 00B4D: 320bde
    LD ($de0c),HL                  ; ROM 00B50: 220cde
    CALL $0b12                     ; ROM 00B53: cd120b
    LD DE,$8800                    ; ROM 00B56: 110088
    RST $28                        ; ROM 00B59: ef
    INC D                          ; ROM 00B5A: 14
    RST $28                        ; ROM 00B5B: ef
    LD HL,0                        ; ROM 00B5C: 210000
    LD ($c018),HL                  ; ROM 00B5F: 2218c0
    LD DE,$7f40                    ; ROM 00B62: 11407f
    LD BC,$20                      ; ROM 00B65: 012000
    CALL $0397                     ; ROM 00B68: cd9703
    LD HL,$1fa                     ; ROM 00B6B: 21fa01
    LD DE,$7800                    ; ROM 00B6E: 110078
    LD BC,$380                     ; ROM 00B71: 018003
    CALL $0397                     ; ROM 00B74: cd9703
    LD ($d600),HL                  ; ROM 00B77: 2200d6
    LD HL,$d600                    ; ROM 00B7A: 2100d6
    LD DE,$d602                    ; ROM 00B7D: 1102d6
    LD BC,$5fe                     ; ROM 00B80: 01fe05
    LDIR                           ; ROM 00B83: edb0
    LD HL,$dca0                    ; ROM 00B85: 21a0dc
    LD DE,$dca1                    ; ROM 00B88: 11a1dc
    LD BC,$1f                      ; ROM 00B8B: 011f00
    LD (HL),B                      ; ROM 00B8E: 70
    LDIR                           ; ROM 00B8F: edb0
    RET                            ; ROM 00B91: c9
    CALL $0b95                     ; ROM 00B92: cd950b
    PUSH AF                        ; ROM 00B95: f5
    PUSH BC                        ; ROM 00B96: c5
    PUSH DE                        ; ROM 00B97: d5
    PUSH HL                        ; ROM 00B98: e5
    EX AF,AF'                      ; ROM 00B99: 08
    EXX                            ; ROM 00B9A: d9
    PUSH AF                        ; ROM 00B9B: f5
    PUSH BC                        ; ROM 00B9C: c5
    PUSH DE                        ; ROM 00B9D: d5
    PUSH HL                        ; ROM 00B9E: e5
    PUSH IX                        ; ROM 00B9F: dde5
    PUSH IY                        ; ROM 00BA1: fde5
    LD A,($ffff)                   ; ROM 00BA3: 3affff
    PUSH AF                        ; ROM 00BA6: f5
    LD A,1                         ; ROM 00BA7: 3e01
    LD ($c02e),A                   ; ROM 00BA9: 322ec0
    EI                             ; ROM 00BAC: fb
    LD A,($c02e)                   ; ROM 00BAD: 3a2ec0
    OR A                           ; ROM 00BB0: b7
    JR nz,$0bad                    ; ROM 00BB1: 20fa
    POP AF                         ; ROM 00BB3: f1
    LD ($ffff),A                   ; ROM 00BB4: 32ffff
    POP IY                         ; ROM 00BB7: fde1
    POP IX                         ; ROM 00BB9: dde1
    POP HL                         ; ROM 00BBB: e1
    POP DE                         ; ROM 00BBC: d1
    POP BC                         ; ROM 00BBD: c1
    POP AF                         ; ROM 00BBE: f1
    EXX                            ; ROM 00BBF: d9
    EX AF,AF'                      ; ROM 00BC0: 08
    POP HL                         ; ROM 00BC1: e1
    POP DE                         ; ROM 00BC2: d1
    POP BC                         ; ROM 00BC3: c1
    POP AF                         ; ROM 00BC4: f1
    RET                            ; ROM 00BC5: c9
    LD A,1                         ; ROM 00BC6: 3e01
    LD ($c033),A                   ; ROM 00BC8: 3233c0
    CALL $0b95                     ; ROM 00BCB: cd950b
    XOR A                          ; ROM 00BCE: af
    LD ($c033),A                   ; ROM 00BCF: 3233c0
    RET                            ; ROM 00BD2: c9
    PUSH DE                        ; ROM 00BD3: d5
    LD DE,$d100                    ; ROM 00BD4: 1100d1
    LD A,(HL)                      ; ROM 00BD7: 7e
    INC HL                         ; ROM 00BD8: 23
    OR A                           ; ROM 00BD9: b7
    JR z,$0bf4                     ; ROM 00BDA: 2818
    JP p,$0bea                     ; ROM 00BDC: f2ea0b
    AND $7f                        ; ROM 00BDF: e67f
    LD B,A                         ; ROM 00BE1: 47
    LD A,(HL)                      ; ROM 00BE2: 7e
    LD (DE),A                      ; ROM 00BE3: 12
    INC DE                         ; ROM 00BE4: 13
    INC HL                         ; ROM 00BE5: 23
    DJNZ $0be2                     ; ROM 00BE6: 10fa
    JR $0bd7                       ; ROM 00BE8: 18ed
    LD B,A                         ; ROM 00BEA: 47
    LD A,(HL)                      ; ROM 00BEB: 7e
    LD (DE),A                      ; ROM 00BEC: 12
    INC DE                         ; ROM 00BED: 13
    INC A                          ; ROM 00BEE: 3c
    DJNZ $0bec                     ; ROM 00BEF: 10fb
    INC HL                         ; ROM 00BF1: 23
    JR $0bd7                       ; ROM 00BF2: 18e3
    POP DE                         ; ROM 00BF4: d1
    PUSH HL                        ; ROM 00BF5: e5
    LD HL,$d100                    ; ROM 00BF6: 2100d1
    CALL $0bfe                     ; ROM 00BF9: cdfe0b
    POP HL                         ; ROM 00BFC: e1
    RET                            ; ROM 00BFD: c9
    LD C,2                         ; ROM 00BFE: 0e02
    LD B,C                         ; ROM 00C00: 41
    PUSH DE                        ; ROM 00C01: d5
    PUSH BC                        ; ROM 00C02: c5
    LD A,(HL)                      ; ROM 00C03: 7e
    OR A                           ; ROM 00C04: b7
    JR z,$0c2a                     ; ROM 00C05: 2823
    JP p,$0c1b                     ; ROM 00C07: f21b0c
    AND $7f                        ; ROM 00C0A: e67f
    LD B,A                         ; ROM 00C0C: 47
    INC HL                         ; ROM 00C0D: 23
    LD A,(HL)                      ; ROM 00C0E: 7e
    LD (DE),A                      ; ROM 00C0F: 12
    LD A,C                         ; ROM 00C10: 79
    ADD A,E                        ; ROM 00C11: 83
    LD E,A                         ; ROM 00C12: 5f
    JR nc,$0c16                    ; ROM 00C13: 3001
    INC D                          ; ROM 00C15: 14
    DJNZ $0c0d                     ; ROM 00C16: 10f5
    INC HL                         ; ROM 00C18: 23
    JR $0c03                       ; ROM 00C19: 18e8
    LD B,A                         ; ROM 00C1B: 47
    INC HL                         ; ROM 00C1C: 23
    LD A,(HL)                      ; ROM 00C1D: 7e
    LD (DE),A                      ; ROM 00C1E: 12
    LD A,C                         ; ROM 00C1F: 79
    ADD A,E                        ; ROM 00C20: 83
    LD E,A                         ; ROM 00C21: 5f
    JR nc,$0c25                    ; ROM 00C22: 3001
    INC D                          ; ROM 00C24: 14
    DJNZ $0c1d                     ; ROM 00C25: 10f6
    INC HL                         ; ROM 00C27: 23
    JR $0c03                       ; ROM 00C28: 18d9
    POP BC                         ; ROM 00C2A: c1
    POP DE                         ; ROM 00C2B: d1
    INC DE                         ; ROM 00C2C: 13
    INC HL                         ; ROM 00C2D: 23
    DJNZ $0c01                     ; ROM 00C2E: 10d1
    RET                            ; ROM 00C30: c9
    db $21,$76,$87,$18,$03 ; ROM 00C31
    LD HL,$87c6                    ; ROM 00C36: 21c687
    LD B,0                         ; ROM 00C39: 0600
    SLA C                          ; ROM 00C3B: cb21
    RL B                           ; ROM 00C3D: cb10
    SLA C                          ; ROM 00C3F: cb21
    RL B                           ; ROM 00C41: cb10
    SLA C                          ; ROM 00C43: cb21
    RL B                           ; ROM 00C45: cb10
    PUSH BC                        ; ROM 00C47: c5
    LD A,3                         ; ROM 00C48: 3e03
    LD ($ffff),A                   ; ROM 00C4A: 32ffff
    CALL $0365                     ; ROM 00C4D: cd6503
    POP BC                         ; ROM 00C50: c1
    RST $28                        ; ROM 00C51: ef
    LD A,$ff                       ; ROM 00C52: 3eff
    OUT ($00be),A                  ; ROM 00C54: d3be
    PUSH AF                        ; ROM 00C56: f5
    POP AF                         ; ROM 00C57: f1
    IN A,($00be)                   ; ROM 00C58: dbbe
    PUSH AF                        ; ROM 00C5A: f5
    POP AF                         ; ROM 00C5B: f1
    IN A,($00be)                   ; ROM 00C5C: dbbe
    PUSH AF                        ; ROM 00C5E: f5
    POP AF                         ; ROM 00C5F: f1
    IN A,($00be)                   ; ROM 00C60: dbbe
    DEC BC                         ; ROM 00C62: 0b
    LD A,B                         ; ROM 00C63: 78
    OR C                           ; ROM 00C64: b1
    JR nz,$0c52                    ; ROM 00C65: 20eb
    RET                            ; ROM 00C67: c9
    LD A,3                         ; ROM 00C68: 3e03
    LD ($ffff),A                   ; ROM 00C6A: 32ffff
    LD E,(HL)                      ; ROM 00C6D: 5e
    INC HL                         ; ROM 00C6E: 23
    LD D,(HL)                      ; ROM 00C6F: 56
    INC HL                         ; ROM 00C70: 23
    LD A,(HL)                      ; ROM 00C71: 7e
    INC HL                         ; ROM 00C72: 23
    OR A                           ; ROM 00C73: b7
    RET z                          ; ROM 00C74: c8
    PUSH HL                        ; ROM 00C75: e5
    SUB $41                        ; ROM 00C76: d641
    LD L,A                         ; ROM 00C78: 6f
    LD H,0                         ; ROM 00C79: 2600
    ADD HL,HL                      ; ROM 00C7B: 29
    ADD HL,HL                      ; ROM 00C7C: 29
    ADD HL,HL                      ; ROM 00C7D: 29
    LD BC,$87c6                    ; ROM 00C7E: 01c687
    ADD HL,BC                      ; ROM 00C81: 09
    LD BC,8                        ; ROM 00C82: 010800
    LD A,3                         ; ROM 00C85: 3e03
    CALL $0365                     ; ROM 00C87: cd6503
    LD BC,8                        ; ROM 00C8A: 010800
    CALL $0c51                     ; ROM 00C8D: cd510c
    LD HL,$20                      ; ROM 00C90: 212000
    ADD HL,DE                      ; ROM 00C93: 19
    EX DE,HL                       ; ROM 00C94: eb
    POP HL                         ; ROM 00C95: e1
    JR $0c71                       ; ROM 00C96: 18d9
    CALL $0b48                     ; ROM 00C98: cd480b
    LD ($c02a),SP                  ; ROM 00C9B: ed732ac0
    LD HL,$a74c                    ; ROM 00C9F: 214ca7
    LD DE,$6600                    ; ROM 00CA2: 110066
    LD A,4                         ; ROM 00CA5: 3e04
    CALL $0327                     ; ROM 00CA7: cd2703
    LD DE,$6820                    ; ROM 00CAA: 112068
    LD C,$20                       ; ROM 00CAD: 0e20
    CALL $0c36                     ; ROM 00CAF: cd360c
    LD HL,$a7d0                    ; ROM 00CB2: 21d0a7
    LD DE,$7400                    ; ROM 00CB5: 110074
    LD A,4                         ; ROM 00CB8: 3e04
    CALL $0327                     ; ROM 00CBA: cd2703
    LD HL,$10c3                    ; ROM 00CBD: 21c310
    LD B,7                         ; ROM 00CC0: 0607
    PUSH BC                        ; ROM 00CC2: c5
    CALL $0c68                     ; ROM 00CC3: cd680c
    POP BC                         ; ROM 00CC6: c1
    DJNZ $0cc2                     ; ROM 00CC7: 10f9
    LD DE,$4000                    ; ROM 00CC9: 110040
    LD HL,0                        ; ROM 00CCC: 210000
    LD BC,$1200                    ; ROM 00CCF: 010012
    CALL $0397                     ; ROM 00CD2: cd9703
    CALL $1deb                     ; ROM 00CD5: cdeb1d
    LD A,$85                       ; ROM 00CD8: 3e85
    LD ($de06),A                   ; ROM 00CDA: 3206de
    CALL $0aa4                     ; ROM 00CDD: cda40a
    XOR A                          ; ROM 00CE0: af
    LD ($c030),A                   ; ROM 00CE1: 3230c0
    LD ($dce0),A                   ; ROM 00CE4: 32e0dc
    LD ($dce1),A                   ; ROM 00CE7: 32e1dc
    LD HL,$10f1                    ; ROM 00CEA: 21f110
    LD ($dcea),HL                  ; ROM 00CED: 22eadc
    LD HL,$b9ce                    ; ROM 00CF0: 21ceb9
    LD ($dce8),HL                  ; ROM 00CF3: 22e8dc
    LD HL,$f36                     ; ROM 00CF6: 21360f
    LD ($dcec),HL                  ; ROM 00CF9: 22ecdc
    CALL $0e4a                     ; ROM 00CFC: cd4a0e
    CALL $0d10                     ; ROM 00CFF: cd100d
    CALL $10df                     ; ROM 00D02: cddf10
    LD A,($dce1)                   ; ROM 00D05: 3ae1dc
    OR A                           ; ROM 00D08: b7
    JR z,$0cff                     ; ROM 00D09: 28f4
    LD SP,($c02a)                  ; ROM 00D0B: ed7b2ac0
    RET                            ; ROM 00D0F: c9
    CALL $0f09                     ; ROM 00D10: cd090f
    LD A,($c030)                   ; ROM 00D13: 3a30c0
    OR A                           ; ROM 00D16: b7
    JR nz,$0d10                    ; ROM 00D17: 20f7
    LD A,$5a                       ; ROM 00D19: 3e5a
    LD ($c030),A                   ; ROM 00D1B: 3230c0
    LD A,6                         ; ROM 00D1E: 3e06
    LD ($ffff),A                   ; ROM 00D20: 32ffff
    LD HL,($dce8)                  ; ROM 00D23: 2ae8dc
    LD A,(HL)                      ; ROM 00D26: 7e
    OR A                           ; ROM 00D27: b7
    JR nz,$0d30                    ; ROM 00D28: 2006
    LD A,1                         ; ROM 00D2A: 3e01
    LD ($dce1),A                   ; ROM 00D2C: 32e1dc
    RET                            ; ROM 00D2F: c9
    CALL $0d6d                     ; ROM 00D30: cd6d0d
    CALL $0d59                     ; ROM 00D33: cd590d
    CALL $0d6d                     ; ROM 00D36: cd6d0d
    LD DE,$dbc2                    ; ROM 00D39: 11c2db
    LD A,6                         ; ROM 00D3C: 3e06
    LD ($ffff),A                   ; ROM 00D3E: 32ffff
    LD A,(HL)                      ; ROM 00D41: 7e
    INC HL                         ; ROM 00D42: 23
    CP $ff                         ; ROM 00D43: feff
    JR z,$0d4f                     ; ROM 00D45: 2808
    LD (DE),A                      ; ROM 00D47: 12
    INC DE                         ; ROM 00D48: 13
    LD A,9                         ; ROM 00D49: 3e09
    LD (DE),A                      ; ROM 00D4B: 12
    INC DE                         ; ROM 00D4C: 13
    JR $0d3c                       ; ROM 00D4D: 18ed
    LD ($dce8),HL                  ; ROM 00D4F: 22e8dc
    LD A,($dce0)                   ; ROM 00D52: 3ae0dc
    INC A                          ; ROM 00D55: 3c
    LD ($dce0),A                   ; ROM 00D56: 32e0dc
    PUSH HL                        ; ROM 00D59: e5
    LD B,2                         ; ROM 00D5A: 0602
    CALL $0f2c                     ; ROM 00D5C: cd2c0f
    LD HL,$d900                    ; ROM 00D5F: 2100d9
    LD DE,$7b00                    ; ROM 00D62: 11007b
    LD BC,$300                     ; ROM 00D65: 010003
    CALL $0384                     ; ROM 00D68: cd8403
    POP HL                         ; ROM 00D6B: e1
    RET                            ; ROM 00D6C: c9
    PUSH HL                        ; ROM 00D6D: e5
    LD HL,$d940                    ; ROM 00D6E: 2140d9
    LD DE,$d900                    ; ROM 00D71: 1100d9
    LD BC,$2c0                     ; ROM 00D74: 01c002
    LDIR                           ; ROM 00D77: edb0
    LD HL,$1fa                     ; ROM 00D79: 21fa01
    LD ($dbc0),HL                  ; ROM 00D7C: 22c0db
    LD HL,$dbc0                    ; ROM 00D7F: 21c0db
    LD DE,$dbc2                    ; ROM 00D82: 11c2db
    LD BC,$3e                      ; ROM 00D85: 013e00
    LDIR                           ; ROM 00D88: edb0
    POP HL                         ; ROM 00D8A: e1
    RET                            ; ROM 00D8B: c9
    db $3E,$06,$32,$FF,$FF,$21,$95,$B5,$11,$00,$C9,$0E,$02,$CD,$00,$0C ; ROM 00D8C
    db $0E,$01,$C5,$21,$00,$C9,$11,$02,$40,$EF,$79,$A6,$23,$D3,$BE,$79 ; ROM 00D9C
    db $A6,$23,$13,$13,$13,$13,$D3,$BE,$CB,$01,$CB,$01,$7A,$FE,$58,$38 ; ROM 00DAC
    db $E8,$CD,$1E,$0F,$C1,$37,$CB,$11,$30,$D8,$21,$4A,$10,$22,$EC,$DC ; ROM 00DBC
    db $21,$E4,$0F,$C3,$54,$0F,$21,$1F,$AF,$CD,$A5,$0E,$CD,$0C,$0E,$11 ; ROM 00DCC
    db $00,$40,$CD,$14,$0E,$CD,$0C,$0E,$11,$01,$40,$CD,$14,$0E,$CD,$2B ; ROM 00DDC
    db $0E,$21,$00,$C9,$0E,$00,$59,$16,$00,$06,$18,$73,$23,$72,$23,$3E ; ROM 00DEC
    db $0C,$83,$5F,$30,$01,$14,$10,$F3,$0C,$79,$FE,$0C,$38,$E8,$18,$5A ; ROM 00DFC
    db $11,$00,$C9,$0E,$01,$C3,$00,$0C,$E5,$21,$00,$C9,$01,$00,$09,$EF ; ROM 00E0C
    db $7E,$23,$D3,$BE,$13,$13,$13,$13,$0B,$78,$B1,$20,$F2,$E1,$C9 ; ROM 00E1C
    PUSH HL                        ; ROM 00E2B: e5
    LD DE,$4003                    ; ROM 00E2C: 110340
    RST $28                        ; ROM 00E2F: ef
    INC DE                         ; ROM 00E30: 13
    INC DE                         ; ROM 00E31: 13
    INC DE                         ; ROM 00E32: 13
    INC DE                         ; ROM 00E33: 13
    LD A,$ff                       ; ROM 00E34: 3eff
    OUT ($00be),A                  ; ROM 00E36: d3be
    LD A,D                         ; ROM 00E38: 7a
    CP $64                         ; ROM 00E39: fe64
    JR c,$0e2f                     ; ROM 00E3B: 38f2
    POP HL                         ; ROM 00E3D: e1
    RET                            ; ROM 00E3E: c9
    db $CD,$51,$0F,$11,$55,$10,$21,$55,$A6,$18,$06 ; ROM 00E3F
    LD DE,$f37                     ; ROM 00E4A: 11370f
    LD HL,$9d70                    ; ROM 00E4D: 21709d
    LD ($dcec),DE                  ; ROM 00E50: ed53ecdc
    CALL $0ea5                     ; ROM 00E54: cda50e
    LD DE,$4000                    ; ROM 00E57: 110040
    CALL $032a                     ; ROM 00E5A: cd2a03
    CALL $0e2b                     ; ROM 00E5D: cd2b0e
    LD DE,$c900                    ; ROM 00E60: 1100c9
    CALL $0bd3                     ; ROM 00E63: cdd30b
    LD HL,$c900                    ; ROM 00E66: 2100c9
    LD DE,$d608                    ; ROM 00E69: 1108d6
    LD BC,$300c                    ; ROM 00E6C: 010c30
    CALL $7357                     ; ROM 00E6F: cd5773
    CALL $0efa                     ; ROM 00E72: cdfa0e
    LD D,$7f                       ; ROM 00E75: 167f
    LD C,$be                       ; ROM 00E77: 0ebe
    EXX                            ; ROM 00E79: d9
    LD HL,$4003                    ; ROM 00E7A: 210340
    LD DE,4                        ; ROM 00E7D: 110400
    LD C,$bf                       ; ROM 00E80: 0ebf
    EXX                            ; ROM 00E82: d9
    LD E,D                         ; ROM 00E83: 5a
    RLC E                          ; ROM 00E84: cb03
    RLC E                          ; ROM 00E86: cb03
    CALL $0f1e                     ; ROM 00E88: cd1e0f
    EXX                            ; ROM 00E8B: d9
    DI                             ; ROM 00E8C: f3
    OUT (C),L                      ; ROM 00E8D: ed69
    OUT (C),H                      ; ROM 00E8F: ed61
    EI                             ; ROM 00E91: fb
    ADD HL,DE                      ; ROM 00E92: 19
    LD A,H                         ; ROM 00E93: 7c
    EXX                            ; ROM 00E94: d9
    RRC E                          ; ROM 00E95: cb0b
    RRC E                          ; ROM 00E97: cb0b
    OUT (C),E                      ; ROM 00E99: ed59
    CP $64                         ; ROM 00E9B: fe64
    JP nz,$0e8b                    ; ROM 00E9D: c28b0e
    SRL D                          ; ROM 00EA0: cb3a
    JR c,$0e79                     ; ROM 00EA2: 38d5
    RET                            ; ROM 00EA4: c9
    PUSH HL                        ; ROM 00EA5: e5
    LD HL,$9fa                     ; ROM 00EA6: 21fa09
    LD ($d600),HL                  ; ROM 00EA9: 2200d6
    LD HL,$d600                    ; ROM 00EAC: 2100d6
    LD DE,$d602                    ; ROM 00EAF: 1102d6
    LD BC,$2fe                     ; ROM 00EB2: 01fe02
    LDIR                           ; ROM 00EB5: edb0
    CALL $0efa                     ; ROM 00EB7: cdfa0e
    LD HL,$dca0                    ; ROM 00EBA: 21a0dc
    LD DE,$dca1                    ; ROM 00EBD: 11a1dc
    LD BC,15                       ; ROM 00EC0: 010f00
    LD (HL),B                      ; ROM 00EC3: 70
    LDIR                           ; ROM 00EC4: edb0
    POP HL                         ; ROM 00EC6: e1
    LD A,6                         ; ROM 00EC7: 3e06
    LD ($ffff),A                   ; ROM 00EC9: 32ffff
    LD DE,$dca0                    ; ROM 00ECC: 11a0dc
    LD C,4                         ; ROM 00ECF: 0e04
    LDIR                           ; ROM 00ED1: edb0
    RET                            ; ROM 00ED3: c9
    db $21,$36,$0F,$22,$EC,$DC,$21,$C0,$DC,$11,$C1,$DC,$01,$0F,$00,$70 ; ROM 00ED4
    db $ED,$B0,$21,$0E,$0B,$7E,$87,$28,$0C,$CD,$DE,$0A,$28,$F7,$06,$04 ; ROM 00EE4
    db $CD,$2C,$0F,$18,$F0,$C9 ; ROM 00EF4
    CALL $0f1e                     ; ROM 00EFA: cd1e0f
    LD HL,$d600                    ; ROM 00EFD: 2100d6
    LD DE,$7800                    ; ROM 00F00: 110078
    LD BC,$300                     ; ROM 00F03: 010003
    CALL $0384                     ; ROM 00F06: cd8403
    CALL $0b95                     ; ROM 00F09: cd950b
    PUSH BC                        ; ROM 00F0C: c5
    PUSH DE                        ; ROM 00F0D: d5
    PUSH HL                        ; ROM 00F0E: e5
    CALL $0f32                     ; ROM 00F0F: cd320f
    POP HL                         ; ROM 00F12: e1
    POP DE                         ; ROM 00F13: d1
    POP BC                         ; ROM 00F14: c1
    LD A,($c021)                   ; ROM 00F15: 3a21c0
    AND $30                        ; ROM 00F18: e630
    JP nz,$0d0b                    ; ROM 00F1A: c20b0d
    RET                            ; ROM 00F1D: c9
    CALL $0f09                     ; ROM 00F1E: cd090f
    IN A,($007e)                   ; ROM 00F21: db7e
    CP $70                         ; ROM 00F23: fe70
    JR c,$0f21                     ; ROM 00F25: 38fa
    CP $80                         ; ROM 00F27: fe80
    JR nc,$0f21                    ; ROM 00F29: 30f6
    RET                            ; ROM 00F2B: c9
    CALL $0f09                     ; ROM 00F2C: cd090f
    DJNZ $0f2c                     ; ROM 00F2F: 10fb
    RET                            ; ROM 00F31: c9
    LD HL,($dcec)                  ; ROM 00F32: 2aecdc
    JP (HL)                        ; ROM 00F35: e9
    db $C9 ; ROM 00F36
    LD A,($c02f)                   ; ROM 00F37: 3a2fc0
    AND 7                          ; ROM 00F3A: e607
    RET nz                         ; ROM 00F3C: c0
    LD A,5                         ; ROM 00F3D: 3e05
    LD ($ffff),A                   ; ROM 00F3F: 32ffff
    LD A,($dce2)                   ; ROM 00F42: 3ae2dc
    INC A                          ; ROM 00F45: 3c
    CP 6                           ; ROM 00F46: fe06
    JR c,$0f4b                     ; ROM 00F48: 3801
    XOR A                          ; ROM 00F4A: af
    LD ($dce2),A                   ; ROM 00F4B: 32e2dc
    JP $bdff                       ; ROM 00F4E: c3ffbd
    db $21,$95,$0F,$E5,$AF,$32,$E2,$DC,$21,$00,$C3,$11,$01,$C3,$01,$FF ; ROM 00F51
    db $02,$77,$ED,$B0,$E1,$DD,$21,$00,$C3,$7E,$B7,$C8,$DD,$36,$00,$01 ; ROM 00F61
    db $DD,$77,$11,$23,$7E,$DD,$77,$13,$23,$7E,$DD,$77,$0E,$23,$7E,$DD ; ROM 00F71
    db $77,$0C,$23,$7E,$DD,$77,$08,$23,$7E,$DD,$77,$09,$23,$11,$30,$00 ; ROM 00F81
    db $DD,$19,$18,$D5,$0E,$40,$20,$06,$CC,$0F,$05,$4D,$22,$06,$CC,$0F ; ROM 00F91
    db $0E,$58,$24,$06,$CC,$0F,$FF,$58,$24,$06,$CC,$0F,$05,$65,$26,$06 ; ROM 00FA1
    db $CC,$0F,$FF,$70,$28,$06,$CC,$0F,$0E,$70,$28,$06,$CC,$0F,$05,$7D ; ROM 00FB1
    db $2A,$06,$CC,$0F,$0E,$88,$2C,$06,$CC,$0F,$00,$D8,$0F,$DC,$0F,$E0 ; ROM 00FC1
    db $0F,$E0,$0F,$DC,$0F,$D8,$0F,$01,$00,$00,$A0,$01,$00,$00,$A1,$01 ; ROM 00FD1
    db $00,$00,$A2,$FF,$B0,$10,$04,$09,$10,$FD,$B8,$12,$05,$09,$10,$FF ; ROM 00FE1
    db $B4,$16,$03,$11,$10,$FF,$BF,$1F,$07,$09,$10,$FF,$D0,$40,$03,$11 ; ROM 00FF1
    db $10,$FD,$C6,$45,$05,$0D,$10,$00,$17,$10,$27,$10,$37,$10,$17,$10 ; ROM 01001
    db $37,$10,$27,$10,$37,$10,$05,$00,$08,$00,$08,$00,$08,$A4,$F8,$A5 ; ROM 01011
    db $08,$A6,$F8,$A7,$08,$A8,$05,$00,$08,$00,$08,$00,$00,$A9,$00,$AA ; ROM 01021
    db $08,$AB,$F8,$AC,$08,$AD,$06,$00,$00,$08,$00,$08,$00,$00,$AE,$08 ; ROM 01031
    db $AF,$F8,$B0,$08,$B1,$F8,$B2,$08,$B3,$CD,$61,$10,$3E,$05,$32,$FF ; ROM 01041
    db $FF,$C3,$25,$BE,$3A,$2F,$C0,$E6,$03,$21,$BF,$10,$CF,$32,$B2,$DC ; ROM 01051
    db $3A,$2F,$C0,$E6,$03,$20,$07,$3A,$E2,$DC,$3C,$32,$E2,$DC,$CD,$60 ; ROM 01061
    db $0A,$DD,$21,$00,$C3,$06,$10,$C5,$DD,$7E,$00,$B7,$C4,$8B,$10,$11 ; ROM 01071
    db $30,$00,$DD,$19,$C1,$10,$F0,$C3,$78,$09,$FE,$02,$28,$0A,$3A,$E2 ; ROM 01081
    db $DC,$DD,$BE,$0E,$C0,$DD,$34,$00,$DD,$7E,$0B,$DD,$6E,$08,$DD,$66 ; ROM 01091
    db $09,$87,$CF,$CD,$78,$0A,$3A,$2F,$C0,$E6,$03,$C0,$DD,$34,$0B,$DD ; ROM 010A1
    db $7E,$0C,$DD,$BE,$0B,$C0,$DD,$35,$00,$DD,$36,$0B,$00,$C9,$1B,$36 ; ROM 010B1
    db $27,$2D,$00,$64,$62,$00,$C0,$64,$5B,$00,$C0,$65,$5C,$00,$80,$65 ; ROM 010C1
    db $5D,$00,$E0,$67,$5E,$00,$20,$64,$5F,$00,$A0,$65,$61,$00 ; ROM 010D1
    LD HL,($dcea)                  ; ROM 010DF: 2aeadc
    LD A,($dce0)                   ; ROM 010E2: 3ae0dc
    CP (HL)                        ; ROM 010E5: be
    RET nz                         ; ROM 010E6: c0
    INC HL                         ; ROM 010E7: 23
    LD E,(HL)                      ; ROM 010E8: 5e
    INC HL                         ; ROM 010E9: 23
    LD D,(HL)                      ; ROM 010EA: 56
    INC HL                         ; ROM 010EB: 23
    LD ($dcea),HL                  ; ROM 010EC: 22eadc
    EX DE,HL                       ; ROM 010EF: eb
    JP (HL)                        ; ROM 010F0: e9
    db $12,$D4,$0E,$13,$3F,$0E,$27,$D4,$0E,$28,$D2,$0D,$2C,$8C,$0D,$00 ; ROM 010F1
    LD HL,$c0b0                    ; ROM 01101: 21b0c0
    LD DE,$c0b1                    ; ROM 01104: 11b1c0
    LD BC,$14f                     ; ROM 01107: 014f01
    LD (HL),0                      ; ROM 0110A: 3600
    LDIR                           ; ROM 0110C: edb0
    CALL $0b53                     ; ROM 0110E: cd530b
    CALL $1deb                     ; ROM 01111: cdeb1d
    CALL $1260                     ; ROM 01114: cd6012
    LD DE,$d7ce                    ; ROM 01117: 11ced7
    LD BC,$1103                    ; ROM 0111A: 010311
    CALL $0877                     ; ROM 0111D: cd7708
    LD DE,$d904                    ; ROM 01120: 1104d9
    LD BC,$1b0b                    ; ROM 01123: 010b1b
    CALL $0877                     ; ROM 01126: cd7708
    LD HL,$8aea                    ; ROM 01129: 21ea8a
    LD DE,$d690                    ; ROM 0112C: 1190d6
    CALL $0812                     ; ROM 0112F: cd1208
    LD DE,$d710                    ; ROM 01132: 1110d7
    CALL $0812                     ; ROM 01135: cd1208
    LD DE,$d812                    ; ROM 01138: 1112d8
    CALL $0812                     ; ROM 0113B: cd1208
    LD HL,$8b19                    ; ROM 0113E: 21198b
    LD DE,$d988                    ; ROM 01141: 1188d9
    CALL $129f                     ; ROM 01144: cd9f12
    LD DE,$da08                    ; ROM 01147: 1108da
    CALL $129f                     ; ROM 0114A: cd9f12
    LD DE,$da88                    ; ROM 0114D: 1188da
    CALL $129f                     ; ROM 01150: cd9f12
    LD DE,$db08                    ; ROM 01153: 1108db
    CALL $12a3                     ; ROM 01156: cda312
    LD DE,$db26                    ; ROM 01159: 1126db
    LD B,4                         ; ROM 0115C: 0604
    CALL $12b6                     ; ROM 0115E: cdb612
    LD DE,$db30                    ; ROM 01161: 1130db
    LD B,3                         ; ROM 01164: 0603
    CALL $12b6                     ; ROM 01166: cdb612
    LD HL,$d600                    ; ROM 01169: 2100d6
    LD BC,$300                     ; ROM 0116C: 010003
    INC HL                         ; ROM 0116F: 23
    RES 4,(HL)                     ; ROM 01170: cba6
    INC HL                         ; ROM 01172: 23
    DEC BC                         ; ROM 01173: 0b
    LD A,B                         ; ROM 01174: 78
    OR C                           ; ROM 01175: b1
    JR nz,$116f                    ; ROM 01176: 20f7
    CALL $0914                     ; ROM 01178: cd1409
    LD HL,0                        ; ROM 0117B: 210000
    LD ($c0a0),HL                  ; ROM 0117E: 22a0c0
    LD ($d121),HL                  ; ROM 01181: 2221d1
    CALL $0aa4                     ; ROM 01184: cda40a
    CALL $0b95                     ; ROM 01187: cd950b
    CALL $12c1                     ; ROM 0118A: cdc112
    CALL $11ba                     ; ROM 0118D: cdba11
    LD A,($c01d)                   ; ROM 01190: 3a1dc0
    CP $12                         ; ROM 01193: fe12
    JR z,$1187                     ; ROM 01195: 28f0
    CALL $0b48                     ; ROM 01197: cd480b
    CALL $1deb                     ; ROM 0119A: cdeb1d
    LD HL,$a74c                    ; ROM 0119D: 214ca7
    LD DE,$5e00                    ; ROM 011A0: 11005e
    LD A,4                         ; ROM 011A3: 3e04
    CALL $0327                     ; ROM 011A5: cd2703
    CALL $0aa4                     ; ROM 011A8: cda40a
    LD HL,$c0b0                    ; ROM 011AB: 21b0c0
    LD ($dce0),HL                  ; ROM 011AE: 22e0dc
    LD HL,$ab68                    ; ROM 011B1: 2168ab
    CALL $7444                     ; ROM 011B4: cd4474
    JP $0b48                       ; ROM 011B7: c3480b
    LD BC,($c020)                  ; ROM 011BA: ed4b20c0
    BIT 5,B                        ; ROM 011BE: cb68
    JR nz,$11c7                    ; ROM 011C0: 2005
    BIT 4,B                        ; ROM 011C2: cb60
    JR nz,$120a                    ; ROM 011C4: 2044
    RET                            ; ROM 011C6: c9
    LD A,($c0a0)                   ; ROM 011C7: 3aa0c0
    CP $28                         ; ROM 011CA: fe28
    JR z,$120a                     ; ROM 011CC: 283c
    JR nc,$1214                    ; ROM 011CE: 3044
    LD A,3                         ; ROM 011D0: 3e03
    LD ($ffff),A                   ; ROM 011D2: 32ffff
    LD A,($c0a0)                   ; ROM 011D5: 3aa0c0
    LD HL,$8b48                    ; ROM 011D8: 21488b
    ADD A,L                        ; ROM 011DB: 85
    LD L,A                         ; ROM 011DC: 6f
    JR nc,$11e0                    ; ROM 011DD: 3001
    INC H                          ; ROM 011DF: 24
    LD A,($d120)                   ; ROM 011E0: 3a20d1
    LD DE,$d81c                    ; ROM 011E3: 111cd8
    ADD A,E                        ; ROM 011E6: 83
    LD E,A                         ; ROM 011E7: 5f
    JR nc,$11eb                    ; ROM 011E8: 3001
    INC D                          ; ROM 011EA: 14
    CALL $12a7                     ; ROM 011EB: cda712
    LD A,$96                       ; ROM 011EE: 3e96
    LD ($de08),A                   ; ROM 011F0: 3208de
    CALL $0914                     ; ROM 011F3: cd1409
    LD A,($d120)                   ; ROM 011F6: 3a20d1
    ADD A,2                        ; ROM 011F9: c602
    CP $10                         ; ROM 011FB: fe10
    JR z,$1204                     ; ROM 011FD: 2805
    LD ($d120),A                   ; ROM 011FF: 3220d1
    JR $1209                       ; ROM 01202: 1805
    LD A,$29                       ; ROM 01204: 3e29
    LD ($c0a0),A                   ; ROM 01206: 32a0c0
    RET                            ; ROM 01209: c9
    LD A,($d120)                   ; ROM 0120A: 3a20d1
    SUB 2                          ; ROM 0120D: d602
    RET m                          ; ROM 0120F: f8
    LD ($d120),A                   ; ROM 01210: 3220d1
    RET                            ; ROM 01213: c9
    LD A,3                         ; ROM 01214: 3e03
    LD ($ffff),A                   ; ROM 01216: 32ffff
    LD HL,$d81c                    ; ROM 01219: 211cd8
    LD DE,$c0b0                    ; ROM 0121C: 11b0c0
    LD B,8                         ; ROM 0121F: 0608
    LD A,(HL)                      ; ROM 01221: 7e
    EXX                            ; ROM 01222: d9
    LD HL,$8b48                    ; ROM 01223: 21488b
    LD BC,$28                      ; ROM 01226: 012800
    CPIR                           ; ROM 01229: edb1
    LD BC,$27                      ; ROM 0122B: 012700
    ADD HL,BC                      ; ROM 0122E: 09
    LD A,(HL)                      ; ROM 0122F: 7e
    EXX                            ; ROM 01230: d9
    LD (DE),A                      ; ROM 01231: 12
    INC HL                         ; ROM 01232: 23
    INC HL                         ; ROM 01233: 23
    INC DE                         ; ROM 01234: 13
    DJNZ $1221                     ; ROM 01235: 10ea
    LD HL,$c0b8                    ; ROM 01237: 21b8c0
    LD BC,$800                     ; ROM 0123A: 010008
    LD (HL),C                      ; ROM 0123D: 71
    DEC HL                         ; ROM 0123E: 2b
    LD A,(HL)                      ; ROM 0123F: 7e
    CP $20                         ; ROM 01240: fe20
    JR nz,$124b                    ; ROM 01242: 2007
    LD A,C                         ; ROM 01244: 79
    OR A                           ; ROM 01245: b7
    JR nz,$124c                    ; ROM 01246: 2004
    LD (HL),C                      ; ROM 01248: 71
    JR $124c                       ; ROM 01249: 1801
    INC C                          ; ROM 0124B: 0c
    DEC HL                         ; ROM 0124C: 2b
    DJNZ $123f                     ; ROM 0124D: 10f0
    LD A,C                         ; ROM 0124F: 79
    OR A                           ; ROM 01250: b7
    JR nz,$125a                    ; ROM 01251: 2007
    LD A,$96                       ; ROM 01253: 3e96
    LD ($de08),A                   ; ROM 01255: 3208de
    JR $125f                       ; ROM 01258: 1805
    LD A,4                         ; ROM 0125A: 3e04
    LD ($c01d),A                   ; ROM 0125C: 321dc0
    RET                            ; ROM 0125F: c9
    LD HL,$1435                    ; ROM 01260: 213514
    LD DE,$7000                    ; ROM 01263: 110070
    LD BC,$38                      ; ROM 01266: 013800
    LD A,3                         ; ROM 01269: 3e03
    CALL $0365                     ; ROM 0126B: cd6503
    LD A,3                         ; ROM 0126E: 3e03
    LD ($ffff),A                   ; ROM 01270: 32ffff
    LD HL,$8776                    ; ROM 01273: 217687
    LD DE,$5400                    ; ROM 01276: 110054
    LD BC,$180                     ; ROM 01279: 018001
    LD A,2                         ; ROM 0127C: 3e02
    CALL $0365                     ; ROM 0127E: cd6503
    LD DE,$5a00                    ; ROM 01281: 11005a
    LD C,$20                       ; ROM 01284: 0e20
    CALL $0c36                     ; ROM 01286: cd360c
    LD HL,$a74c                    ; ROM 01289: 214ca7
    LD DE,$5e00                    ; ROM 0128C: 11005e
    LD A,4                         ; ROM 0128F: 3e04
    CALL $0327                     ; ROM 01291: cd2703
    LD HL,$a707                    ; ROM 01294: 2107a7
    LD DE,$5f40                    ; ROM 01297: 11405f
    LD A,4                         ; ROM 0129A: 3e04
    JP $0327                       ; ROM 0129C: c32703
    LD B,12                        ; ROM 0129F: 060c
    JR $12a9                       ; ROM 012A1: 1806
    LD B,4                         ; ROM 012A3: 0604
    JR $12a9                       ; ROM 012A5: 1802
    LD B,1                         ; ROM 012A7: 0601
    LD A,(HL)                      ; ROM 012A9: 7e
    INC HL                         ; ROM 012AA: 23
    LD (DE),A                      ; ROM 012AB: 12
    INC DE                         ; ROM 012AC: 13
    LD A,8                         ; ROM 012AD: 3e08
    LD (DE),A                      ; ROM 012AF: 12
    INC DE                         ; ROM 012B0: 13
    INC DE                         ; ROM 012B1: 13
    INC DE                         ; ROM 012B2: 13
    DJNZ $12a9                     ; ROM 012B3: 10f4
    RET                            ; ROM 012B5: c9
    LD A,(HL)                      ; ROM 012B6: 7e
    LD (DE),A                      ; ROM 012B7: 12
    INC HL                         ; ROM 012B8: 23
    INC DE                         ; ROM 012B9: 13
    LD A,8                         ; ROM 012BA: 3e08
    LD (DE),A                      ; ROM 012BC: 12
    INC DE                         ; ROM 012BD: 13
    DJNZ $12b6                     ; ROM 012BE: 10f6
    RET                            ; ROM 012C0: c9
    LD BC,($c020)                  ; ROM 012C1: ed4b20c0
    LD HL,($d121)                  ; ROM 012C5: 2a21d1
    LD D,$18                       ; ROM 012C8: 1618
    LD A,C                         ; ROM 012CA: 79
    AND 15                         ; ROM 012CB: e60f
    JR nz,$12d2                    ; ROM 012CD: 2003
    LD HL,0                        ; ROM 012CF: 210000
    LD A,L                         ; ROM 012D2: 7d
    OR A                           ; ROM 012D3: b7
    JR z,$12d8                     ; ROM 012D4: 2802
    LD D,8                         ; ROM 012D6: 1608
    INC H                          ; ROM 012D8: 24
    LD A,H                         ; ROM 012D9: 7c
    CP D                           ; ROM 012DA: ba
    JR c,$12e5                     ; ROM 012DB: 3808
    LD HL,1                        ; ROM 012DD: 210100
    LD A,C                         ; ROM 012E0: 79
    AND 15                         ; ROM 012E1: e60f
    OR B                           ; ROM 012E3: b0
    LD B,A                         ; ROM 012E4: 47
    LD ($d121),HL                  ; ROM 012E5: 2221d1
    LD A,($c0a0)                   ; ROM 012E8: 3aa0c0
    LD E,A                         ; ROM 012EB: 5f
    BIT 2,B                        ; ROM 012EC: cb50
    JR z,$12f6                     ; ROM 012EE: 2806
    OR A                           ; ROM 012F0: b7
    JR z,$12f6                     ; ROM 012F1: 2803
    DEC A                          ; ROM 012F3: 3d
    JR $133b                       ; ROM 012F4: 1845
    BIT 3,B                        ; ROM 012F6: cb58
    JR z,$1301                     ; ROM 012F8: 2807
    CP $29                         ; ROM 012FA: fe29
    JR nc,$1301                    ; ROM 012FC: 3003
    INC A                          ; ROM 012FE: 3c
    JR $133b                       ; ROM 012FF: 183a
    BIT 0,B                        ; ROM 01301: cb40
    JR z,$1319                     ; ROM 01303: 2814
    CP 12                          ; ROM 01305: fe0c
    JR c,$1319                     ; ROM 01307: 3810
    CP $28                         ; ROM 01309: fe28
    JR c,$1317                     ; ROM 0130B: 380a
    JR z,$1313                     ; ROM 0130D: 2804
    LD A,$22                       ; ROM 0130F: 3e22
    JR $1319                       ; ROM 01311: 1806
    LD A,$20                       ; ROM 01313: 3e20
    JR $1319                       ; ROM 01315: 1802
    SUB 12                         ; ROM 01317: d60c
    BIT 1,B                        ; ROM 01319: cb48
    JR z,$133b                     ; ROM 0131B: 281e
    CP $24                         ; ROM 0131D: fe24
    JR nc,$133b                    ; ROM 0131F: 301a
    CP $1c                         ; ROM 01321: fe1c
    JR c,$1339                     ; ROM 01323: 3814
    CP $1f                         ; ROM 01325: fe1f
    JR c,$1335                     ; ROM 01327: 380c
    CP $22                         ; ROM 01329: fe22
    JR c,$1331                     ; ROM 0132B: 3804
    LD A,$29                       ; ROM 0132D: 3e29
    JR $133b                       ; ROM 0132F: 180a
    LD A,$28                       ; ROM 01331: 3e28
    JR $133b                       ; ROM 01333: 1806
    LD A,$27                       ; ROM 01335: 3e27
    JR $133b                       ; ROM 01337: 1802
    ADD A,12                       ; ROM 01339: c60c
    LD ($c0a0),A                   ; ROM 0133B: 32a0c0
    CP E                           ; ROM 0133E: bb
    JR z,$1346                     ; ROM 0133F: 2805
    LD A,$95                       ; ROM 01341: 3e95
    LD ($de08),A                   ; ROM 01343: 3208de
    CALL $0a60                     ; ROM 01346: cd600a
    LD IX,$d100                    ; ROM 01349: dd2100d1
    LD A,($c0a0)                   ; ROM 0134D: 3aa0c0
    ADD A,A                        ; ROM 01350: 87
    LD HL,$1398                    ; ROM 01351: 219813
    RST 8                          ; ROM 01354: cf
    LD (IX+$11),L                  ; ROM 01355: dd7511
    LD (IX+$13),H                  ; ROM 01358: dd7413
    LD HL,$13ec                    ; ROM 0135B: 21ec13
    LD A,($c0a0)                   ; ROM 0135E: 3aa0c0
    CP $28                         ; ROM 01361: fe28
    JR c,$136f                     ; ROM 01363: 380a
    JR z,$136c                     ; ROM 01365: 2805
    LD HL,$1418                    ; ROM 01367: 211814
    JR $136f                       ; ROM 0136A: 1803
    LD HL,$13f9                    ; ROM 0136C: 21f913
    CALL $0a78                     ; ROM 0136F: cd780a
    LD A,($d120)                   ; ROM 01372: 3a20d1
    LD HL,$1388                    ; ROM 01375: 218813
    RST 8                          ; ROM 01378: cf
    LD (IX+$11),L                  ; ROM 01379: dd7511
    LD (IX+$13),H                  ; ROM 0137C: dd7413
    LD HL,$1431                    ; ROM 0137F: 213114
    CALL $0a78                     ; ROM 01382: cd780a
    JP $0978                       ; ROM 01385: c37809
    db $40,$70,$40,$78,$40,$80,$40,$88,$40,$90,$40,$98,$40,$A0,$40,$A8 ; ROM 01388
    db $70,$20,$70,$30,$70,$40,$70,$50,$70,$60,$70,$70,$70,$80,$70,$90 ; ROM 01398
    db $70,$A0,$70,$B0,$70,$C0,$70,$D0,$80,$20,$80,$30,$80,$40,$80,$50 ; ROM 013A8
    db $80,$60,$80,$70,$80,$80,$80,$90,$80,$A0,$80,$B0,$80,$C0,$80,$D0 ; ROM 013B8
    db $90,$20,$90,$30,$90,$40,$90,$50,$90,$60,$90,$70,$90,$80,$90,$90 ; ROM 013C8
    db $90,$A0,$90,$B0,$90,$C0,$90,$D0,$A0,$20,$A0,$30,$A0,$40,$A0,$50 ; ROM 013D8
    db $A0,$98,$A0,$C0,$04,$FC,$00,$07,$00,$FC,$80,$07,$81,$F9,$82,$07 ; ROM 013E8
    db $83,$0A,$FC,$00,$00,$00,$00,$07,$00,$00,$00,$00,$FC,$80,$08,$84 ; ROM 013F8
    db $08,$84,$08,$84,$07,$81,$E1,$82,$08,$85,$08,$85,$08,$85,$07,$83 ; ROM 01408
    db $08,$FC,$00,$00,$00,$07,$00,$00,$00,$FC,$80,$08,$84,$08,$84,$07 ; ROM 01418
    db $81,$E9,$82,$08,$85,$08,$85,$07,$83,$01,$FC,$00,$86,$00,$00,$3F ; ROM 01428
    db $20,$20,$20,$20,$20,$00,$00,$FC,$04,$04,$04,$04,$04,$20,$20,$20 ; ROM 01438
    db $20,$20,$3F,$00,$00,$04,$04,$04,$04,$04,$FC,$00,$00,$00,$00,$FF ; ROM 01448
    db $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$FF,$00,$00,$00,$7C,$7C ; ROM 01458
    db $00,$00,$00,$00,$00 ; ROM 01468
    CALL $0c98                     ; ROM 0146D: cd980c
    CALL $0b48                     ; ROM 01470: cd480b
    LD ($c02a),SP                  ; ROM 01473: ed732ac0
    LD A,7                         ; ROM 01477: 3e07
    LD ($ffff),A                   ; ROM 01479: 32ffff
    LD HL,$8000                    ; ROM 0147C: 210080
    LD DE,$dca0                    ; ROM 0147F: 11a0dc
    LD BC,$10                      ; ROM 01482: 011000
    LDIR                           ; ROM 01485: edb0
    LD DE,$4000                    ; ROM 01487: 110040
    CALL $032a                     ; ROM 0148A: cd2a03
    LD DE,$d600                    ; ROM 0148D: 1100d6
    CALL $0bd3                     ; ROM 01490: cdd30b
    LD DE,$c900                    ; ROM 01493: 1100c9
    CALL $0bd3                     ; ROM 01496: cdd30b
    LD HL,$dbab                    ; ROM 01499: 21abdb
    LD B,10                        ; ROM 0149C: 060a
    SET 3,(HL)                     ; ROM 0149E: cbde
    INC HL                         ; ROM 014A0: 23
    INC HL                         ; ROM 014A1: 23
    DJNZ $149e                     ; ROM 014A2: 10fa
    LD A,$20                       ; ROM 014A4: 3e20
    LD ($c019),A                   ; ROM 014A6: 3219c0
    LD HL,$dca0                    ; ROM 014A9: 21a0dc
    LD DE,$dcb0                    ; ROM 014AC: 11b0dc
    LDI                            ; ROM 014AF: eda0
    LDI                            ; ROM 014B1: eda0
    XOR A                          ; ROM 014B3: af
    LD ($dcaf),A                   ; ROM 014B4: 32afdc
    LD HL,$dca1                    ; ROM 014B7: 21a1dc
    LD DE,$dca2                    ; ROM 014BA: 11a2dc
    LD BC,9                        ; ROM 014BD: 010900
    LD (HL),A                      ; ROM 014C0: 77
    LDIR                           ; ROM 014C1: edb0
    LD HL,$d600                    ; ROM 014C3: 2100d6
    LD DE,$7900                    ; ROM 014C6: 110079
    LD BC,$600                     ; ROM 014C9: 010006
    CALL $0384                     ; ROM 014CC: cd8403
    CALL $024f                     ; ROM 014CF: cd4f02
    CALL $0aa4                     ; ROM 014D2: cda40a
    LD A,$81                       ; ROM 014D5: 3e81
    LD ($de06),A                   ; ROM 014D7: 3206de
    CALL $165c                     ; ROM 014DA: cd5c16
    CALL $169c                     ; ROM 014DD: cd9c16
    LD BC,$3c                      ; ROM 014E0: 013c00
    CALL $1693                     ; ROM 014E3: cd9316
    CALL $163f                     ; ROM 014E6: cd3f16
    CALL $161d                     ; ROM 014E9: cd1d16
    RET                            ; ROM 014EC: c9
    CALL $0b53                     ; ROM 014ED: cd530b
    CALL $0227                     ; ROM 014F0: cd2702
    LD A,$89                       ; ROM 014F3: 3e89
    CALL $1cf8                     ; ROM 014F5: cdf81c
    CALL $1deb                     ; ROM 014F8: cdeb1d
    CALL $1260                     ; ROM 014FB: cd6012
    LD HL,$b701                    ; ROM 014FE: 2101b7
    LD DE,$7040                    ; ROM 01501: 114070
    LD A,4                         ; ROM 01504: 3e04
    CALL $0327                     ; ROM 01506: cd2703
    LD DE,$d852                    ; ROM 01509: 1152d8
    LD BC,$e04                     ; ROM 0150C: 01040e
    CALL $0877                     ; ROM 0150F: cd7708
    LD HL,$be13                    ; ROM 01512: 2113be
    LD DE,$d898                    ; ROM 01515: 1198d8
    CALL $0812                     ; ROM 01518: cd1208
    CALL $0914                     ; ROM 0151B: cd1409
    CALL $0aa4                     ; ROM 0151E: cda40a
    LD A,($c036)                   ; ROM 01521: 3a36c0
    LD ($c0a0),A                   ; ROM 01524: 32a0c0
    LD HL,$982                     ; ROM 01527: 218209
    LD DE,$18ff                    ; ROM 0152A: 11ff18
    LD A,($c0a0)                   ; ROM 0152D: 3aa0c0
    OR A                           ; ROM 01530: b7
    JR z,$1534                     ; ROM 01531: 2801
    EX DE,HL                       ; ROM 01533: eb
    LD ($d896),HL                  ; ROM 01534: 2296d8
    LD ($d8d6),DE                  ; ROM 01537: ed53d6d8
    CALL $20f5                     ; ROM 0153B: cdf520
    XOR A                          ; ROM 0153E: af
    LD BC,($c020)                  ; ROM 0153F: ed4b20c0
    BIT 0,B                        ; ROM 01543: cb40
    JR nz,$1553                    ; ROM 01545: 200c
    INC A                          ; ROM 01547: 3c
    BIT 1,B                        ; ROM 01548: cb48
    JR nz,$1553                    ; ROM 0154A: 2007
    LD A,B                         ; ROM 0154C: 78
    AND $30                        ; ROM 0154D: e630
    JR nz,$1560                    ; ROM 0154F: 200f
    JR $153b                       ; ROM 01551: 18e8
    LD HL,$c0a0                    ; ROM 01553: 21a0c0
    CP (HL)                        ; ROM 01556: be
    JR z,$153b                     ; ROM 01557: 28e2
    LD HL,$de08                    ; ROM 01559: 2108de
    LD (HL),$95                    ; ROM 0155C: 3695
    JR $1524                       ; ROM 0155E: 18c4
    LD A,$ab                       ; ROM 01560: 3eab
    LD ($de08),A                   ; ROM 01562: 3208de
    LD A,($c0a0)                   ; ROM 01565: 3aa0c0
    OR A                           ; ROM 01568: b7
    JR nz,$1571                    ; ROM 01569: 2006
    LD A,$12                       ; ROM 0156B: 3e12
    LD ($c01d),A                   ; ROM 0156D: 321dc0
    RET                            ; ROM 01570: c9
    CALL $0b53                     ; ROM 01571: cd530b
    CALL $727a                     ; ROM 01574: cd7a72
    LD A,4                         ; ROM 01577: 3e04
    LD HL,$a4fc                    ; ROM 01579: 21fca4
    LD DE,$5400                    ; ROM 0157C: 110054
    CALL $0327                     ; ROM 0157F: cd2703
    CALL $1deb                     ; ROM 01582: cdeb1d
    LD DE,$d65a                    ; ROM 01585: 115ad6
    LD B,3                         ; ROM 01588: 0603
    PUSH BC                        ; ROM 0158A: c5
    PUSH DE                        ; ROM 0158B: d5
    LD HL,$8a8                     ; ROM 0158C: 21a808
    CALL $7295                     ; ROM 0158F: cd9572
    POP DE                         ; ROM 01592: d1
    POP BC                         ; ROM 01593: c1
    LD HL,$c0                      ; ROM 01594: 21c000
    ADD HL,DE                      ; ROM 01597: 19
    EX DE,HL                       ; ROM 01598: eb
    DJNZ $158a                     ; ROM 01599: 10ef
    CALL $7842                     ; ROM 0159B: cd4278
    LD HL,$be26                    ; ROM 0159E: 2126be
    LD DE,$d9ce                    ; ROM 015A1: 11ced9
    CALL $0812                     ; ROM 015A4: cd1208
    LD A,($c036)                   ; ROM 015A7: 3a36c0
    DEC A                          ; ROM 015AA: 3d
    JP p,$15b0                     ; ROM 015AB: f2b015
    LD A,3                         ; ROM 015AE: 3e03
    LD ($c0a0),A                   ; ROM 015B0: 32a0c0
    LD A,3                         ; ROM 015B3: 3e03
    LD ($c0a1),A                   ; ROM 015B5: 32a1c0
    CALL $229c                     ; ROM 015B8: cd9c22
    CALL $0aa4                     ; ROM 015BB: cda40a
    CALL $0b95                     ; ROM 015BE: cd950b
    CALL $0a60                     ; ROM 015C1: cd600a
    CALL $7744                     ; ROM 015C4: cd4477
    CALL $0978                     ; ROM 015C7: cd7809
    LD BC,($c020)                  ; ROM 015CA: ed4b20c0
    BIT 4,B                        ; ROM 015CE: cb60
    JP nz,$14ed                    ; ROM 015D0: c2ed14
    BIT 5,B                        ; ROM 015D3: cb68
    JR z,$15be                     ; ROM 015D5: 28e7
    LD A,($c0a0)                   ; ROM 015D7: 3aa0c0
    CP 3                           ; ROM 015DA: fe03
    JP z,$14ed                     ; ROM 015DC: caed14
    ADD A,A                        ; ROM 015DF: 87
    LD HL,$78c2                    ; ROM 015E0: 21c278
    RST 8                          ; ROM 015E3: cf
    CALL $0444                     ; ROM 015E4: cd4404
    LD C,(HL)                      ; ROM 015E7: 4e
    CALL $043a                     ; ROM 015E8: cd3a04
    LD A,C                         ; ROM 015EB: 79
    OR A                           ; ROM 015EC: b7
    JR nz,$15f6                    ; ROM 015ED: 2007
    LD A,$a1                       ; ROM 015EF: 3ea1
    LD ($de08),A                   ; ROM 015F1: 3208de
    JR $15be                       ; ROM 015F4: 18c8
    CALL $0444                     ; ROM 015F6: cd4404
    LD DE,$c0b0                    ; ROM 015F9: 11b0c0
    LD BC,$250                     ; ROM 015FC: 015002
    LDIR                           ; ROM 015FF: edb0
    CALL $043a                     ; ROM 01601: cd3a04
    LD A,($c0a0)                   ; ROM 01604: 3aa0c0
    INC A                          ; ROM 01607: 3c
    LD ($c036),A                   ; ROM 01608: 3236c0
    LD A,($c0d9)                   ; ROM 0160B: 3ad9c0
    LD ($c318),A                   ; ROM 0160E: 3218c3
    LD HL,($c0c2)                  ; ROM 01611: 2ac2c0
    LD ($c0c0),HL                  ; ROM 01614: 22c0c0
    LD A,6                         ; ROM 01617: 3e06
    LD ($c01d),A                   ; ROM 01619: 321dc0
    RET                            ; ROM 0161C: c9
    LD BC,$168                     ; ROM 0161D: 016801
    LD HL,$cdbe                    ; ROM 01620: 21becd
    LD A,C                         ; ROM 01623: 79
    AND $30                        ; ROM 01624: e630
    JR nz,$162b                    ; ROM 01626: 2003
    LD HL,$d840                    ; ROM 01628: 2140d8
    LD DE,$7b40                    ; ROM 0162B: 11407b
    CALL $16c0                     ; ROM 0162E: cdc016
    PUSH BC                        ; ROM 01631: c5
    LD BC,$40                      ; ROM 01632: 014000
    CALL $0384                     ; ROM 01635: cd8403
    POP BC                         ; ROM 01638: c1
    DEC BC                         ; ROM 01639: 0b
    LD A,B                         ; ROM 0163A: 78
    OR C                           ; ROM 0163B: b1
    JR nz,$1620                    ; ROM 0163C: 20e2
    RET                            ; ROM 0163E: c9
    LD HL,$c900                    ; ROM 0163F: 2100c9
    LD DE,$7900                    ; ROM 01642: 110079
    LD B,8                         ; ROM 01645: 0608
    CALL $16c0                     ; ROM 01647: cdc016
    PUSH BC                        ; ROM 0164A: c5
    LD BC,$40                      ; ROM 0164B: 014000
    CALL $0384                     ; ROM 0164E: cd8403
    POP BC                         ; ROM 01651: c1
    LD A,$40                       ; ROM 01652: 3e40
    ADD A,E                        ; ROM 01654: 83
    LD E,A                         ; ROM 01655: 5f
    JR nc,$1659                    ; ROM 01656: 3001
    INC D                          ; ROM 01658: 14
    DJNZ $1647                     ; ROM 01659: 10ec
    RET                            ; ROM 0165B: c9
    LD B,11                        ; ROM 0165C: 060b
    LD HL,$cb00                    ; ROM 0165E: 2100cb
    CALL $1681                     ; ROM 01661: cd8116
    LD HL,$cbea                    ; ROM 01664: 21eacb
    CALL $1681                     ; ROM 01667: cd8116
    LD HL,$ccd4                    ; ROM 0166A: 21d4cc
    CALL $1681                     ; ROM 0166D: cd8116
    DJNZ $165e                     ; ROM 01670: 10ec
    CALL $1690                     ; ROM 01672: cd9016
    LD HL,$d9c0                    ; ROM 01675: 21c0d9
    LD DE,$7cc0                    ; ROM 01678: 11c07c
    LD BC,$240                     ; ROM 0167B: 014002
    JP $0384                       ; ROM 0167E: c38403
    PUSH BC                        ; ROM 01681: c5
    CALL $1690                     ; ROM 01682: cd9016
    LD BC,$91a                     ; ROM 01685: 011a09
    LD DE,$7cc4                    ; ROM 01688: 11c47c
    CALL $03ab                     ; ROM 0168B: cdab03
    POP BC                         ; ROM 0168E: c1
    RET                            ; ROM 0168F: c9
    LD BC,6                        ; ROM 01690: 010600
    CALL $16c0                     ; ROM 01693: cdc016
    DEC BC                         ; ROM 01696: 0b
    LD A,C                         ; ROM 01697: 79
    OR B                           ; ROM 01698: b0
    JR nz,$1693                    ; ROM 01699: 20f8
    RET                            ; ROM 0169B: c9
    LD HL,$8000                    ; ROM 0169C: 210080
    LD DE,$dcc0                    ; ROM 0169F: 11c0dc
    LD BC,$10                      ; ROM 016A2: 011000
    LDIR                           ; ROM 016A5: edb0
    LD HL,$16bc                    ; ROM 016A7: 21bc16
    LD A,(HL)                      ; ROM 016AA: 7e
    ADD A,A                        ; ROM 016AB: 87
    JR z,$16bb                     ; ROM 016AC: 280d
    CALL $0ade                     ; ROM 016AE: cdde0a
    JR z,$16aa                     ; ROM 016B1: 28f7
    LD BC,6                        ; ROM 016B3: 010600
    CALL $1693                     ; ROM 016B6: cd9316
    JR $16aa                       ; ROM 016B9: 18ef
    RET                            ; ROM 016BB: c9
    db $01,$04,$10,$00 ; ROM 016BC
    CALL $0b95                     ; ROM 016C0: cd950b
    LD A,($c021)                   ; ROM 016C3: 3a21c0
    AND $30                        ; ROM 016C6: e630
    RET z                          ; ROM 016C8: c8
    LD SP,($c02a)                  ; ROM 016C9: ed7b2ac0
    JP $14ed                       ; ROM 016CD: c3ed14
    CALL $175f                     ; ROM 016D0: cd5f17
    LD HL,$c040                    ; ROM 016D3: 2140c0
    LD A,15                        ; ROM 016D6: 3e0f
    SUB (HL)                       ; ROM 016D8: 96
    LD HL,$c066                    ; ROM 016D9: 2166c0
    CP (HL)                        ; ROM 016DC: be
    LD (HL),A                      ; ROM 016DD: 77
    RET z                          ; ROM 016DE: c8
    LD A,$b0                       ; ROM 016DF: 3eb0
    LD ($c065),A                   ; ROM 016E1: 3265c0
    LD ($de06),A                   ; ROM 016E4: 3206de
    LD A,($c011)                   ; ROM 016E7: 3a11c0
    AND $40                        ; ROM 016EA: e640
    CALL nz,$0b12                  ; ROM 016EC: c4120b
    LD A,($c066)                   ; ROM 016EF: 3a66c0
    LD ($ffff),A                   ; ROM 016F2: 32ffff
    LD HL,$8000                    ; ROM 016F5: 210080
    LD DE,$dca0                    ; ROM 016F8: 11a0dc
    LD BC,$10                      ; ROM 016FB: 011000
    LDIR                           ; ROM 016FE: edb0
    LD DE,$4000                    ; ROM 01700: 110040
    CALL $032a                     ; ROM 01703: cd2a03
    LD DE,$c900                    ; ROM 01706: 1100c9
    LD C,2                         ; ROM 01709: 0e02
    CALL $0c00                     ; ROM 0170B: cd000c
    LD HL,$cac0                    ; ROM 0170E: 21c0ca
    LD DE,$c080                    ; ROM 01711: 1180c0
    LD BC,8                        ; ROM 01714: 010800
    LDIR                           ; ROM 01717: edb0
    LD HL,$caf0                    ; ROM 01719: 21f0ca
    LD C,8                         ; ROM 0171C: 0e08
    LDIR                           ; ROM 0171E: edb0
    CALL $1a30                     ; ROM 01720: cd301a
    LD A,5                         ; ROM 01723: 3e05
    LD ($ffff),A                   ; ROM 01725: 32ffff
    CALL $be78                     ; ROM 01728: cd78be
    LD A,2                         ; ROM 0172B: 3e02
    LD ($ffff),A                   ; ROM 0172D: 32ffff
    CALL $81c0                     ; ROM 01730: cdc081
    LD A,($c040)                   ; ROM 01733: 3a40c0
    ADD A,A                        ; ROM 01736: 87
    LD HL,$1759                    ; ROM 01737: 215917
    RST 8                          ; ROM 0173A: cf
    LD A,11                        ; ROM 0173B: 3e0b
    LD ($ffff),A                   ; ROM 0173D: 32ffff
    LD DE,$d100                    ; ROM 01740: 1100d1
    LD C,4                         ; ROM 01743: 0e04
    CALL $0c00                     ; ROM 01745: cd000c
    CALL $0444                     ; ROM 01748: cd4404
    LD HL,$d100                    ; ROM 0174B: 2100d1
    LD DE,$9000                    ; ROM 0174E: 110090
    LD BC,$400                     ; ROM 01751: 010004
    LDIR                           ; ROM 01754: edb0
    JP $043a                       ; ROM 01756: c33a04
    db $02,$B4,$C8,$B6,$5F,$B5 ; ROM 01759
    LD A,($c0ba)                   ; ROM 0175F: 3abac0
    OR A                           ; ROM 01762: b7
    LD A,2                         ; ROM 01763: 3e02
    JR nz,$177c                    ; ROM 01765: 2015
    LD A,($c0b9)                   ; ROM 01767: 3ab9c0
    CP $10                         ; ROM 0176A: fe10
    LD A,1                         ; ROM 0176C: 3e01
    JR c,$177c                     ; ROM 0176E: 380c
    LD A,($c0b9)                   ; ROM 01770: 3ab9c0
    AND 15                         ; ROM 01773: e60f
    CP 15                          ; ROM 01775: fe0f
    LD A,1                         ; ROM 01777: 3e01
    JR z,$177c                     ; ROM 01779: 2801
    XOR A                          ; ROM 0177B: af
    LD ($c040),A                   ; ROM 0177C: 3240c0
    RET                            ; ROM 0177F: c9
    LD A,12                        ; ROM 01780: 3e0c
    LD ($ffff),A                   ; ROM 01782: 32ffff
    LD HL,$c600                    ; ROM 01785: 2100c6
    LD DE,$c601                    ; ROM 01788: 1101c6
    LD BC,$2ff                     ; ROM 0178B: 01ff02
    LD (HL),0                      ; ROM 0178E: 3600
    LDIR                           ; ROM 01790: edb0
    LD HL,($c0b9)                  ; ROM 01792: 2ab9c0
    ADD HL,HL                      ; ROM 01795: 29
    ADD HL,HL                      ; ROM 01796: 29
    ADD HL,HL                      ; ROM 01797: 29
    LD DE,$a34e                    ; ROM 01798: 114ea3
    ADD HL,DE                      ; ROM 0179B: 19
    LD IX,$c600                    ; ROM 0179C: dd2100c6
    LD DE,$30                      ; ROM 017A0: 113000
    LD B,8                         ; ROM 017A3: 0608
    LD A,(HL)                      ; ROM 017A5: 7e
    INC HL                         ; ROM 017A6: 23
    LD (IX),A                      ; ROM 017A7: dd7700
    ADD IX,DE                      ; ROM 017AA: dd19
    DJNZ $17a5                     ; ROM 017AC: 10f7
    LD IX,$c600                    ; ROM 017AE: dd2100c6
    LD B,8                         ; ROM 017B2: 0608
    LD A,(IX)                      ; ROM 017B4: dd7e00
    SUB $20                        ; ROM 017B7: d620
    JR c,$17d7                     ; ROM 017B9: 381c
    LD L,A                         ; ROM 017BB: 6f
    LD H,0                         ; ROM 017BC: 2600
    ADD HL,HL                      ; ROM 017BE: 29
    ADD HL,HL                      ; ROM 017BF: 29
    LD DE,$a0ea                    ; ROM 017C0: 11eaa0
    ADD HL,DE                      ; ROM 017C3: 19
    LD A,(HL)                      ; ROM 017C4: 7e
    LD (IX+$18),A                  ; ROM 017C5: dd7718
    INC HL                         ; ROM 017C8: 23
    LD A,(HL)                      ; ROM 017C9: 7e
    LD (IX+$19),A                  ; ROM 017CA: dd7719
    INC HL                         ; ROM 017CD: 23
    LD A,(HL)                      ; ROM 017CE: 7e
    LD (IX+$1a),A                  ; ROM 017CF: dd771a
    INC HL                         ; ROM 017D2: 23
    LD A,(HL)                      ; ROM 017D3: 7e
    LD (IX+3),A                    ; ROM 017D4: dd7703
    LD DE,$30                      ; ROM 017D7: 113000
    ADD IX,DE                      ; ROM 017DA: dd19
    DJNZ $17b4                     ; ROM 017DC: 10d6
    LD HL,($c0b9)                  ; ROM 017DE: 2ab9c0
    LD H,$c2                       ; ROM 017E1: 26c2
    LD C,(HL)                      ; ROM 017E3: 4e
    LD IX,$c600                    ; ROM 017E4: dd2100c6
    LD B,8                         ; ROM 017E8: 0608
    RLC C                          ; ROM 017EA: cb01
    JR c,$17fe                     ; ROM 017EC: 3810
    EXX                            ; ROM 017EE: d9
    PUSH IX                        ; ROM 017EF: dde5
    POP HL                         ; ROM 017F1: e1
    LD E,L                         ; ROM 017F2: 5d
    LD D,H                         ; ROM 017F3: 54
    INC DE                         ; ROM 017F4: 13
    LD BC,$2f                      ; ROM 017F5: 012f00
    LD (HL),B                      ; ROM 017F8: 70
    LDIR                           ; ROM 017F9: edb0
    EXX                            ; ROM 017FB: d9
    RES 0,C                        ; ROM 017FC: cb81
    LD DE,$30                      ; ROM 017FE: 113000
    ADD IX,DE                      ; ROM 01801: dd19
    DJNZ $17ea                     ; ROM 01803: 10e5
    LD HL,$c603                    ; ROM 01805: 2103c6
    LD DE,$30                      ; ROM 01808: 113000
    XOR A                          ; ROM 0180B: af
    LD B,8                         ; ROM 0180C: 0608
    OR (HL)                        ; ROM 0180E: b6
    ADD HL,DE                      ; ROM 0180F: 19
    DJNZ $180e                     ; ROM 01810: 10fc
    AND $40                        ; ROM 01812: e640
    JR z,$1839                     ; ROM 01814: 2823
    LD HL,($c037)                  ; ROM 01816: 2a37c0
    LD H,0                         ; ROM 01819: 2600
    LD DE,$c0ce                    ; ROM 0181B: 11cec0
    ADD HL,DE                      ; ROM 0181E: 19
    LD A,(HL)                      ; ROM 0181F: 7e
    OR A                           ; ROM 01820: b7
    JR z,$1839                     ; ROM 01821: 2816
    LD HL,$c600                    ; ROM 01823: 2100c6
    LD DE,$c601                    ; ROM 01826: 1101c6
    LD BC,$17f                     ; ROM 01829: 017f01
    LD (HL),0                      ; ROM 0182C: 3600
    LDIR                           ; ROM 0182E: edb0
    OR A                           ; ROM 01830: b7
    JP m,$1839                     ; ROM 01831: fa3918
    LD A,15                        ; ROM 01834: 3e0f
    LD ($c600),A                   ; ROM 01836: 3200c6
    LD HL,$c600                    ; ROM 01839: 2100c6
    LD DE,$30                      ; ROM 0183C: 113000
    LD BC,$800                     ; ROM 0183F: 010008
    LD A,(HL)                      ; ROM 01842: 7e
    OR A                           ; ROM 01843: b7
    JR z,$1847                     ; ROM 01844: 2801
    INC C                          ; ROM 01846: 0c
    ADD HL,DE                      ; ROM 01847: 19
    DJNZ $1842                     ; ROM 01848: 10f8
    LD A,C                         ; ROM 0184A: 79
    OR A                           ; ROM 0184B: b7
    JR nz,$1850                    ; ROM 0184C: 2002
    LD A,$80                       ; ROM 0184E: 3e80
    LD ($c0a2),A                   ; ROM 01850: 32a2c0
    LD IX,$c600                    ; ROM 01853: dd2100c6
    LD BC,$800                     ; ROM 01857: 010008
    LD A,(IX)                      ; ROM 0185A: dd7e00
    CP $20                         ; ROM 0185D: fe20
    JP c,$18d4                     ; ROM 0185F: dad418
    LD A,8                         ; ROM 01862: 3e08
    SUB B                          ; ROM 01864: 90
    LD H,A                         ; ROM 01865: 67
    LD IY,$c600                    ; ROM 01866: fd2100c6
    LD DE,$30                      ; ROM 0186A: 113000
    LD A,(IX)                      ; ROM 0186D: dd7e00
    DEC H                          ; ROM 01870: 25
    JP m,$187d                     ; ROM 01871: fa7d18
    CP (IY)                        ; ROM 01874: fdbe00
    JR z,$18ce                     ; ROM 01877: 2855
    ADD IY,DE                      ; ROM 01879: fd19
    JR $1870                       ; ROM 0187B: 18f3
    LD (IX+2),C                    ; ROM 0187D: dd7102
    SUB $20                        ; ROM 01880: d620
    LD L,A                         ; ROM 01882: 6f
    LD H,0                         ; ROM 01883: 2600
    LD E,L                         ; ROM 01885: 5d
    LD D,H                         ; ROM 01886: 54
    ADD HL,HL                      ; ROM 01887: 29
    ADD HL,DE                      ; ROM 01888: 19
    LD DE,$825f                    ; ROM 01889: 115f82
    ADD HL,DE                      ; ROM 0188C: 19
    LD A,2                         ; ROM 0188D: 3e02
    LD ($ffff),A                   ; ROM 0188F: 32ffff
    LD A,(HL)                      ; ROM 01892: 7e
    INC HL                         ; ROM 01893: 23
    LD E,(HL)                      ; ROM 01894: 5e
    INC HL                         ; ROM 01895: 23
    LD D,(HL)                      ; ROM 01896: 56
    PUSH AF                        ; ROM 01897: f5
    AND 15                         ; ROM 01898: e60f
    LD ($ffff),A                   ; ROM 0189A: 32ffff
    LD L,C                         ; ROM 0189D: 69
    LD H,0                         ; ROM 0189E: 2600
    ADD HL,HL                      ; ROM 018A0: 29
    ADD HL,HL                      ; ROM 018A1: 29
    ADD HL,HL                      ; ROM 018A2: 29
    ADD HL,HL                      ; ROM 018A3: 29
    ADD HL,HL                      ; ROM 018A4: 29
    EX DE,HL                       ; ROM 018A5: eb
    SET 6,D                        ; ROM 018A6: cbf2
    SET 5,D                        ; ROM 018A8: cbea
    PUSH DE                        ; ROM 018AA: d5
    PUSH BC                        ; ROM 018AB: c5
    CALL $032a                     ; ROM 018AC: cd2a03
    POP BC                         ; ROM 018AF: c1
    POP HL                         ; ROM 018B0: e1
    POP AF                         ; ROM 018B1: f1
    AND $f0                        ; ROM 018B2: e6f0
    CALL nz,$1d0d                  ; ROM 018B4: c40d1d
    SRL D                          ; ROM 018B7: cb3a
    RR E                           ; ROM 018B9: cb1b
    SRL D                          ; ROM 018BB: cb3a
    RR E                           ; ROM 018BD: cb1b
    SRL D                          ; ROM 018BF: cb3a
    RR E                           ; ROM 018C1: cb1b
    SRL D                          ; ROM 018C3: cb3a
    RR E                           ; ROM 018C5: cb1b
    SRL D                          ; ROM 018C7: cb3a
    RR E                           ; ROM 018C9: cb1b
    LD C,E                         ; ROM 018CB: 4b
    JR $18d4                       ; ROM 018CC: 1806
    LD A,(IY+2)                    ; ROM 018CE: fd7e02
    LD (IX+2),A                    ; ROM 018D1: dd7702
    LD DE,$30                      ; ROM 018D4: 113000
    ADD IX,DE                      ; ROM 018D7: dd19
    DEC B                          ; ROM 018D9: 05
    JP nz,$185a                    ; ROM 018DA: c25a18
    LD A,C                         ; ROM 018DD: 79
    LD ($c067),A                   ; ROM 018DE: 3267c0
    RET                            ; ROM 018E1: c9
    db $CD,$E9,$18,$22,$B9,$C0,$C9 ; ROM 018E2
    PUSH AF                        ; ROM 018E9: f5
    PUSH BC                        ; ROM 018EA: c5
    PUSH DE                        ; ROM 018EB: d5
    PUSH HL                        ; ROM 018EC: e5
    LD HL,$c600                    ; ROM 018ED: 2100c6
    LD DE,$30                      ; ROM 018F0: 113000
    LD BC,$800                     ; ROM 018F3: 010008
    LD A,(HL)                      ; ROM 018F6: 7e
    OR A                           ; ROM 018F7: b7
    JR z,$18fb                     ; ROM 018F8: 2801
    CCF                            ; ROM 018FA: 3f
    RL C                           ; ROM 018FB: cb11
    ADD HL,DE                      ; ROM 018FD: 19
    DJNZ $18f6                     ; ROM 018FE: 10f6
    LD HL,($c0b9)                  ; ROM 01900: 2ab9c0
    LD H,$c2                       ; ROM 01903: 26c2
    LD (HL),C                      ; ROM 01905: 71
    POP HL                         ; ROM 01906: e1
    POP DE                         ; ROM 01907: d1
    POP BC                         ; ROM 01908: c1
    POP AF                         ; ROM 01909: f1
    RET                            ; ROM 0190A: c9
    PUSH AF                        ; ROM 0190B: f5
    PUSH BC                        ; ROM 0190C: c5
    PUSH DE                        ; ROM 0190D: d5
    PUSH HL                        ; ROM 0190E: e5
    CALL $175f                     ; ROM 0190F: cd5f17
    LD HL,($c0b9)                  ; ROM 01912: 2ab9c0
    ADD HL,HL                      ; ROM 01915: 29
    LD A,H                         ; ROM 01916: 7c
    ADD A,8                        ; ROM 01917: c608
    LD ($ffff),A                   ; ROM 01919: 32ffff
    LD H,$80                       ; ROM 0191C: 2680
    LD E,(HL)                      ; ROM 0191E: 5e
    INC HL                         ; ROM 0191F: 23
    LD D,(HL)                      ; ROM 01920: 56
    EX DE,HL                       ; ROM 01921: eb
    LD DE,$dc00                    ; ROM 01922: 1100dc
    LD C,1                         ; ROM 01925: 0e01
    CALL $0c00                     ; ROM 01927: cd000c
    CALL $1976                     ; ROM 0192A: cd7619
    CALL $1a02                     ; ROM 0192D: cd021a
    LD HL,$dd00                    ; ROM 01930: 2100dd
    LD (HL),0                      ; ROM 01933: 3600
    LD ($c034),HL                  ; ROM 01935: 2234c0
    POP HL                         ; ROM 01938: e1
    POP DE                         ; ROM 01939: d1
    POP BC                         ; ROM 0193A: c1
    POP AF                         ; ROM 0193B: f1
    RET                            ; ROM 0193C: c9
    CALL $1951                     ; ROM 0193D: cd5119
    LD (HL),D                      ; ROM 01940: 72
    RET                            ; ROM 01941: c9
    CALL $195e                     ; ROM 01942: cd5e19
    LD (HL),D                      ; ROM 01945: 72
    RET                            ; ROM 01946: c9
    CALL $194c                     ; ROM 01947: cd4c19
    LD (HL),D                      ; ROM 0194A: 72
    RET                            ; ROM 0194B: c9
    LD HL,($c0b9)                  ; ROM 0194C: 2ab9c0
    JR $195e                       ; ROM 0194F: 180d
    LD HL,($c0b9)                  ; ROM 01951: 2ab9c0
    LD A,($c040)                   ; ROM 01954: 3a40c0
    CP 1                           ; ROM 01957: fe01
    JR nz,$195e                    ; ROM 01959: 2003
    LD HL,($c0bb)                  ; ROM 0195B: 2abbc0
    LD H,$c1                       ; ROM 0195E: 26c1
    LD DE,$4d                      ; ROM 01960: 114d00
    ADD A,E                        ; ROM 01963: 83
    LD E,A                         ; ROM 01964: 5f
    LD A,(DE)                      ; ROM 01965: 1a
    LD E,A                         ; ROM 01966: 5f
    OR (HL)                        ; ROM 01967: b6
    LD D,A                         ; ROM 01968: 57
    LD A,E                         ; ROM 01969: 7b
    AND (HL)                       ; ROM 0196A: a6
    RET                            ; ROM 0196B: c9
    db $CD,$5E,$19,$C8,$F5,$2F,$A6,$77,$F1,$C9 ; ROM 0196C
    CALL $1bcd                     ; ROM 01976: cdcd1b
    LD A,2                         ; ROM 01979: 3e02
    LD ($ffff),A                   ; ROM 0197B: 32ffff
    LD BC,($c0b9)                  ; ROM 0197E: ed4bb9c0
    LD A,B                         ; ROM 01982: 78
    OR A                           ; ROM 01983: b7
    LD HL,$bb62                    ; ROM 01984: 2162bb
    JR z,$198c                     ; ROM 01987: 2803
    LD HL,$bd1f                    ; ROM 01989: 211fbd
    LD DE,4                        ; ROM 0198C: 110400
    LD A,(HL)                      ; ROM 0198F: 7e
    OR A                           ; ROM 01990: b7
    JR z,$1999                     ; ROM 01991: 2806
    CP C                           ; ROM 01993: b9
    JR z,$19a1                     ; ROM 01994: 280b
    ADD HL,DE                      ; ROM 01996: 19
    JR $198f                       ; ROM 01997: 18f6
    LD HL,$199e                    ; ROM 01999: 219e19
    JR $19a2                       ; ROM 0199C: 1804
    db $FF,$FF,$00 ; ROM 0199E
    INC HL                         ; ROM 019A1: 23
    LD DE,$c06e                    ; ROM 019A2: 116ec0
    LDI                            ; ROM 019A5: eda0
    LDI                            ; ROM 019A7: eda0
    LDI                            ; ROM 019A9: eda0
    LD A,($c0ba)                   ; ROM 019AB: 3abac0
    OR A                           ; ROM 019AE: b7
    JR z,$19bc                     ; ROM 019AF: 280b
    CALL $1951                     ; ROM 019B1: cd5119
    CALL nz,$1a7c                  ; ROM 019B4: c47c1a
    XOR A                          ; ROM 019B7: af
    LD ($dd00),A                   ; ROM 019B8: 3200dd
    RET                            ; ROM 019BB: c9
    CALL $1951                     ; ROM 019BC: cd5119
    CALL nz,$1a7c                  ; ROM 019BF: c47c1a
    XOR A                          ; ROM 019C2: af
    LD ($dd00),A                   ; ROM 019C3: 3200dd
    LD A,($c041)                   ; ROM 019C6: 3a41c0
    CP 5                           ; ROM 019C9: fe05
    JR nz,$1a01                    ; ROM 019CB: 2034
    LD BC,$10                      ; ROM 019CD: 011000
    LD A,($c313)                   ; ROM 019D0: 3a13c3
    AND $f0                        ; ROM 019D3: e6f0
    RRCA                           ; ROM 019D5: 0f
    RRCA                           ; ROM 019D6: 0f
    RRCA                           ; ROM 019D7: 0f
    RRCA                           ; ROM 019D8: 0f
    LD E,A                         ; ROM 019D9: 5f
    LD D,B                         ; ROM 019DA: 50
    LD HL,$dc00                    ; ROM 019DB: 2100dc
    ADD HL,DE                      ; ROM 019DE: 19
    LD A,($c30a)                   ; ROM 019DF: 3a0ac3
    CP 0                           ; ROM 019E2: fe00
    JR nz,$19f5                    ; ROM 019E4: 200f
    LD E,$90                       ; ROM 019E6: 1e90
    ADD HL,DE                      ; ROM 019E8: 19
    LD A,(HL)                      ; ROM 019E9: 7e
    CP 12                          ; ROM 019EA: fe0c
    JR nz,$1a01                    ; ROM 019EC: 2013
    LD (HL),$6c                    ; ROM 019EE: 366c
    OR A                           ; ROM 019F0: b7
    SBC HL,BC                      ; ROM 019F1: ed42
    JR $19e9                       ; ROM 019F3: 18f4
    LD A,(HL)                      ; ROM 019F5: 7e
    CP 12                          ; ROM 019F6: fe0c
    JR nz,$19ff                    ; ROM 019F8: 2005
    LD (HL),$6c                    ; ROM 019FA: 366c
    ADD HL,BC                      ; ROM 019FC: 09
    JR $19f5                       ; ROM 019FD: 18f6
    LD (HL),$6d                    ; ROM 019FF: 366d
    RET                            ; ROM 01A01: c9
    CALL $1a30                     ; ROM 01A02: cd301a
    CALL $1a09                     ; ROM 01A05: cd091a
    RET                            ; ROM 01A08: c9
    LD DE,($c0b9)                  ; ROM 01A09: ed5bb9c0
    LD HL,$bf                      ; ROM 01A0D: 21bf00
    OR A                           ; ROM 01A10: b7
    SBC HL,DE                      ; ROM 01A11: ed52
    RET nz                         ; ROM 01A13: c0
    LD HL,$1a2a                    ; ROM 01A14: 212a1a
    LD A,($c0bb)                   ; ROM 01A17: 3abbc0
    LD B,3                         ; ROM 01A1A: 0603
    CP (HL)                        ; ROM 01A1C: be
    INC HL                         ; ROM 01A1D: 23
    LD C,(HL)                      ; ROM 01A1E: 4e
    INC HL                         ; ROM 01A1F: 23
    JR z,$1a25                     ; ROM 01A20: 2803
    DJNZ $1a1c                     ; ROM 01A22: 10f8
    RET                            ; ROM 01A24: c9
    LD A,C                         ; ROM 01A25: 79
    LD ($dc28),A                   ; ROM 01A26: 3228dc
    RET                            ; ROM 01A29: c9
    db $A3,$2A,$2C,$28,$AA,$28 ; ROM 01A2A
    LD A,($c040)                   ; ROM 01A30: 3a40c0
    OR A                           ; ROM 01A33: b7
    RET nz                         ; ROM 01A34: c0
    LD A,($c0ac)                   ; ROM 01A35: 3aacc0
    OR A                           ; ROM 01A38: b7
    JR nz,$1a50                    ; ROM 01A39: 2015
    LD HL,$c998                    ; ROM 01A3B: 2198c9
    LD DE,$cac0                    ; ROM 01A3E: 11c0ca
    LD BC,8                        ; ROM 01A41: 010800
    PUSH HL                        ; ROM 01A44: e5
    PUSH BC                        ; ROM 01A45: c5
    LDIR                           ; ROM 01A46: edb0
    POP BC                         ; ROM 01A48: c1
    POP HL                         ; ROM 01A49: e1
    LD DE,$caf0                    ; ROM 01A4A: 11f0ca
    LDIR                           ; ROM 01A4D: edb0
    RET                            ; ROM 01A4F: c9
    LD A,($c040)                   ; ROM 01A50: 3a40c0
    OR A                           ; ROM 01A53: b7
    RET nz                         ; ROM 01A54: c0
    LD HL,$c080                    ; ROM 01A55: 2180c0
    LD DE,$cac0                    ; ROM 01A58: 11c0ca
    LD BC,8                        ; ROM 01A5B: 010800
    LDIR                           ; ROM 01A5E: edb0
    LD DE,$caf0                    ; ROM 01A60: 11f0ca
    LD C,8                         ; ROM 01A63: 0e08
    LDIR                           ; ROM 01A65: edb0
    LD A,($c0b9)                   ; ROM 01A67: 3ab9c0
    LD HL,$1a79                    ; ROM 01A6A: 21791a
    LD BC,3                        ; ROM 01A6D: 010300
    CPIR                           ; ROM 01A70: edb1
    RET nz                         ; ROM 01A72: c0
    CALL $193d                     ; ROM 01A73: cd3d19
    JP $1976                       ; ROM 01A76: c37619
    db $96,$AA,$CB ; ROM 01A79
    LD DE,($c06f)                  ; ROM 01A7C: ed5b6fc0
    LD A,D                         ; ROM 01A80: 7a
    LD D,$dc                       ; ROM 01A81: 16dc
    ADD A,A                        ; ROM 01A83: 87
    LD HL,$1a8a                    ; ROM 01A84: 218a1a
    JP $0018                       ; ROM 01A87: c31800
    db $B4,$1A,$B7,$1A,$C0,$1A,$C4,$1A,$C8,$1A,$E1,$1A,$E6,$1A,$F6,$1A ; ROM 01A8A
    db $5F,$1B,$7A,$1B,$7E,$1B,$67,$1B,$82,$1B,$8E,$1B,$88,$1B,$93,$1B ; ROM 01A9A
    db $9F,$1B,$AF,$1B,$B4,$1B,$BD,$1B,$C2,$1B,$AF,$18,$13,$3A,$6E,$C0 ; ROM 01AAA
    db $5F,$3A,$6F,$C0,$18,$0A,$3E,$15,$18,$06,$3E,$03,$18,$02,$3E,$04 ; ROM 01ABA
    db $CD,$0E,$1B,$21,$10,$00,$19,$EB,$1A,$21,$05,$1B,$06,$04,$BE,$23 ; ROM 01ACA
    db $CA,$0D,$1B,$23,$10,$F8,$C9,$01,$01,$01,$18,$13,$3E,$30,$32,$30 ; ROM 01ADA
    db $DC,$3E,$31,$32,$40,$DC,$3E,$1F,$32,$50,$DC,$C9,$01,$04,$01,$78 ; ROM 01AEA
    db $CD,$0E,$1B,$21,$10,$00,$19,$EB,$79,$18,$09,$27,$01,$28,$03,$29 ; ROM 01AFA
    db $00,$39,$3A,$7E,$C5,$D5,$12,$6F,$26,$00,$29,$29,$29,$01,$00,$C9 ; ROM 01B0A
    db $09,$E5,$7B,$E6,$F0,$6F,$26,$00,$54,$29,$29,$29,$7B,$E6,$0F,$87 ; ROM 01B1A
    db $87,$5F,$19,$01,$00,$D6,$09,$EB,$2A,$34,$C0,$3E,$02,$77,$2C,$77 ; ROM 01B2A
    db $2C,$77,$2C,$73,$2C,$72,$2C,$22,$34,$C0,$E1,$ED,$A0,$ED,$A0,$ED ; ROM 01B3A
    db $A0,$ED,$A0,$3E,$3C,$83,$5F,$30,$01,$14,$ED,$A0,$ED,$A0,$ED,$A0 ; ROM 01B4A
    db $ED,$A0,$D1,$C1,$C9,$CD,$63,$1B,$13,$3E,$08,$18,$A7,$3E,$09,$CD ; ROM 01B5A
    db $0E,$1B,$3E,$10,$83,$5F,$30,$01,$14,$3E,$06,$CD,$0E,$1B,$1E,$1B ; ROM 01B6A
    db $3E,$4D,$18,$90,$3E,$4C,$18,$8C,$CD,$85,$1B,$CD,$88,$1B,$AF,$CD ; ROM 01B7A
    db $0E,$1B,$13,$C9,$3E,$0C,$C3,$0E,$1B,$CD,$9A,$1B,$3A,$6E,$C0,$5F ; ROM 01B8A
    db $3E,$09,$C3,$0E,$1B,$CD,$85,$1B,$7B,$C6,$0E,$5F,$CD,$85,$1B,$3A ; ROM 01B9A
    db $6E,$C0,$5F,$18,$CB,$CD,$5F,$1B,$18,$F5,$CD,$5F,$1B,$3A,$6E,$C0 ; ROM 01BAA
    db $5F,$18,$CB,$CD,$9A,$1B,$18,$E7,$3E,$0A,$32,$4A,$DC,$3E,$6B,$32 ; ROM 01BBA
    db $5A,$DC,$C9 ; ROM 01BCA
    LD A,($c0ba)                   ; ROM 01BCD: 3abac0
    OR A                           ; ROM 01BD0: b7
    RET z                          ; ROM 01BD1: c8
    LD A,4                         ; ROM 01BD2: 3e04
    CALL $1947                     ; ROM 01BD4: cd4719
    LD A,5                         ; ROM 01BD7: 3e05
    CALL $194c                     ; ROM 01BD9: cd4c19
    CALL nz,$1bf0                  ; ROM 01BDC: c4f01b
    LD A,6                         ; ROM 01BDF: 3e06
    CALL $194c                     ; ROM 01BE1: cd4c19
    CALL nz,$1bf7                  ; ROM 01BE4: c4f71b
    LD A,7                         ; ROM 01BE7: 3e07
    CALL $194c                     ; ROM 01BE9: cd4c19
    CALL nz,$1c06                  ; ROM 01BEC: c4061c
    RET                            ; ROM 01BEF: c9
    LD HL,0                        ; ROM 01BF0: 210000
    LD ($dc17),HL                  ; ROM 01BF3: 2217dc
    RET                            ; ROM 01BF6: c9
    LD A,$18                       ; ROM 01BF7: 3e18
    LD ($dc31),A                   ; ROM 01BF9: 3231dc
    XOR A                          ; ROM 01BFC: af
    LD ($dc41),A                   ; ROM 01BFD: 3241dc
    LD A,$19                       ; ROM 01C00: 3e19
    LD ($dc51),A                   ; ROM 01C02: 3251dc
    RET                            ; ROM 01C05: c9
    LD A,$22                       ; ROM 01C06: 3e22
    LD ($dc3e),A                   ; ROM 01C08: 323edc
    XOR A                          ; ROM 01C0B: af
    LD ($dc4e),A                   ; ROM 01C0C: 324edc
    LD A,$23                       ; ROM 01C0F: 3e23
    LD ($dc5e),A                   ; ROM 01C11: 325edc
    RET                            ; ROM 01C14: c9
    LD A,($c0ba)                   ; ROM 01C15: 3abac0
    OR A                           ; ROM 01C18: b7
    JR nz,$1c4e                    ; ROM 01C19: 2033
    LD B,3                         ; ROM 01C1B: 0603
    PUSH BC                        ; ROM 01C1D: c5
    CALL $1c25                     ; ROM 01C1E: cd251c
    POP BC                         ; ROM 01C21: c1
    DJNZ $1c1d                     ; ROM 01C22: 10f9
    RET                            ; ROM 01C24: c9
    LD A,($c0b9)                   ; ROM 01C25: 3ab9c0
    LD HL,$dcf0                    ; ROM 01C28: 21f0dc
    LD BC,$10                      ; ROM 01C2B: 011000
    CPIR                           ; ROM 01C2E: edb1
    JR z,$1c40                     ; ROM 01C30: 280e
    LD HL,$dcfe                    ; ROM 01C32: 21fedc
    LD DE,$dcff                    ; ROM 01C35: 11ffdc
    LD BC,15                       ; ROM 01C38: 010f00
    LDDR                           ; ROM 01C3B: edb8
    LD ($dcf0),A                   ; ROM 01C3D: 32f0dc
    CALL $04e1                     ; ROM 01C40: cde104
    LD HL,$dcf0                    ; ROM 01C43: 21f0dc
    LD BC,$10                      ; ROM 01C46: 011000
    CPIR                           ; ROM 01C49: edb1
    RET z                          ; ROM 01C4B: c8
    JR $1c88                       ; ROM 01C4C: 183a
    LD B,5                         ; ROM 01C4E: 0605
    PUSH BC                        ; ROM 01C50: c5
    CALL $1c58                     ; ROM 01C51: cd581c
    POP BC                         ; ROM 01C54: c1
    DJNZ $1c50                     ; ROM 01C55: 10f9
    RET                            ; ROM 01C57: c9
    LD A,($c0b9)                   ; ROM 01C58: 3ab9c0
    LD HL,$dcf0                    ; ROM 01C5B: 21f0dc
    LD BC,4                        ; ROM 01C5E: 010400
    CPIR                           ; ROM 01C61: edb1
    JR z,$1c73                     ; ROM 01C63: 280e
    LD HL,$dcf2                    ; ROM 01C65: 21f2dc
    LD DE,$dcf3                    ; ROM 01C68: 11f3dc
    LD BC,3                        ; ROM 01C6B: 010300
    LDDR                           ; ROM 01C6E: edb8
    LD ($dcf0),A                   ; ROM 01C70: 32f0dc
    CALL $04e1                     ; ROM 01C73: cde104
    LD HL,$dcf0                    ; ROM 01C76: 21f0dc
    LD BC,4                        ; ROM 01C79: 010400
    CPIR                           ; ROM 01C7C: edb1
    RET z                          ; ROM 01C7E: c8
    LD HL,$1c91                    ; ROM 01C7F: 21911c
    LD BC,6                        ; ROM 01C82: 010600
    CPIR                           ; ROM 01C85: edb1
    RET z                          ; ROM 01C87: c8
    LD L,A                         ; ROM 01C88: 6f
    LD H,$c2                       ; ROM 01C89: 26c2
    LD A,(HL)                      ; ROM 01C8B: 7e
    OR A                           ; ROM 01C8C: b7
    RET nz                         ; ROM 01C8D: c0
    LD (HL),$ff                    ; ROM 01C8E: 36ff
    RET                            ; ROM 01C90: c9
    db $1E,$5E,$9C,$B8,$BE,$C9 ; ROM 01C91
    LD HL,$c200                    ; ROM 01C97: 2100c2
    LD DE,$c201                    ; ROM 01C9A: 1101c2
    LD BC,$ff                      ; ROM 01C9D: 01ff00
    LD (HL),C                      ; ROM 01CA0: 71
    LDIR                           ; ROM 01CA1: edb0
    LD HL,$dcf0                    ; ROM 01CA3: 21f0dc
    LD DE,$dcf1                    ; ROM 01CA6: 11f1dc
    LD C,15                        ; ROM 01CA9: 0e0f
    LD (HL),B                      ; ROM 01CAB: 70
    LDIR                           ; ROM 01CAC: edb0
    RET                            ; ROM 01CAE: c9
    LD A,($c040)                   ; ROM 01CAF: 3a40c0
    CP 1                           ; ROM 01CB2: fe01
    JR z,$1ccb                     ; ROM 01CB4: 2815
    JR nc,$1cd8                    ; ROM 01CB6: 3020
    LD HL,$1d02                    ; ROM 01CB8: 21021d
    LD BC,11                       ; ROM 01CBB: 010b00
    LD A,($c0b9)                   ; ROM 01CBE: 3ab9c0
    CPIR                           ; ROM 01CC1: edb1
    LD A,$82                       ; ROM 01CC3: 3e82
    JR nz,$1cf8                    ; ROM 01CC5: 2031
    LD A,$84                       ; ROM 01CC7: 3e84
    JR $1cf8                       ; ROM 01CC9: 182d
    LD A,($c0b9)                   ; ROM 01CCB: 3ab9c0
    CP $bf                         ; ROM 01CCE: febf
    LD A,$87                       ; ROM 01CD0: 3e87
    JR nz,$1cf8                    ; ROM 01CD2: 2024
    LD A,$8b                       ; ROM 01CD4: 3e8b
    JR $1cf8                       ; ROM 01CD6: 1820
    LD HL,$c603                    ; ROM 01CD8: 2103c6
    LD DE,$30                      ; ROM 01CDB: 113000
    XOR A                          ; ROM 01CDE: af
    LD B,8                         ; ROM 01CDF: 0608
    OR (HL)                        ; ROM 01CE1: b6
    ADD HL,DE                      ; ROM 01CE2: 19
    DJNZ $1ce1                     ; ROM 01CE3: 10fc
    AND $40                        ; ROM 01CE5: e640
    JR nz,$1cf1                    ; ROM 01CE7: 2008
    XOR A                          ; ROM 01CE9: af
    LD ($c0ae),A                   ; ROM 01CEA: 32aec0
    LD A,$83                       ; ROM 01CED: 3e83
    JR $1cf8                       ; ROM 01CEF: 1807
    LD A,1                         ; ROM 01CF1: 3e01
    LD ($c0ae),A                   ; ROM 01CF3: 32aec0
    LD A,$86                       ; ROM 01CF6: 3e86
    LD HL,$c065                    ; ROM 01CF8: 2165c0
    CP (HL)                        ; ROM 01CFB: be
    LD (HL),A                      ; ROM 01CFC: 77
    RET z                          ; ROM 01CFD: c8
    LD ($de06),A                   ; ROM 01CFE: 3206de
    RET                            ; ROM 01D01: c9
    db $22,$2E,$4C,$55,$57,$94,$95,$C7,$CE,$F0,$FE ; ROM 01D02
    PUSH BC                        ; ROM 01D0D: c5
    PUSH DE                        ; ROM 01D0E: d5
    PUSH HL                        ; ROM 01D0F: e5
    EX DE,HL                       ; ROM 01D10: eb
    OR A                           ; ROM 01D11: b7
    SBC HL,DE                      ; ROM 01D12: ed52
    LD C,L                         ; ROM 01D14: 4d
    LD B,H                         ; ROM 01D15: 44
    LD HL,$1da2                    ; ROM 01D16: 21a21d
    ADD A,L                        ; ROM 01D19: 85
    LD L,A                         ; ROM 01D1A: 6f
    JR nc,$1d1e                    ; ROM 01D1B: 3001
    INC H                          ; ROM 01D1D: 24
    PUSH HL                        ; ROM 01D1E: e5
    EXX                            ; ROM 01D1F: d9
    POP HL                         ; ROM 01D20: e1
    LD DE,$d100                    ; ROM 01D21: 1100d1
    LD BC,$10                      ; ROM 01D24: 011000
    LDIR                           ; ROM 01D27: edb0
    EXX                            ; ROM 01D29: d9
    LD A,C                         ; ROM 01D2A: 79
    ADD A,A                        ; ROM 01D2B: 87
    RL B                           ; ROM 01D2C: cb10
    ADD A,A                        ; ROM 01D2E: 87
    RL B                           ; ROM 01D2F: cb10
    ADD A,A                        ; ROM 01D31: 87
    RL B                           ; ROM 01D32: cb10
    PUSH DE                        ; ROM 01D34: d5
    EXX                            ; ROM 01D35: d9
    POP DE                         ; ROM 01D36: d1
    DI                             ; ROM 01D37: f3
    RES 6,D                        ; ROM 01D38: cbb2
    LD C,$bf                       ; ROM 01D3A: 0ebf
    OUT (C),E                      ; ROM 01D3C: ed59
    OUT (C),D                      ; ROM 01D3E: ed51
    LD HL,$d110                    ; ROM 01D40: 2110d1
    LD BC,$40be                    ; ROM 01D43: 01be40
    INI                            ; ROM 01D46: eda2
    DJNZ $1d46                     ; ROM 01D48: 10fc
    SET 6,D                        ; ROM 01D4A: cbf2
    DEC C                          ; ROM 01D4C: 0d
    OUT (C),E                      ; ROM 01D4D: ed59
    OUT (C),D                      ; ROM 01D4F: ed51
    EI                             ; ROM 01D51: fb
    LD HL,$d113                    ; ROM 01D52: 2113d1
    LD DE,$d130                    ; ROM 01D55: 1130d1
    LD C,L                         ; ROM 01D58: 4d
    LD B,8                         ; ROM 01D59: 0608
    LD L,C                         ; ROM 01D5B: 69
    XOR A                          ; ROM 01D5C: af
    SLA (HL)                       ; ROM 01D5D: cb26
    RLA                            ; ROM 01D5F: 17
    DEC L                          ; ROM 01D60: 2d
    SLA (HL)                       ; ROM 01D61: cb26
    RLA                            ; ROM 01D63: 17
    DEC L                          ; ROM 01D64: 2d
    SLA (HL)                       ; ROM 01D65: cb26
    RLA                            ; ROM 01D67: 17
    DEC L                          ; ROM 01D68: 2d
    SLA (HL)                       ; ROM 01D69: cb26
    RLA                            ; ROM 01D6B: 17
    LD L,A                         ; ROM 01D6C: 6f
    LD A,(HL)                      ; ROM 01D6D: 7e
    LD (DE),A                      ; ROM 01D6E: 12
    INC E                          ; ROM 01D6F: 1c
    DJNZ $1d5b                     ; ROM 01D70: 10e9
    LD L,E                         ; ROM 01D72: 6b
    LD B,8                         ; ROM 01D73: 0608
    DEC L                          ; ROM 01D75: 2d
    SRL (HL)                       ; ROM 01D76: cb3e
    RRA                            ; ROM 01D78: 1f
    DJNZ $1d75                     ; ROM 01D79: 10fa
    OUT ($00be),A                  ; ROM 01D7B: d3be
    LD B,8                         ; ROM 01D7D: 0608
    SRL (HL)                       ; ROM 01D7F: cb3e
    RLA                            ; ROM 01D81: 17
    INC L                          ; ROM 01D82: 2c
    DJNZ $1d7f                     ; ROM 01D83: 10fa
    OUT ($00be),A                  ; ROM 01D85: d3be
    LD B,8                         ; ROM 01D87: 0608
    DEC L                          ; ROM 01D89: 2d
    SRL (HL)                       ; ROM 01D8A: cb3e
    RRA                            ; ROM 01D8C: 1f
    DJNZ $1d89                     ; ROM 01D8D: 10fa
    OUT ($00be),A                  ; ROM 01D8F: d3be
    LD B,8                         ; ROM 01D91: 0608
    SRL (HL)                       ; ROM 01D93: cb3e
    RLA                            ; ROM 01D95: 17
    INC L                          ; ROM 01D96: 2c
    DJNZ $1d93                     ; ROM 01D97: 10fa
    OUT ($00be),A                  ; ROM 01D99: d3be
    LD A,C                         ; ROM 01D9B: 79
    ADD A,4                        ; ROM 01D9C: c604
    LD C,A                         ; ROM 01D9E: 4f
    CP $33                         ; ROM 01D9F: fe33
    JP nz,$1d59                    ; ROM 01DA1: c2591d
    EXX                            ; ROM 01DA4: d9
    LD A,$20                       ; ROM 01DA5: 3e20
    ADD A,E                        ; ROM 01DA7: 83
    LD E,A                         ; ROM 01DA8: 5f
    JR nc,$1dac                    ; ROM 01DA9: 3001
    INC D                          ; ROM 01DAB: 14
    DJNZ $1d34                     ; ROM 01DAC: 1086
    POP HL                         ; ROM 01DAE: e1
    POP DE                         ; ROM 01DAF: d1
    POP BC                         ; ROM 01DB0: c1
    RET                            ; ROM 01DB1: c9
    db $00,$01,$0C,$03,$04,$0B,$06,$07,$0D,$09,$0A,$0B,$0C,$0D,$0E,$0F ; ROM 01DB2
    db $00,$01,$09,$03,$04,$0B,$06,$07,$0A,$09,$0A,$0B,$0C,$0D,$0E,$0F ; ROM 01DC2
    db $01,$01,$02,$03,$04,$05,$06,$07,$08,$09,$0A,$0B,$0C,$0D,$0E,$0F ; ROM 01DD2
    CALL $2279                     ; ROM 01DE2: cd7922
    CALL $1e4e                     ; ROM 01DE5: cd4e1e
    CALL $229c                     ; ROM 01DE8: cd9c22
    LD HL,$1e20                    ; ROM 01DEB: 21201e
    LD DE,$dcb0                    ; ROM 01DEE: 11b0dc
    LD BC,$10                      ; ROM 01DF1: 011000
    LDIR                           ; ROM 01DF4: edb0
    LD A,($c0f1)                   ; ROM 01DF6: 3af1c0
    ADD A,A                        ; ROM 01DF9: 87
    LD HL,$1e2e                    ; ROM 01DFA: 212e1e
    RST 8                          ; ROM 01DFD: cf
    LD ($dcb6),HL                  ; ROM 01DFE: 22b6dc
    LD A,($c0bf)                   ; ROM 01E01: 3abfc0
    OR A                           ; ROM 01E04: b7
    JR z,$1e14                     ; ROM 01E05: 280d
    LD A,($c02f)                   ; ROM 01E07: 3a2fc0
    RRCA                           ; ROM 01E0A: 0f
    RRCA                           ; ROM 01E0B: 0f
    JR c,$1e14                     ; ROM 01E0C: 3806
    LD HL,$116                     ; ROM 01E0E: 211601
    LD ($dcb6),HL                  ; ROM 01E11: 22b6dc
    LD A,($c02f)                   ; ROM 01E14: 3a2fc0
    AND 2                          ; ROM 01E17: e602
    JR nz,$1e1c                    ; ROM 01E19: 2001
    INC A                          ; ROM 01E1B: 3c
    LD ($dcbf),A                   ; ROM 01E1C: 32bfdc
    RET                            ; ROM 01E1F: c9
    db $00,$00,$1B,$3F,$1F,$06,$38,$30,$03,$0D,$08,$14,$3C,$30,$2A,$00 ; ROM 01E20
    db $38,$30,$2B,$13,$3D,$39,$16,$01 ; ROM 01E30
    LD A,$95                       ; ROM 01E38: 3e95
    LD ($de08),A                   ; ROM 01E3A: 3208de
    LD A,1                         ; ROM 01E3D: 3e01
    JR $1e48                       ; ROM 01E3F: 1807
    db $3E,$95,$32,$08,$DE,$3E,$03 ; ROM 01E41
    CALL $1e9c                     ; ROM 01E48: cd9c1e
    JP $0b92                       ; ROM 01E4B: c3920b
    LD A,4                         ; ROM 01E4E: 3e04
    LD ($ffff),A                   ; ROM 01E50: 32ffff
    LD HL,$a6ab                    ; ROM 01E53: 21aba6
    LD DE,$db00                    ; ROM 01E56: 1100db
    CALL $0bfe                     ; ROM 01E59: cdfe0b
    LD HL,$db00                    ; ROM 01E5C: 2100db
    LD B,$80                       ; ROM 01E5F: 0680
    LD A,(HL)                      ; ROM 01E61: 7e
    ADD A,$d0                      ; ROM 01E62: c6d0
    LD (HL),A                      ; ROM 01E64: 77
    INC HL                         ; ROM 01E65: 23
    LD A,(HL)                      ; ROM 01E66: 7e
    OR $18                         ; ROM 01E67: f618
    LD (HL),A                      ; ROM 01E69: 77
    INC HL                         ; ROM 01E6A: 23
    DJNZ $1e61                     ; ROM 01E6B: 10f4
    LD HL,$1e91                    ; ROM 01E6D: 21911e
    LD DE,$db58                    ; ROM 01E70: 1158db
    LD BC,$402                     ; ROM 01E73: 010204
    CALL $7357                     ; ROM 01E76: cd5773
    LD B,4                         ; ROM 01E79: 0604
    PUSH BC                        ; ROM 01E7B: c5
    LD A,B                         ; ROM 01E7C: 78
    CALL $1ea1                     ; ROM 01E7D: cda11e
    POP BC                         ; ROM 01E80: c1
    DJNZ $1e7b                     ; ROM 01E81: 10f8
    LD HL,$db01                    ; ROM 01E83: 2101db
    LD B,$80                       ; ROM 01E86: 0680
    LD A,(HL)                      ; ROM 01E88: 7e
    OR $40                         ; ROM 01E89: f640
    LD (HL),A                      ; ROM 01E8B: 77
    INC HL                         ; ROM 01E8C: 23
    INC HL                         ; ROM 01E8D: 23
    DJNZ $1e88                     ; ROM 01E8E: 10f8
    RET                            ; ROM 01E90: c9
    db $EC,$18,$ED,$18,$EE,$18,$EF,$18 ; ROM 01E91
    LD A,($c02f)                   ; ROM 01E99: 3a2fc0
    OR $80                         ; ROM 01E9C: f680
    LD ($c045),A                   ; ROM 01E9E: 3245c0
    AND 3                          ; ROM 01EA1: e603
    ADD A,A                        ; ROM 01EA3: 87
    LD HL,$1ead                    ; ROM 01EA4: 21ad1e
    PUSH IX                        ; ROM 01EA7: dde5
    RST $18                        ; ROM 01EA9: df
    POP IX                         ; ROM 01EAA: dde1
    RET                            ; ROM 01EAC: c9
    db $B5,$1E,$EE,$1E,$25,$1F,$4B,$1F ; ROM 01EAD
    LD HL,$c0cf                    ; ROM 01EB5: 21cfc0
    LD IY,$1edc                    ; ROM 01EB8: fd21dc1e
    LD B,9                         ; ROM 01EBC: 0609
    BIT 7,(HL)                     ; ROM 01EBE: cb7e
    JR z,$1ed4                     ; ROM 01EC0: 2812
    db $16,$DB,$FD,$5E,$01,$FD,$7E,$00,$D5,$DD,$E1,$DD,$77,$00,$DD,$36 ; ROM 01EC2
    db $01,$59 ; ROM 01ED2
    INC HL                         ; ROM 01ED4: 23
    INC IY                         ; ROM 01ED5: fd23
    INC IY                         ; ROM 01ED7: fd23
    DJNZ $1ebe                     ; ROM 01ED9: 10e3
    RET                            ; ROM 01EDB: c9
    db $85,$82,$83,$8E,$87,$86,$89,$8A,$82,$44,$88,$4C,$86,$06,$84,$0A ; ROM 01EDC
    db $8A,$48 ; ROM 01EEC
    LD HL,$db5e                    ; ROM 01EEE: 215edb
    LD DE,$198b                    ; ROM 01EF1: 118b19
    LD A,($c318)                   ; ROM 01EF4: 3a18c3
    LD C,A                         ; ROM 01EF7: 4f
    LD A,($c0da)                   ; ROM 01EF8: 3adac0
    RRCA                           ; ROM 01EFB: 0f
    RRCA                           ; ROM 01EFC: 0f
    RRCA                           ; ROM 01EFD: 0f
    AND $1f                        ; ROM 01EFE: e61f
    LD B,A                         ; ROM 01F00: 47
    LD A,C                         ; ROM 01F01: 79
    SUB 8                          ; ROM 01F02: d608
    LD C,A                         ; ROM 01F04: 4f
    JR c,$1f0e                     ; ROM 01F05: 3807
    LD (HL),E                      ; ROM 01F07: 73
    INC HL                         ; ROM 01F08: 23
    LD (HL),D                      ; ROM 01F09: 72
    INC HL                         ; ROM 01F0A: 23
    DJNZ $1f01                     ; ROM 01F0B: 10f4
    RET                            ; ROM 01F0D: c9
    ADD A,8                        ; ROM 01F0E: c608
    SRL A                          ; ROM 01F10: cb3f
    SUB $8f                        ; ROM 01F12: d68f
    NEG                            ; ROM 01F14: ed44
    LD (HL),A                      ; ROM 01F16: 77
    INC HL                         ; ROM 01F17: 23
    LD (HL),D                      ; ROM 01F18: 72
    INC HL                         ; ROM 01F19: 23
    DJNZ $1f1d                     ; ROM 01F1A: 1001
    RET                            ; ROM 01F1C: c9
    LD (HL),$8f                    ; ROM 01F1D: 368f
    INC HL                         ; ROM 01F1F: 23
    LD (HL),D                      ; ROM 01F20: 72
    INC HL                         ; ROM 01F21: 23
    DJNZ $1f1d                     ; ROM 01F22: 10f9
    RET                            ; ROM 01F24: c9
    LD HL,$dbde                    ; ROM 01F25: 21dedb
    LD DE,$1990                    ; ROM 01F28: 119019
    LD BC,($c0db)                  ; ROM 01F2B: ed4bdbc0
    LD A,B                         ; ROM 01F2F: 78
    RRCA                           ; ROM 01F30: 0f
    RRCA                           ; ROM 01F31: 0f
    RRCA                           ; ROM 01F32: 0f
    AND $1f                        ; ROM 01F33: e61f
    LD B,A                         ; ROM 01F35: 47
    LD A,C                         ; ROM 01F36: 79
    SUB 8                          ; ROM 01F37: d608
    LD C,A                         ; ROM 01F39: 4f
    JR c,$1f43                     ; ROM 01F3A: 3807
    LD (HL),E                      ; ROM 01F3C: 73
    INC HL                         ; ROM 01F3D: 23
    LD (HL),D                      ; ROM 01F3E: 72
    INC HL                         ; ROM 01F3F: 23
    DJNZ $1f36                     ; ROM 01F40: 10f4
    RET                            ; ROM 01F42: c9
    INC E                          ; ROM 01F43: 1c
    LD (HL),E                      ; ROM 01F44: 73
    INC HL                         ; ROM 01F45: 23
    LD (HL),D                      ; ROM 01F46: 72
    INC HL                         ; ROM 01F47: 23
    DJNZ $1f44                     ; ROM 01F48: 10fa
    RET                            ; ROM 01F4A: c9
    LD A,($c0dd)                   ; ROM 01F4B: 3addc0
    LD HL,$dbd0                    ; ROM 01F4E: 21d0db
    JP $085b                       ; ROM 01F51: c35b08
    LD A,($c033)                   ; ROM 01F54: 3a33c0
    OR A                           ; ROM 01F57: b7
    RET nz                         ; ROM 01F58: c0
    LD A,($c045)                   ; ROM 01F59: 3a45c0
    AND 3                          ; ROM 01F5C: e603
    RET z                          ; ROM 01F5E: c8
    RRCA                           ; ROM 01F5F: 0f
    RRCA                           ; ROM 01F60: 0f
    ADD A,2                        ; ROM 01F61: c602
    OUT ($00bf),A                  ; ROM 01F63: d3bf
    LD L,A                         ; ROM 01F65: 6f
    LD A,$7d                       ; ROM 01F66: 3e7d
    OUT ($00bf),A                  ; ROM 01F68: d3bf
    XOR A                          ; ROM 01F6A: af
    LD ($c045),A                   ; ROM 01F6B: 3245c0
    LD H,$db                       ; ROM 01F6E: 26db
    LD A,4                         ; ROM 01F70: 3e04
    LD ($ffff),A                   ; ROM 01F72: 32ffff
    JP $8088                       ; ROM 01F75: c38880
    db $3E,$A6,$32,$08,$DE,$11,$00,$78,$0E,$14,$41,$D5,$CD,$C6,$0B,$EF ; ROM 01F78
    db $3E,$FF,$D3,$BE,$79,$87,$83,$5F,$30,$01,$14,$3E,$18,$D3,$BE,$21 ; ROM 01F88
    db $00,$7E,$B7,$ED,$52,$30,$E8,$D1,$13,$13,$10,$DF,$C3,$24,$0B ; ROM 01F98
    LD HL,$18ff                    ; ROM 01FA7: 21ff18
    LD DE,$7800                    ; ROM 01FAA: 110078
    LD BC,$300                     ; ROM 01FAD: 010003
    CALL $0397                     ; ROM 01FB0: cd9703
    CALL $0aa4                     ; ROM 01FB3: cda40a
    LD IX,$2011                    ; ROM 01FB6: dd211120
    LD C,$10                       ; ROM 01FBA: 0e10
    CALL $0b92                     ; ROM 01FBC: cd920b
    LD E,(IX)                      ; ROM 01FBF: dd5e00
    LD D,(IX+1)                    ; ROM 01FC2: dd5601
    LD B,(IX+3)                    ; ROM 01FC5: dd4603
    INC DE                         ; ROM 01FC8: 13
    INC DE                         ; ROM 01FC9: 13
    CALL $2003                     ; ROM 01FCA: cd0320
    DJNZ $1fc8                     ; ROM 01FCD: 10f9
    LD B,(IX+2)                    ; ROM 01FCF: dd4602
    LD A,$40                       ; ROM 01FD2: 3e40
    ADD A,E                        ; ROM 01FD4: 83
    LD E,A                         ; ROM 01FD5: 5f
    JR nc,$1fd9                    ; ROM 01FD6: 3001
    INC D                          ; ROM 01FD8: 14
    CALL $2003                     ; ROM 01FD9: cd0320
    DJNZ $1fd2                     ; ROM 01FDC: 10f4
    LD B,(IX+3)                    ; ROM 01FDE: dd4603
    DEC DE                         ; ROM 01FE1: 1b
    DEC DE                         ; ROM 01FE2: 1b
    CALL $2003                     ; ROM 01FE3: cd0320
    DJNZ $1fe1                     ; ROM 01FE6: 10f9
    LD B,(IX+2)                    ; ROM 01FE8: dd4602
    LD A,$c0                       ; ROM 01FEB: 3ec0
    ADD A,E                        ; ROM 01FED: 83
    LD E,A                         ; ROM 01FEE: 5f
    JR c,$1ff2                     ; ROM 01FEF: 3801
    DEC D                          ; ROM 01FF1: 15
    CALL $2003                     ; ROM 01FF2: cd0320
    DJNZ $1feb                     ; ROM 01FF5: 10f4
    INC IX                         ; ROM 01FF7: dd23
    INC IX                         ; ROM 01FF9: dd23
    INC IX                         ; ROM 01FFB: dd23
    INC IX                         ; ROM 01FFD: dd23
    DEC C                          ; ROM 01FFF: 0d
    JR nz,$1fbc                    ; ROM 02000: 20ba
    RET                            ; ROM 02002: c9
    RST $28                        ; ROM 02003: ef
    LD HL,$5e00                    ; ROM 02004: 21005e
    ADD HL,DE                      ; ROM 02007: 19
    LD A,(HL)                      ; ROM 02008: 7e
    OUT ($00be),A                  ; ROM 02009: d3be
    INC HL                         ; ROM 0200B: 23
    LD A,(HL)                      ; ROM 0200C: 7e
    LD A,(HL)                      ; ROM 0200D: 7e
    OUT ($00be),A                  ; ROM 0200E: d3be
    RET                            ; ROM 02010: c9
    db $DE,$7A,$01,$01,$9C,$7A,$03,$03,$5A,$7A,$05,$05,$58,$7A,$05,$07 ; ROM 02011
    db $16,$7A,$07,$09,$D4,$79,$09,$0B,$92,$79,$0B,$0D,$90,$79,$0B,$0F ; ROM 02021
    db $4E,$79,$0D,$11,$0C,$79,$0F,$13,$CA,$78,$11,$15,$C8,$78,$11,$17 ; ROM 02031
    db $86,$78,$13,$19,$44,$78,$15,$1B,$02,$78,$17,$1D,$00,$78,$17,$1F ; ROM 02041
    LD A,($c313)                   ; ROM 02051: 3a13c3
    CP $10                         ; ROM 02054: fe10
    JP c,$2118                     ; ROM 02056: da1821
    CP $f1                         ; ROM 02059: fef1
    JP nc,$214b                    ; ROM 0205B: d24b21
    LD A,($c311)                   ; ROM 0205E: 3a11c3
    CP $10                         ; ROM 02061: fe10
    JR c,$206a                     ; ROM 02063: 3805
    CP $a1                         ; ROM 02065: fea1
    JR nc,$20ad                    ; ROM 02067: 3044
    RET                            ; ROM 02069: c9
    LD HL,$1000                    ; ROM 0206A: 210010
    LD ($c310),HL                  ; ROM 0206D: 2210c3
    CALL $21a1                     ; ROM 02070: cda121
    CALL $2099                     ; ROM 02073: cd9920
    LD A,$f0                       ; ROM 02076: 3ef0
    CALL $21c5                     ; ROM 02078: cdc521
    CALL $2260                     ; ROM 0207B: cd6022
    CALL $2099                     ; ROM 0207E: cd9920
    LD HL,$d5c0                    ; ROM 02081: 21c0d5
    LD DE,$ffc0                    ; ROM 02084: 11c0ff
    LD BC,$1408                    ; ROM 02087: 010814
    CALL $2237                     ; ROM 0208A: cd3722
    CALL $20f8                     ; ROM 0208D: cdf820
    ADD HL,DE                      ; ROM 02090: 19
    DJNZ $208a                     ; ROM 02091: 10f7
    LD HL,$a000                    ; ROM 02093: 2100a0
    LD ($c310),HL                  ; ROM 02096: 2210c3
    LD HL,$d100                    ; ROM 02099: 2100d1
    LD DE,$d600                    ; ROM 0209C: 1100d6
    LD BC,$500                     ; ROM 0209F: 010005
    LD A,(DE)                      ; ROM 020A2: 1a
    LDI                            ; ROM 020A3: eda0
    DEC HL                         ; ROM 020A5: 2b
    LD (HL),A                      ; ROM 020A6: 77
    INC HL                         ; ROM 020A7: 23
    LD A,B                         ; ROM 020A8: 78
    OR C                           ; ROM 020A9: b1
    JR nz,$20a2                    ; ROM 020AA: 20f6
    RET                            ; ROM 020AC: c9
    LD HL,$a000                    ; ROM 020AD: 2100a0
    LD ($c310),HL                  ; ROM 020B0: 2210c3
    CALL $21a1                     ; ROM 020B3: cda121
    CALL $2099                     ; ROM 020B6: cd9920
    LD A,$10                       ; ROM 020B9: 3e10
    CALL $21c5                     ; ROM 020BB: cdc521
    CALL $2260                     ; ROM 020BE: cd6022
    LD HL,$d140                    ; ROM 020C1: 2140d1
    LD DE,$40                      ; ROM 020C4: 114000
    LD BC,$14f8                    ; ROM 020C7: 01f814
    CALL $2237                     ; ROM 020CA: cd3722
    CALL $20f8                     ; ROM 020CD: cdf820
    ADD HL,DE                      ; ROM 020D0: 19
    DJNZ $20ca                     ; ROM 020D1: 10f7
    LD HL,$1000                    ; ROM 020D3: 210010
    LD ($c310),HL                  ; ROM 020D6: 2210c3
    RET                            ; ROM 020D9: c9
    LD A,$d0                       ; ROM 020DA: 3ed0
    LD ($dd40),A                   ; ROM 020DC: 3240dd
    LD HL,$8ff                     ; ROM 020DF: 21ff08
    JR $20e7                       ; ROM 020E2: 1803
    db $21,$FF,$00 ; ROM 020E4
    LD ($d600),HL                  ; ROM 020E7: 2200d6
    LD HL,$d600                    ; ROM 020EA: 2100d6
    LD DE,$d602                    ; ROM 020ED: 1102d6
    LD BC,$4fe                     ; ROM 020F0: 01fe04
    LDIR                           ; ROM 020F3: edb0
    LD HL,$d600                    ; ROM 020F5: 2100d6
    PUSH AF                        ; ROM 020F8: f5
    PUSH BC                        ; ROM 020F9: c5
    PUSH DE                        ; ROM 020FA: d5
    PUSH HL                        ; ROM 020FB: e5
    CALL $0bc6                     ; ROM 020FC: cdc60b
    XOR A                          ; ROM 020FF: af
    OUT ($00bf),A                  ; ROM 02100: d3bf
    LD A,$78                       ; ROM 02102: 3e78
    OUT ($00bf),A                  ; ROM 02104: d3bf
    LD BC,$be                      ; ROM 02106: 01be00
    LD E,10                        ; ROM 02109: 1e0a
    OUTI                           ; ROM 0210B: eda3
    DJNZ $210b                     ; ROM 0210D: 10fc
    DEC E                          ; ROM 0210F: 1d
    JP nz,$210b                    ; ROM 02110: c20b21
    POP HL                         ; ROM 02113: e1
    POP DE                         ; ROM 02114: d1
    POP BC                         ; ROM 02115: c1
    POP AF                         ; ROM 02116: f1
    RET                            ; ROM 02117: c9
    LD HL,$1000                    ; ROM 02118: 210010
    LD ($c312),HL                  ; ROM 0211B: 2212c3
    CALL $21a1                     ; ROM 0211E: cda121
    CALL $2099                     ; ROM 02121: cd9920
    LD A,$ff                       ; ROM 02124: 3eff
    CALL $21cb                     ; ROM 02126: cdcb21
    CALL $2260                     ; ROM 02129: cd6022
    CALL $0240                     ; ROM 0212C: cd4002
    LD DE,$783e                    ; ROM 0212F: 113e78
    LD BC,$2008                    ; ROM 02132: 010820
    CALL $224b                     ; ROM 02135: cd4b22
    LD A,E                         ; ROM 02138: 7b
    NEG                            ; ROM 02139: ed44
    CALL $217d                     ; ROM 0213B: cd7d21
    DEC E                          ; ROM 0213E: 1d
    DEC E                          ; ROM 0213F: 1d
    DJNZ $2135                     ; ROM 02140: 10f3
    LD HL,$f000                    ; ROM 02142: 2100f0
    LD ($c312),HL                  ; ROM 02145: 2212c3
    JP $0227                       ; ROM 02148: c32702
    LD HL,$f000                    ; ROM 0214B: 2100f0
    LD ($c312),HL                  ; ROM 0214E: 2212c3
    CALL $21a1                     ; ROM 02151: cda121
    CALL $2099                     ; ROM 02154: cd9920
    LD A,1                         ; ROM 02157: 3e01
    CALL $21cb                     ; ROM 02159: cdcb21
    CALL $2260                     ; ROM 0215C: cd6022
    CALL $0240                     ; ROM 0215F: cd4002
    LD DE,$7800                    ; ROM 02162: 110078
    LD BC,$20f8                    ; ROM 02165: 01f820
    CALL $224b                     ; ROM 02168: cd4b22
    LD A,E                         ; ROM 0216B: 7b
    CPL                            ; ROM 0216C: 2f
    CALL $217d                     ; ROM 0216D: cd7d21
    INC E                          ; ROM 02170: 1c
    INC E                          ; ROM 02171: 1c
    DJNZ $2168                     ; ROM 02172: 10f4
    LD HL,$1000                    ; ROM 02174: 210010
    LD ($c312),HL                  ; ROM 02177: 2212c3
    JP $0227                       ; ROM 0217A: c32702
    PUSH BC                        ; ROM 0217D: c5
    PUSH DE                        ; ROM 0217E: d5
    AND $3e                        ; ROM 0217F: e63e
    ADD A,A                        ; ROM 02181: 87
    ADD A,A                        ; ROM 02182: 87
    LD ($c018),A                   ; ROM 02183: 3218c0
    CALL $0bc6                     ; ROM 02186: cdc60b
    LD BC,$28be                    ; ROM 02189: 01be28
    RST $28                        ; ROM 0218C: ef
    LD HL,$5e00                    ; ROM 0218D: 21005e
    ADD HL,DE                      ; ROM 02190: 19
    OUTI                           ; ROM 02191: eda3
    LD A,$40                       ; ROM 02193: 3e40
    ADD A,E                        ; ROM 02195: 83
    LD E,A                         ; ROM 02196: 5f
    JR nc,$219a                    ; ROM 02197: 3001
    INC D                          ; ROM 02199: 14
    OUTI                           ; ROM 0219A: eda3
    JR nz,$218c                    ; ROM 0219C: 20ee
    POP DE                         ; ROM 0219E: d1
    POP BC                         ; ROM 0219F: c1
    RET                            ; ROM 021A0: c9
    LD A,10                        ; ROM 021A1: 3e0a
    LD ($c01d),A                   ; ROM 021A3: 321dc0
    CALL $18e9                     ; ROM 021A6: cde918
    LD HL,0                        ; ROM 021A9: 210000
    LD ($c314),HL                  ; ROM 021AC: 2214c3
    LD ($c316),HL                  ; ROM 021AF: 2216c3
    XOR A                          ; ROM 021B2: af
    LD ($c304),A                   ; ROM 021B3: 3204c3
    LD HL,$c333                    ; ROM 021B6: 2133c3
    LD DE,$30                      ; ROM 021B9: 113000
    LD B,$1f                       ; ROM 021BC: 061f
    LD (HL),A                      ; ROM 021BE: 77
    ADD HL,DE                      ; ROM 021BF: 19
    DJNZ $21be                     ; ROM 021C0: 10fc
    JP $0938                       ; ROM 021C2: c33809
    LD HL,$c0b9                    ; ROM 021C5: 21b9c0
    ADD A,(HL)                     ; ROM 021C8: 86
    JR $21d6                       ; ROM 021C9: 180b
    LD HL,$c0b9                    ; ROM 021CB: 21b9c0
    ADD A,(HL)                     ; ROM 021CE: 86
    AND 15                         ; ROM 021CF: e60f
    LD C,A                         ; ROM 021D1: 4f
    LD A,(HL)                      ; ROM 021D2: 7e
    AND $f0                        ; ROM 021D3: e6f0
    OR C                           ; ROM 021D5: b1
    LD C,A                         ; ROM 021D6: 4f
    LD A,($c040)                   ; ROM 021D7: 3a40c0
    OR A                           ; ROM 021DA: b7
    JR nz,$21e7                    ; ROM 021DB: 200a
    LD A,(HL)                      ; ROM 021DD: 7e
    CP $77                         ; ROM 021DE: fe77
    JR nz,$21e7                    ; ROM 021E0: 2005
    LD A,C                         ; ROM 021E2: 79
    CP $76                         ; ROM 021E3: fe76
    JR nz,$21ea                    ; ROM 021E5: 2003
    LD (HL),C                      ; ROM 021E7: 71
    JR $220d                       ; ROM 021E8: 1823
    LD A,($c06c)                   ; ROM 021EA: 3a6cc0
    INC A                          ; ROM 021ED: 3c
    LD ($c06c),A                   ; ROM 021EE: 326cc0
    ADD A,A                        ; ROM 021F1: 87
    LD HL,$21f6                    ; ROM 021F2: 21f621
    JP $0018                       ; ROM 021F5: c31800
    db $02,$22,$12,$22,$18,$22,$25,$22,$2B,$22,$79,$FE,$78,$20,$06,$3A ; ROM 021F8
    db $11,$C3,$FE,$60,$D0 ; ROM 02208
    XOR A                          ; ROM 0220D: af
    LD ($c06c),A                   ; ROM 0220E: 326cc0
    RET                            ; ROM 02211: c9
    db $79,$FE,$67,$20,$F6,$C9,$79,$FE,$78,$20,$F0,$3A,$11,$C3,$FE,$60 ; ROM 02212
    db $30,$E9,$C9,$79,$FE,$87,$20,$E3,$C9,$79,$FE,$67,$20,$DD,$2A,$B9 ; ROM 02222
    db $C0,$6F,$C3,$E2,$18 ; ROM 02232
    LD A,B                         ; ROM 02237: 78
    CP 3                           ; ROM 02238: fe03
    RET c                          ; ROM 0223A: d8
    PUSH HL                        ; ROM 0223B: e5
    LD HL,$dd40                    ; ROM 0223C: 2140dd
    LD A,(HL)                      ; ROM 0223F: 7e
    CP $d0                         ; ROM 02240: fed0
    JR z,$2249                     ; ROM 02242: 2805
    ADD A,C                        ; ROM 02244: 81
    LD (HL),A                      ; ROM 02245: 77
    INC HL                         ; ROM 02246: 23
    JR $223f                       ; ROM 02247: 18f6
    POP HL                         ; ROM 02249: e1
    RET                            ; ROM 0224A: c9
    LD A,B                         ; ROM 0224B: 78
    CP 5                           ; ROM 0224C: fe05
    RET c                          ; ROM 0224E: d8
    PUSH HL                        ; ROM 0224F: e5
    PUSH BC                        ; ROM 02250: c5
    LD HL,$dd80                    ; ROM 02251: 2180dd
    LD B,$10                       ; ROM 02254: 0610
    LD A,C                         ; ROM 02256: 79
    ADD A,(HL)                     ; ROM 02257: 86
    LD (HL),A                      ; ROM 02258: 77
    INC HL                         ; ROM 02259: 23
    INC HL                         ; ROM 0225A: 23
    DJNZ $2256                     ; ROM 0225B: 10f9
    POP BC                         ; ROM 0225D: c1
    POP HL                         ; ROM 0225E: e1
    RET                            ; ROM 0225F: c9
    XOR A                          ; ROM 02260: af
    LD ($c0ad),A                   ; ROM 02261: 32adc0
    LD ($c0ac),A                   ; ROM 02264: 32acc0
    LD A,5                         ; ROM 02267: 3e05
    LD ($ffff),A                   ; ROM 02269: 32ffff
    CALL $be78                     ; ROM 0226C: cd78be
    LD A,($c072)                   ; ROM 0226F: 3a72c0
    OR A                           ; ROM 02272: b7
    CALL nz,$0b95                  ; ROM 02273: c4950b
    CALL $190b                     ; ROM 02276: cd0b19
    PUSH AF                        ; ROM 02279: f5
    PUSH BC                        ; ROM 0227A: c5
    PUSH DE                        ; ROM 0227B: d5
    PUSH HL                        ; ROM 0227C: e5
    LD HL,$d600                    ; ROM 0227D: 2100d6
    LD C,0                         ; ROM 02280: 0e00
    LD B,0                         ; ROM 02282: 0600
    CALL $22e2                     ; ROM 02284: cde222
    LD (HL),E                      ; ROM 02287: 73
    INC HL                         ; ROM 02288: 23
    LD (HL),D                      ; ROM 02289: 72
    INC HL                         ; ROM 0228A: 23
    INC B                          ; ROM 0228B: 04
    LD A,B                         ; ROM 0228C: 78
    CP $20                         ; ROM 0228D: fe20
    JR c,$2284                     ; ROM 0228F: 38f3
    INC C                          ; ROM 02291: 0c
    LD A,C                         ; ROM 02292: 79
    CP $14                         ; ROM 02293: fe14
    JR c,$2282                     ; ROM 02295: 38eb
    POP HL                         ; ROM 02297: e1
    POP DE                         ; ROM 02298: d1
    POP BC                         ; ROM 02299: c1
    POP AF                         ; ROM 0229A: f1
    RET                            ; ROM 0229B: c9
    PUSH AF                        ; ROM 0229C: f5
    PUSH BC                        ; ROM 0229D: c5
    PUSH DE                        ; ROM 0229E: d5
    PUSH HL                        ; ROM 0229F: e5
    CALL $0b95                     ; ROM 022A0: cd950b
    DI                             ; ROM 022A3: f3
    XOR A                          ; ROM 022A4: af
    OUT ($00bf),A                  ; ROM 022A5: d3bf
    LD A,$78                       ; ROM 022A7: 3e78
    OUT ($00bf),A                  ; ROM 022A9: d3bf
    LD HL,$d600                    ; ROM 022AB: 2100d6
    LD BC,$be                      ; ROM 022AE: 01be00
    LD E,12                        ; ROM 022B1: 1e0c
    OUTI                           ; ROM 022B3: eda3
    DJNZ $22b3                     ; ROM 022B5: 10fc
    DEC E                          ; ROM 022B7: 1d
    JP nz,$22b3                    ; ROM 022B8: c2b322
    IN A,($00bf)                   ; ROM 022BB: dbbf
    EI                             ; ROM 022BD: fb
    POP HL                         ; ROM 022BE: e1
    POP DE                         ; ROM 022BF: d1
    POP BC                         ; ROM 022C0: c1
    POP AF                         ; ROM 022C1: f1
    RET                            ; ROM 022C2: c9
    db $CD,$95,$0B,$F3,$AF,$D3,$BF,$3E,$78,$D3,$BF,$21,$00,$D6,$01,$BE ; ROM 022C3
    db $00,$1E,$0A,$ED,$A3,$10,$FC,$1D,$C2,$D6,$22,$DB,$BF,$FB,$C9 ; ROM 022D3
    PUSH HL                        ; ROM 022E2: e5
    LD E,B                         ; ROM 022E3: 58
    SRL E                          ; ROM 022E4: cb3b
    LD A,C                         ; ROM 022E6: 79
    AND $fe                        ; ROM 022E7: e6fe
    ADD A,A                        ; ROM 022E9: 87
    ADD A,A                        ; ROM 022EA: 87
    ADD A,A                        ; ROM 022EB: 87
    ADD A,E                        ; ROM 022EC: 83
    LD E,A                         ; ROM 022ED: 5f
    LD D,0                         ; ROM 022EE: 1600
    LD HL,$dc00                    ; ROM 022F0: 2100dc
    ADD HL,DE                      ; ROM 022F3: 19
    LD L,(HL)                      ; ROM 022F4: 6e
    LD H,D                         ; ROM 022F5: 62
    ADD HL,HL                      ; ROM 022F6: 29
    ADD HL,HL                      ; ROM 022F7: 29
    ADD HL,HL                      ; ROM 022F8: 29
    LD DE,$c900                    ; ROM 022F9: 1100c9
    BIT 0,C                        ; ROM 022FC: cb41
    JR z,$2302                     ; ROM 022FE: 2802
    SET 2,E                        ; ROM 02300: cbd3
    BIT 0,B                        ; ROM 02302: cb40
    JR z,$2308                     ; ROM 02304: 2802
    SET 1,E                        ; ROM 02306: cbcb
    ADD HL,DE                      ; ROM 02308: 19
    LD E,(HL)                      ; ROM 02309: 5e
    INC HL                         ; ROM 0230A: 23
    LD D,(HL)                      ; ROM 0230B: 56
    POP HL                         ; ROM 0230C: e1
    RET                            ; ROM 0230D: c9
    LD A,(IX+$11)                  ; ROM 0230E: dd7e11
    ADD A,C                        ; ROM 02311: 81
    AND $f8                        ; ROM 02312: e6f8
    LD L,A                         ; ROM 02314: 6f
    LD H,0                         ; ROM 02315: 2600
    ADD HL,HL                      ; ROM 02317: 29
    ADD HL,HL                      ; ROM 02318: 29
    ADD HL,HL                      ; ROM 02319: 29
    LD A,(IX+$13)                  ; ROM 0231A: dd7e13
    ADD A,B                        ; ROM 0231D: 80
    RRCA                           ; ROM 0231E: 0f
    RRCA                           ; ROM 0231F: 0f
    AND $3e                        ; ROM 02320: e63e
    ADD A,L                        ; ROM 02322: 85
    LD L,A                         ; ROM 02323: 6f
    JR nc,$2327                    ; ROM 02324: 3001
    INC H                          ; ROM 02326: 24
    LD DE,$d600                    ; ROM 02327: 1100d6
    ADD HL,DE                      ; ROM 0232A: 19
    LD E,(HL)                      ; ROM 0232B: 5e
    INC L                          ; ROM 0232C: 2c
    LD D,(HL)                      ; ROM 0232D: 56
    RET                            ; ROM 0232E: c9
    LD A,(IX+$13)                  ; ROM 0232F: dd7e13
    ADD A,B                        ; ROM 02332: 80
    AND $f0                        ; ROM 02333: e6f0
    RRCA                           ; ROM 02335: 0f
    RRCA                           ; ROM 02336: 0f
    RRCA                           ; ROM 02337: 0f
    RRCA                           ; ROM 02338: 0f
    LD L,A                         ; ROM 02339: 6f
    LD A,(IX+$11)                  ; ROM 0233A: dd7e11
    ADD A,C                        ; ROM 0233D: 81
    AND $f0                        ; ROM 0233E: e6f0
    OR L                           ; ROM 02340: b5
    LD L,A                         ; ROM 02341: 6f
    LD H,$dc                       ; ROM 02342: 26dc
    LD A,(HL)                      ; ROM 02344: 7e
    RET                            ; ROM 02345: c9
    LD HL,($c02f)                  ; ROM 02346: 2a2fc0
    LD A,($c046)                   ; ROM 02349: 3a46c0
    XOR L                          ; ROM 0234C: ad
    RRCA                           ; ROM 0234D: 0f
    RET c                          ; ROM 0234E: d8
    LD A,(IX+5)                    ; ROM 0234F: dd7e05
    OR A                           ; ROM 02352: b7
    RET nz                         ; ROM 02353: c0
    BIT 1,(IX+3)                   ; ROM 02354: ddcb034e
    RET z                          ; ROM 02358: c8
    LD A,2                         ; ROM 02359: 3e02
    LD ($ffff),A                   ; ROM 0235B: 32ffff
    LD A,(IX+$1b)                  ; ROM 0235E: dd7e1b
    ADD A,A                        ; ROM 02361: 87
    RET z                          ; ROM 02362: c8
    EXX                            ; ROM 02363: d9
    ADD A,A                        ; ROM 02364: 87
    LD L,A                         ; ROM 02365: 6f
    LD H,$81                       ; ROM 02366: 2681
    LD A,(IX+$13)                  ; ROM 02368: dd7e13
    ADD A,(HL)                     ; ROM 0236B: 86
    INC L                          ; ROM 0236C: 2c
    LD B,A                         ; ROM 0236D: 47
    ADD A,(HL)                     ; ROM 0236E: 86
    INC L                          ; ROM 0236F: 2c
    LD C,A                         ; ROM 02370: 4f
    LD A,(IX+$11)                  ; ROM 02371: dd7e11
    ADD A,(HL)                     ; ROM 02374: 86
    INC L                          ; ROM 02375: 2c
    LD D,A                         ; ROM 02376: 57
    ADD A,(HL)                     ; ROM 02377: 86
    LD E,A                         ; ROM 02378: 5f
    EXX                            ; ROM 02379: d9
    LD HL,$2404                    ; ROM 0237A: 210424
    LD A,($c046)                   ; ROM 0237D: 3a46c0
    LD E,A                         ; ROM 02380: 5f
    LD D,0                         ; ROM 02381: 1600
    ADD HL,DE                      ; ROM 02383: 19
    LD E,(HL)                      ; ROM 02384: 5e
    LD HL,$2424                    ; ROM 02385: 212424
    ADD HL,DE                      ; ROM 02388: 19
    LD E,(HL)                      ; ROM 02389: 5e
    INC HL                         ; ROM 0238A: 23
    LD D,(HL)                      ; ROM 0238B: 56
    INC HL                         ; ROM 0238C: 23
    PUSH DE                        ; ROM 0238D: d5
    POP IY                         ; ROM 0238E: fde1
    LD B,(HL)                      ; ROM 02390: 46
    LD DE,$30                      ; ROM 02391: 113000
    EXX                            ; ROM 02394: d9
    LD A,(IY)                      ; ROM 02395: fd7e00
    OR A                           ; ROM 02398: b7
    JR z,$23d0                     ; ROM 02399: 2835
    LD A,(IY+6)                    ; ROM 0239B: fd7e06
    OR A                           ; ROM 0239E: b7
    JR nz,$23d0                    ; ROM 0239F: 202f
    BIT 1,(IY+3)                   ; ROM 023A1: fdcb034e
    JR z,$23d0                     ; ROM 023A5: 2829
    LD A,(IY+$1c)                  ; ROM 023A7: fd7e1c
    ADD A,A                        ; ROM 023AA: 87
    JR z,$23d0                     ; ROM 023AB: 2823
    ADD A,A                        ; ROM 023AD: 87
    LD L,A                         ; ROM 023AE: 6f
    LD A,(HL)                      ; ROM 023AF: 7e
    INC L                          ; ROM 023B0: 2c
    ADD A,(IY+$13)                 ; ROM 023B1: fd8613
    JR nc,$23d0                    ; ROM 023B4: 301a
    CP C                           ; ROM 023B6: b9
    JR nc,$23d0                    ; ROM 023B7: 3017
    ADD A,(HL)                     ; ROM 023B9: 86
    JR c,$23d0                     ; ROM 023BA: 3814
    CP B                           ; ROM 023BC: b8
    JR c,$23d0                     ; ROM 023BD: 3811
    INC L                          ; ROM 023BF: 2c
    LD A,(HL)                      ; ROM 023C0: 7e
    ADD A,(IY+$11)                 ; ROM 023C1: fd8611
    JR nc,$23d0                    ; ROM 023C4: 300a
    CP E                           ; ROM 023C6: bb
    JR nc,$23d0                    ; ROM 023C7: 3007
    INC L                          ; ROM 023C9: 2c
    ADD A,(HL)                     ; ROM 023CA: 86
    JR c,$23d0                     ; ROM 023CB: 3803
    CP D                           ; ROM 023CD: ba
    JR nc,$23d6                    ; ROM 023CE: 3006
    EXX                            ; ROM 023D0: d9
    ADD IY,DE                      ; ROM 023D1: fd19
    DJNZ $2394                     ; ROM 023D3: 10bf
    RET                            ; ROM 023D5: c9
    PUSH IY                        ; ROM 023D6: fde5
    POP HL                         ; ROM 023D8: e1
    LD A,(IX)                      ; ROM 023D9: dd7e00
    CP 2                           ; ROM 023DC: fe02
    JR nz,$23e7                    ; ROM 023DE: 2007
    LD A,(IY)                      ; ROM 023E0: fd7e00
    CP $10                         ; ROM 023E3: fe10
    JR c,$23f9                     ; ROM 023E5: 3812
    LD A,(IY+$19)                  ; ROM 023E7: fd7e19
    SUB (IX+$1a)                   ; ROM 023EA: dd961a
    JR z,$23f1                     ; ROM 023ED: 2802
    JR nc,$23f3                    ; ROM 023EF: 3002
    LD A,2                         ; ROM 023F1: 3e02
    ADD A,(IX+$1d)                 ; ROM 023F3: dd861d
    LD (IX+$1d),A                  ; ROM 023F6: dd771d
    LD (IX+$1e),L                  ; ROM 023F9: dd751e
    LD (IX+$1f),H                  ; ROM 023FC: dd741f
    SET 2,(IY+3)                   ; ROM 023FF: fdcb03d6
    RET                            ; ROM 02403: c9
    db $00,$03,$03,$03,$03,$03,$03,$03,$03,$06,$06,$06,$06,$06,$06,$06 ; ROM 02404
    db $09,$09,$09,$09,$09,$09,$09,$09,$0C,$0C,$0C,$0C,$0C,$0C,$0C,$0C ; ROM 02414
    db $B0,$C4,$17,$B0,$C4,$07,$00,$C3,$01,$00,$C3,$09,$00,$C3,$09 ; ROM 02424
    LD HL,$c300                    ; ROM 02433: 2100c3
    LD DE,$c301                    ; ROM 02436: 1101c3
    LD BC,$5ff                     ; ROM 02439: 01ff05
    LD (HL),0                      ; ROM 0243C: 3600
    LDIR                           ; ROM 0243E: edb0
    XOR A                          ; ROM 02440: af
    LD ($c0df),A                   ; ROM 02441: 32dfc0
    LD ($c0dd),A                   ; ROM 02444: 32ddc0
    LD ($c0de),A                   ; ROM 02447: 32dec0
    LD A,$18                       ; ROM 0244A: 3e18
    LD ($c0da),A                   ; ROM 0244C: 32dac0
    LD ($c0dc),A                   ; ROM 0244F: 32dcc0
    LD ($c318),A                   ; ROM 02452: 3218c3
    LD ($c0db),A                   ; ROM 02455: 32dbc0
    LD A,1                         ; ROM 02458: 3e01
    LD ($c0e0),A                   ; ROM 0245A: 32e0c0
    LD ($c0f1),A                   ; ROM 0245D: 32f1c0
    LD ($c0f2),A                   ; ROM 02460: 32f2c0
    CALL $1c97                     ; ROM 02463: cd971c
    LD HL,$95                      ; ROM 02466: 219500
    LD ($c0c0),HL                  ; ROM 02469: 22c0c0
    LD ($c0c2),HL                  ; ROM 0246C: 22c2c0
    LD A,($c011)                   ; ROM 0246F: 3a11c0
    AND $40                        ; ROM 02472: e640
    CALL nz,$0b12                  ; ROM 02474: c4120b
    LD HL,($c0c0)                  ; ROM 02477: 2ac0c0
    LD ($c0b9),HL                  ; ROM 0247A: 22b9c0
    LD A,H                         ; ROM 0247D: 7c
    OR A                           ; ROM 0247E: b7
    JR nz,$2484                    ; ROM 0247F: 2003
    LD ($c037),A                   ; ROM 02481: 3237c0
    CALL $3112                     ; ROM 02484: cd1231
    XOR A                          ; ROM 02487: af
    LD HL,$c040                    ; ROM 02488: 2140c0
    LD DE,$c041                    ; ROM 0248B: 1141c0
    LD BC,$4f                      ; ROM 0248E: 014f00
    LD (HL),A                      ; ROM 02491: 77
    LDIR                           ; ROM 02492: edb0
    LD ($c305),A                   ; ROM 02494: 3205c3
    LD ($c31d),A                   ; ROM 02497: 321dc3
    LD HL,$b701                    ; ROM 0249A: 2101b7
    LD DE,$7040                    ; ROM 0249D: 114070
    LD A,4                         ; ROM 024A0: 3e04
    CALL $0327                     ; ROM 024A2: cd2703
    LD HL,$a74c                    ; ROM 024A5: 214ca7
    LD DE,$5e00                    ; ROM 024A8: 11005e
    LD A,4                         ; ROM 024AB: 3e04
    CALL $0327                     ; ROM 024AD: cd2703
    CALL $7219                     ; ROM 024B0: cd1972
    CALL $722a                     ; ROM 024B3: cd2a72
    CALL $16d0                     ; ROM 024B6: cdd016
    CALL $190b                     ; ROM 024B9: cd0b19
    CALL $1de2                     ; ROM 024BC: cde21d
    CALL $24c5                     ; ROM 024BF: cdc524
    JP $1fa7                       ; ROM 024C2: c3a71f
    LD HL,$c090                    ; ROM 024C5: 2190c0
    LD DE,$c091                    ; ROM 024C8: 1191c0
    LD BC,$1f                      ; ROM 024CB: 011f00
    LD (HL),B                      ; ROM 024CE: 70
    LDIR                           ; ROM 024CF: edb0
    LD HL,$c4b0                    ; ROM 024D1: 21b0c4
    LD DE,$c4b1                    ; ROM 024D4: 11b1c4
    LD BC,$14f                     ; ROM 024D7: 014f01
    LD (HL),0                      ; ROM 024DA: 3600
    LDIR                           ; ROM 024DC: edb0
    CALL $1c15                     ; ROM 024DE: cd151c
    CALL $1780                     ; ROM 024E1: cd8017
    CALL $2c63                     ; ROM 024E4: cd632c
    CALL $5b20                     ; ROM 024E7: cd205b
    CALL $1caf                     ; ROM 024EA: cdaf1c
    LD A,12                        ; ROM 024ED: 3e0c
    LD ($c01d),A                   ; ROM 024EF: 321dc0
    RET                            ; ROM 024F2: c9
    CALL $0b95                     ; ROM 024F3: cd950b
    CALL $26b6                     ; ROM 024F6: cdb626
    CALL $0940                     ; ROM 024F9: cd4009
    CALL $1e99                     ; ROM 024FC: cd991e
    CALL $5b5a                     ; ROM 024FF: cd5a5b
    CALL $699c                     ; ROM 02502: cd9c69
    CALL $1df6                     ; ROM 02505: cdf61d
    CALL $2051                     ; ROM 02508: cd5120
    LD A,($c318)                   ; ROM 0250B: 3a18c3
    OR A                           ; ROM 0250E: b7
    RET z                          ; ROM 0250F: c8
    LD A,($c01d)                   ; ROM 02510: 3a1dc0
    CP 12                          ; ROM 02513: fe0c
    RET nz                         ; ROM 02515: c0
    LD A,($c021)                   ; ROM 02516: 3a21c0
    AND $10                        ; ROM 02519: e610
    JR nz,$2524                    ; ROM 0251B: 2007
    LD A,($c023)                   ; ROM 0251D: 3a23c0
    OR A                           ; ROM 02520: b7
    JR nz,$252a                    ; ROM 02521: 2007
    RET                            ; ROM 02523: c9
    LD A,$10                       ; ROM 02524: 3e10
    LD ($c01d),A                   ; ROM 02526: 321dc0
    RET                            ; ROM 02529: c9
    LD A,2                         ; ROM 0252A: 3e02
    LD ($c01d),A                   ; ROM 0252C: 321dc0
    RET                            ; ROM 0252F: c9
    db $2F,$83,$A0,$A1,$11,$12,$93,$94,$99,$B9,$7F,$80,$81,$82,$BA,$BB ; ROM 02530
    db $BC,$BD,$BE,$BF,$30,$25,$02,$01,$32,$25,$02,$02,$34,$25,$06,$03 ; ROM 02540
    db $3A,$25,$04,$04,$3E,$25,$06,$05,$FF,$0C,$0D,$0E,$0F,$10,$11,$FF ; ROM 02550
    db $78,$79,$7A,$7B,$7C,$7D,$7E,$7F,$FF,$58,$25,$01,$01,$59,$25,$06 ; ROM 02560
    db $02,$5F,$25,$01,$03,$60,$25,$08,$04,$68,$25,$01,$05 ; ROM 02570
    LD A,$8a                       ; ROM 0257D: 3e8a
    CALL $1cf8                     ; ROM 0257F: cdf81c
    CALL $263e                     ; ROM 02582: cd3e26
    LD HL,$267a                    ; ROM 02585: 217a26
    CALL $0c68                     ; ROM 02588: cd680c
    LD DE,$d7d6                    ; ROM 0258B: 11d6d7
    LD BC,$b06                     ; ROM 0258E: 01060b
    CALL $0877                     ; ROM 02591: cd7708
    LD HL,$268a                    ; ROM 02594: 218a26
    LD DE,$d818                    ; ROM 02597: 1118d8
    LD BC,$12                      ; ROM 0259A: 011200
    LDIR                           ; ROM 0259D: edb0
    LD DE,$d898                    ; ROM 0259F: 1198d8
    LD C,$12                       ; ROM 025A2: 0e12
    LDIR                           ; ROM 025A4: edb0
    LD DE,$d8d8                    ; ROM 025A6: 11d8d8
    LD C,8                         ; ROM 025A9: 0e08
    LDIR                           ; ROM 025AB: edb0
    LD A,1                         ; ROM 025AD: 3e01
    LD ($dcc0),A                   ; ROM 025AF: 32c0dc
    LD HL,($269c)                  ; ROM 025B2: 2a9c26
    LD DE,($26ae)                  ; ROM 025B5: ed5bae26
    LD A,($dcc0)                   ; ROM 025B9: 3ac0dc
    OR A                           ; ROM 025BC: b7
    JR nz,$25c0                    ; ROM 025BD: 2001
    EX DE,HL                       ; ROM 025BF: eb
    LD ($d898),HL                  ; ROM 025C0: 2298d8
    LD ($d8d8),DE                  ; ROM 025C3: ed53d8d8
    LD HL,($c034)                  ; ROM 025C7: 2a34c0
    LD (HL),2                      ; ROM 025CA: 3602
    INC L                          ; ROM 025CC: 2c
    LD (HL),6                      ; ROM 025CD: 3606
    INC L                          ; ROM 025CF: 2c
    LD (HL),11                     ; ROM 025D0: 360b
    INC L                          ; ROM 025D2: 2c
    LD (HL),$d6                    ; ROM 025D3: 36d6
    INC L                          ; ROM 025D5: 2c
    LD (HL),$d7                    ; ROM 025D6: 36d7
    INC L                          ; ROM 025D8: 2c
    LD ($c034),HL                  ; ROM 025D9: 2234c0
    CALL $0b95                     ; ROM 025DC: cd950b
    LD A,($dcc0)                   ; ROM 025DF: 3ac0dc
    LD BC,($c020)                  ; ROM 025E2: ed4b20c0
    BIT 0,B                        ; ROM 025E6: cb40
    JR z,$25ed                     ; ROM 025E8: 2803
    OR A                           ; ROM 025EA: b7
    JR z,$25f4                     ; ROM 025EB: 2807
    BIT 1,B                        ; ROM 025ED: cb48
    JR z,$25fe                     ; ROM 025EF: 280d
    OR A                           ; ROM 025F1: b7
    JR z,$25fe                     ; ROM 025F2: 280a
    XOR 1                          ; ROM 025F4: ee01
    LD ($dcc0),A                   ; ROM 025F6: 32c0dc
    LD A,$95                       ; ROM 025F9: 3e95
    LD ($de08),A                   ; ROM 025FB: 3208de
    LD A,B                         ; ROM 025FE: 78
    AND $30                        ; ROM 025FF: e630
    JR z,$25b2                     ; ROM 02601: 28af
    LD A,$ab                       ; ROM 02603: 3eab
    LD ($de08),A                   ; ROM 02605: 3208de
    LD A,($dcc0)                   ; ROM 02608: 3ac0dc
    OR A                           ; ROM 0260B: b7
    JR nz,$2614                    ; ROM 0260C: 2006
    LD A,0                         ; ROM 0260E: 3e00
    LD ($c01d),A                   ; ROM 02610: 321dc0
    RET                            ; ROM 02613: c9
    LD HL,($c0c2)                  ; ROM 02614: 2ac2c0
    LD A,($c0ba)                   ; ROM 02617: 3abac0
    OR A                           ; ROM 0261A: b7
    JR z,$2620                     ; ROM 0261B: 2803
    LD HL,($c0c4)                  ; ROM 0261D: 2ac4c0
    LD ($c0c0),HL                  ; ROM 02620: 22c0c0
    LD A,$18                       ; ROM 02623: 3e18
    LD ($c318),A                   ; ROM 02625: 3218c3
    LD ($c0db),A                   ; ROM 02628: 32dbc0
    LD A,($c0dd)                   ; ROM 0262B: 3addc0
    RRCA                           ; ROM 0262E: 0f
    RRCA                           ; ROM 0262F: 0f
    AND $3f                        ; ROM 02630: e63f
    LD B,A                         ; ROM 02632: 47
    ADD A,A                        ; ROM 02633: 87
    ADD A,B                        ; ROM 02634: 80
    LD ($c0dd),A                   ; ROM 02635: 32ddc0
    LD A,6                         ; ROM 02638: 3e06
    LD ($c01d),A                   ; ROM 0263A: 321dc0
    RET                            ; ROM 0263D: c9
    CALL $0b3d                     ; ROM 0263E: cd3d0b
    LD HL,$dca0                    ; ROM 02641: 21a0dc
    LD DE,$dcc0                    ; ROM 02644: 11c0dc
    LD BC,$20                      ; ROM 02647: 012000
    LDIR                           ; ROM 0264A: edb0
    LD DE,$dcc0                    ; ROM 0264C: 11c0dc
    LD B,$10                       ; ROM 0264F: 0610
    LD A,(DE)                      ; ROM 02651: 1a
    AND $30                        ; ROM 02652: e630
    RRCA                           ; ROM 02654: 0f
    RRCA                           ; ROM 02655: 0f
    RRCA                           ; ROM 02656: 0f
    RRCA                           ; ROM 02657: 0f
    LD C,A                         ; ROM 02658: 4f
    LD A,(DE)                      ; ROM 02659: 1a
    AND 12                         ; ROM 0265A: e60c
    RRCA                           ; ROM 0265C: 0f
    RRCA                           ; ROM 0265D: 0f
    ADD A,C                        ; ROM 0265E: 81
    LD C,A                         ; ROM 0265F: 4f
    LD A,(DE)                      ; ROM 02660: 1a
    AND 3                          ; ROM 02661: e603
    ADD A,C                        ; ROM 02663: 81
    LD HL,$2670                    ; ROM 02664: 217026
    RST 8                          ; ROM 02667: cf
    LD A,L                         ; ROM 02668: 7d
    LD (DE),A                      ; ROM 02669: 12
    INC DE                         ; ROM 0266A: 13
    DJNZ $2651                     ; ROM 0266B: 10e4
    JP $0ace                       ; ROM 0266D: c3ce0a
    db $00,$00,$00,$15,$15,$15,$2A,$2A,$3F,$3F,$00,$76,$47,$41,$4D,$45 ; ROM 02670
    db $4F,$56,$52,$43,$4E,$54,$49,$55,$46,$00,$B0,$19,$B1,$19,$B2,$19 ; ROM 02680
    db $B3,$19,$FF,$18,$B4,$19,$B5,$19,$B3,$19,$B6,$19,$82,$19,$B7,$19 ; ROM 02690
    db $B4,$19,$B8,$19,$B9,$19,$BA,$19,$B8,$19,$BB,$19,$B3,$19,$FF,$18 ; ROM 026A0
    db $BC,$19,$BA,$19,$B8,$19 ; ROM 026B0
    XOR A                          ; ROM 026B6: af
    LD ($c046),A                   ; ROM 026B7: 3246c0
    LD ($c047),A                   ; ROM 026BA: 3247c0
    LD IX,$c300                    ; ROM 026BD: dd2100c3
    LD A,(IX)                      ; ROM 026C1: dd7e00
    ADD A,A                        ; ROM 026C4: 87
    JP z,$2756                     ; ROM 026C5: ca5627
    CALL $2346                     ; ROM 026C8: cd4623
    LD A,($c047)                   ; ROM 026CB: 3a47c0
    INC A                          ; ROM 026CE: 3c
    LD ($c047),A                   ; ROM 026CF: 3247c0
    LD A,(IX+6)                    ; ROM 026D2: dd7e06
    OR A                           ; ROM 026D5: b7
    JR z,$26dd                     ; ROM 026D6: 2805
    DEC (IX+6)                     ; ROM 026D8: dd3506
    JR $273d                       ; ROM 026DB: 1860
    LD A,(IX)                      ; ROM 026DD: dd7e00
    ADD A,A                        ; ROM 026E0: 87
    LD HL,$2b63                    ; ROM 026E1: 21632b
    RST $18                        ; ROM 026E4: df
    LD A,(IX+4)                    ; ROM 026E5: dd7e04
    DEC A                          ; ROM 026E8: 3d
    JP m,$271b                     ; ROM 026E9: fa1b27
    LD L,(IX+$14)                  ; ROM 026EC: dd6e14
    LD H,(IX+$15)                  ; ROM 026EF: dd6615
    LD E,(IX+$10)                  ; ROM 026F2: dd5e10
    LD D,(IX+$11)                  ; ROM 026F5: dd5611
    ADD HL,DE                      ; ROM 026F8: 19
    EX DE,HL                       ; ROM 026F9: eb
    LD L,(IX+$16)                  ; ROM 026FA: dd6e16
    LD H,(IX+$17)                  ; ROM 026FD: dd6617
    LD C,(IX+$12)                  ; ROM 02700: dd4e12
    LD B,(IX+$13)                  ; ROM 02703: dd4613
    ADD HL,BC                      ; ROM 02706: 09
    OR A                           ; ROM 02707: b7
    JR nz,$270c                    ; ROM 02708: 2002
    LD L,A                         ; ROM 0270A: 6f
    LD E,A                         ; ROM 0270B: 5f
    LD (IX+4),A                    ; ROM 0270C: dd7704
    LD (IX+$12),L                  ; ROM 0270F: dd7512
    LD (IX+$13),H                  ; ROM 02712: dd7413
    LD (IX+$10),E                  ; ROM 02715: dd7310
    LD (IX+$11),D                  ; ROM 02718: dd7211
    LD A,(IX+12)                   ; ROM 0271B: dd7e0c
    OR A                           ; ROM 0271E: b7
    JR z,$273d                     ; ROM 0271F: 281c
    LD A,(IX+14)                   ; ROM 02721: dd7e0e
    INC A                          ; ROM 02724: 3c
    CP (IX+13)                     ; ROM 02725: ddbe0d
    JR c,$272b                     ; ROM 02728: 3801
    XOR A                          ; ROM 0272A: af
    LD (IX+14),A                   ; ROM 0272B: dd770e
    JR nz,$273d                    ; ROM 0272E: 200d
    LD A,(IX+11)                   ; ROM 02730: dd7e0b
    INC A                          ; ROM 02733: 3c
    CP (IX+12)                     ; ROM 02734: ddbe0c
    JR nz,$273a                    ; ROM 02737: 2001
    XOR A                          ; ROM 02739: af
    LD (IX+11),A                   ; ROM 0273A: dd770b
    LD A,(IX+5)                    ; ROM 0273D: dd7e05
    DEC A                          ; ROM 02740: 3d
    JP m,$2753                     ; ROM 02741: fa5327
    LD (IX+5),A                    ; ROM 02744: dd7705
    SET 0,(IX+3)                   ; ROM 02747: ddcb03c6
    AND 2                          ; ROM 0274B: e602
    JR z,$2753                     ; ROM 0274D: 2804
    RES 0,(IX+3)                   ; ROM 0274F: ddcb0386
    CALL $2768                     ; ROM 02753: cd6827
    LD DE,$30                      ; ROM 02756: 113000
    ADD IX,DE                      ; ROM 02759: dd19
    LD A,($c046)                   ; ROM 0275B: 3a46c0
    INC A                          ; ROM 0275E: 3c
    LD ($c046),A                   ; ROM 0275F: 3246c0
    CP $20                         ; ROM 02762: fe20
    JP c,$26c1                     ; ROM 02764: dac126
    RET                            ; ROM 02767: c9
    LD A,(IX+$1d)                  ; ROM 02768: dd7e1d
    OR A                           ; ROM 0276B: b7
    RET z                          ; ROM 0276C: c8
    LD L,(IX+$1e)                  ; ROM 0276D: dd6e1e
    LD H,(IX+$1f)                  ; ROM 02770: dd661f
    PUSH HL                        ; ROM 02773: e5
    POP IY                         ; ROM 02774: fde1
    LD (IX+$1d),0                  ; ROM 02776: dd361d00
    LD C,A                         ; ROM 0277A: 4f
    BIT 6,(IX+3)                   ; ROM 0277B: ddcb0376
    JR nz,$27da                    ; ROM 0277F: 2059
    BIT 5,(IX+3)                   ; ROM 02781: ddcb036e
    JR nz,$278e                    ; ROM 02785: 2007
    LD A,($c046)                   ; ROM 02787: 3a46c0
    OR A                           ; ROM 0278A: b7
    JR z,$27cf                     ; ROM 0278B: 2842
    RET                            ; ROM 0278D: c9
    LD A,(IX+$1a)                  ; ROM 0278E: dd7e1a
    OR A                           ; ROM 02791: b7
    JR nz,$279b                    ; ROM 02792: 2007
    LD A,(IY)                      ; ROM 02794: fd7e00
    CP 4                           ; ROM 02797: fe04
    JR z,$27ca                     ; ROM 02799: 282f
    LD A,(IX+$18)                  ; ROM 0279B: dd7e18
    SUB C                          ; ROM 0279E: 91
    JR nc,$27a2                    ; ROM 0279F: 3001
    XOR A                          ; ROM 027A1: af
    LD (IX+$18),A                  ; ROM 027A2: dd7718
    JR nz,$2803                    ; ROM 027A5: 205c
    LD A,(IX)                      ; ROM 027A7: dd7e00
    LD (IX+7),A                    ; ROM 027AA: dd7707
    LD (IX),1                      ; ROM 027AD: dd360001
    XOR A                          ; ROM 027B1: af
    LD (IX+6),A                    ; ROM 027B2: dd7706
    LD (IX+1),A                    ; ROM 027B5: dd7701
    LD (IX+$16),A                  ; ROM 027B8: dd7716
    LD (IX+$17),A                  ; ROM 027BB: dd7717
    LD (IX+$14),A                  ; ROM 027BE: dd7714
    LD (IX+$15),A                  ; ROM 027C1: dd7715
    LD A,$a0                       ; ROM 027C4: 3ea0
    LD ($de08),A                   ; ROM 027C6: 3208de
    RET                            ; ROM 027C9: c9
    LD (IX+6),$ff                  ; ROM 027CA: dd3606ff
    RET                            ; ROM 027CE: c9
    LD A,(IX+$18)                  ; ROM 027CF: dd7e18
    SUB C                          ; ROM 027D2: 91
    JR nc,$27d6                    ; ROM 027D3: 3001
    XOR A                          ; ROM 027D5: af
    LD (IX+$18),A                  ; ROM 027D6: dd7718
    RET                            ; ROM 027D9: c9
    LD A,(IX+$18)                  ; ROM 027DA: dd7e18
    SUB C                          ; ROM 027DD: 91
    JR nc,$27e1                    ; ROM 027DE: 3001
    XOR A                          ; ROM 027E0: af
    LD (IX+$18),A                  ; ROM 027E1: dd7718
    JR nz,$2803                    ; ROM 027E4: 201d
    LD (IX),7                      ; ROM 027E6: dd360007
    XOR A                          ; ROM 027EA: af
    LD (IX+6),A                    ; ROM 027EB: dd7706
    LD (IX+1),A                    ; ROM 027EE: dd7701
    LD (IX+$16),A                  ; ROM 027F1: dd7716
    LD (IX+$17),A                  ; ROM 027F4: dd7717
    LD (IX+$14),A                  ; ROM 027F7: dd7714
    LD (IX+$15),A                  ; ROM 027FA: dd7715
    LD A,$9e                       ; ROM 027FD: 3e9e
    LD ($de08),A                   ; ROM 027FF: 3208de
    RET                            ; ROM 02802: c9
    LD A,$9c                       ; ROM 02803: 3e9c
    LD ($de08),A                   ; ROM 02805: 3208de
    LD (IX+5),$20                  ; ROM 02808: dd360520
    BIT 3,(IX+3)                   ; ROM 0280C: ddcb035e
    RET z                          ; ROM 02810: c8
    LD A,(IY+10)                   ; ROM 02811: fd7e0a
    ADD A,A                        ; ROM 02814: 87
    LD HL,$2830                    ; ROM 02815: 213028
    RST $18                        ; ROM 02818: df
    XOR A                          ; ROM 02819: af
    LD (IX+$12),A                  ; ROM 0281A: dd7712
    LD (IX+$16),A                  ; ROM 0281D: dd7716
    LD (IX+$17),A                  ; ROM 02820: dd7717
    LD (IX+$10),A                  ; ROM 02823: dd7710
    LD (IX+$14),A                  ; ROM 02826: dd7714
    LD (IX+$15),A                  ; ROM 02829: dd7715
    LD (IX+4),A                    ; ROM 0282C: dd7704
    RET                            ; ROM 0282F: c9
    db $38,$28,$63,$28,$90,$28,$B8,$28,$DD,$7E,$13,$C6,$04,$E6,$F8,$DD ; ROM 02830
    db $77,$13,$DD,$7E,$11,$E6,$F8,$DD,$77,$11,$FE,$19,$D8,$01,$F0,$F8 ; ROM 02840
    db $CD,$0E,$23,$7A,$2C,$2C,$B6,$E6,$A0,$C0,$DD,$7E,$11,$C6,$F8,$DD ; ROM 02850
    db $77,$11,$C9,$DD,$7E,$13,$C6,$04,$E6,$F8,$DD,$77,$13,$DD,$7E,$11 ; ROM 02860
    db $C6,$07,$E6,$F8,$DD,$77,$11,$FE,$88,$D0,$01,$00,$F8,$CD,$0E,$23 ; ROM 02870
    db $7A,$2C,$2C,$B6,$E6,$A0,$C0,$DD,$7E,$11,$C6,$08,$DD,$77,$11,$C9 ; ROM 02880
    db $DD,$7E,$11,$C6,$04,$E6,$F8,$DD,$77,$11,$DD,$7E,$13,$E6,$F8,$DD ; ROM 02890
    db $77,$13,$FE,$19,$D8,$01,$F8,$F0,$CD,$0E,$23,$7A,$E6,$A0,$C0,$DD ; ROM 028A0
    db $7E,$13,$C6,$F8,$DD,$77,$13,$C9,$DD,$7E,$11,$C6,$04,$E6,$F8,$DD ; ROM 028B0
    db $77,$11,$DD,$7E,$13,$C6,$07,$E6,$F8,$DD,$77,$13,$FE,$E8,$D0,$01 ; ROM 028C0
    db $F8,$08,$CD,$0E,$23,$7A,$E6,$A0,$C0,$DD,$7E,$13,$C6,$08,$DD,$77 ; ROM 028D0
    db $13,$C9 ; ROM 028E0
    LD A,(IX+1)                    ; ROM 028E2: dd7e01
    LD HL,$28fa                    ; ROM 028E5: 21fa28
    RST $18                        ; ROM 028E8: df
    CALL $2add                     ; ROM 028E9: cddd2a
    RET nc                         ; ROM 028EC: d0
    LD A,($c0dd)                   ; ROM 028ED: 3addc0
    ADD A,1                        ; ROM 028F0: c601
    JR nc,$28f6                    ; ROM 028F2: 3002
    db $3E,$FF ; ROM 028F4
    LD ($c0dd),A                   ; ROM 028F6: 32ddc0
    RET                            ; ROM 028F9: c9
    db $02,$29,$26,$29,$39,$29,$46,$29 ; ROM 028FA
    LD A,$92                       ; ROM 02902: 3e92
    LD HL,$84ce                    ; ROM 02904: 21ce84
    LD (IX+2),A                    ; ROM 02907: dd7702
    LD (IX+8),L                    ; ROM 0290A: dd7508
    LD (IX+9),H                    ; ROM 0290D: dd7409
    XOR A                          ; ROM 02910: af
    LD (IX+13),A                   ; ROM 02911: dd770d
    LD (IX+12),A                   ; ROM 02914: dd770c
    LD (IX+11),A                   ; ROM 02917: dd770b
    LD (IX+$1d),A                  ; ROM 0291A: dd771d
    LD (IX+3),1                    ; ROM 0291D: dd360301
    LD (IX+1),2                    ; ROM 02921: dd360102
    RET                            ; ROM 02925: c9
    LD A,($c301)                   ; ROM 02926: 3a01c3
    CP 1                           ; ROM 02929: fe01
    RET nz                         ; ROM 0292B: c0
    SET 1,(IX+3)                   ; ROM 0292C: ddcb03ce
    LD (IX+14),$f0                 ; ROM 02930: dd360ef0
    LD (IX+1),4                    ; ROM 02934: dd360104
    RET                            ; ROM 02938: c9
    DEC (IX+14)                    ; ROM 02939: dd350e
    RET nz                         ; ROM 0293C: c0
    LD (IX+5),$78                  ; ROM 0293D: dd360578
    LD (IX+1),6                    ; ROM 02941: dd360106
    RET                            ; ROM 02945: c9
    LD A,(IX+5)                    ; ROM 02946: dd7e05
    OR A                           ; ROM 02949: b7
    JP z,$57eb                     ; ROM 0294A: caeb57
    RET                            ; ROM 0294D: c9
    LD A,(IX+1)                    ; ROM 0294E: dd7e01
    LD HL,$2966                    ; ROM 02951: 216629
    RST $18                        ; ROM 02954: df
    CALL $2add                     ; ROM 02955: cddd2a
    RET nc                         ; ROM 02958: d0
    LD A,($c0dd)                   ; ROM 02959: 3addc0
    ADD A,5                        ; ROM 0295C: c605
    JR nc,$2962                    ; ROM 0295E: 3002
    db $3E,$FF ; ROM 02960
    LD ($c0dd),A                   ; ROM 02962: 32ddc0
    RET                            ; ROM 02965: c9
    db $6E,$29,$26,$29,$39,$29,$46,$29 ; ROM 02966
    LD A,$94                       ; ROM 0296E: 3e94
    JR $2904                       ; ROM 02970: 1892
    LD A,(IX+1)                    ; ROM 02972: dd7e01
    LD HL,$298e                    ; ROM 02975: 218e29
    RST $18                        ; ROM 02978: df
    CALL $2add                     ; ROM 02979: cddd2a
    RET nc                         ; ROM 0297C: d0
    LD A,($c0da)                   ; ROM 0297D: 3adac0
    LD C,A                         ; ROM 02980: 4f
    LD A,($c318)                   ; ROM 02981: 3a18c3
    ADD A,8                        ; ROM 02984: c608
    CP C                           ; ROM 02986: b9
    JR c,$298a                     ; ROM 02987: 3801
    LD A,C                         ; ROM 02989: 79
    LD ($c318),A                   ; ROM 0298A: 3218c3
    RET                            ; ROM 0298D: c9
    db $96,$29,$26,$29,$39,$29,$46,$29 ; ROM 0298E
    LD A,$aa                       ; ROM 02996: 3eaa
    LD HL,$84e1                    ; ROM 02998: 21e184
    JP $2907                       ; ROM 0299B: c30729
    LD A,(IX+1)                    ; ROM 0299E: dd7e01
    LD HL,$29ba                    ; ROM 029A1: 21ba29
    RST $18                        ; ROM 029A4: df
    CALL $2add                     ; ROM 029A5: cddd2a
    RET nc                         ; ROM 029A8: d0
    LD A,($c0da)                   ; ROM 029A9: 3adac0
    LD C,A                         ; ROM 029AC: 4f
    LD A,($c318)                   ; ROM 029AD: 3a18c3
    ADD A,$18                      ; ROM 029B0: c618
    CP C                           ; ROM 029B2: b9
    JR c,$29b6                     ; ROM 029B3: 3801
    LD A,C                         ; ROM 029B5: 79
    LD ($c318),A                   ; ROM 029B6: 3218c3
    RET                            ; ROM 029B9: c9
    db $C2,$29,$26,$29,$39,$29,$46,$29 ; ROM 029BA
    LD C,$1b                       ; ROM 029C2: 0e1b
    LD A,($c0a3)                   ; ROM 029C4: 3aa3c0
    OR A                           ; ROM 029C7: b7
    JR z,$29d0                     ; ROM 029C8: 2806
    db $B9,$28,$0D,$C3,$EB,$57 ; ROM 029CA
    LD A,C                         ; ROM 029D0: 79
    LD ($c0a3),A                   ; ROM 029D1: 32a3c0
    LD DE,$7780                    ; ROM 029D4: 118077
    CALL $2af4                     ; ROM 029D7: cdf42a
    LD A,$bc                       ; ROM 029DA: 3ebc
    LD HL,$84e1                    ; ROM 029DC: 21e184
    JP $2907                       ; ROM 029DF: c30729
    LD A,(IX+1)                    ; ROM 029E2: dd7e01
    LD HL,$29fe                    ; ROM 029E5: 21fe29
    RST $18                        ; ROM 029E8: df
    CALL $2add                     ; ROM 029E9: cddd2a
    RET nc                         ; ROM 029EC: d0
    LD A,($c0dc)                   ; ROM 029ED: 3adcc0
    LD C,A                         ; ROM 029F0: 4f
    LD A,($c0db)                   ; ROM 029F1: 3adbc0
    ADD A,8                        ; ROM 029F4: c608
    CP C                           ; ROM 029F6: b9
    JR c,$29fa                     ; ROM 029F7: 3801
    LD A,C                         ; ROM 029F9: 79
    LD ($c0db),A                   ; ROM 029FA: 32dbc0
    RET                            ; ROM 029FD: c9
    db $06,$2A,$26,$29,$39,$29,$46,$29 ; ROM 029FE
    LD C,$1c                       ; ROM 02A06: 0e1c
    JR $29c4                       ; ROM 02A08: 18ba
    LD A,(IX+1)                    ; ROM 02A0A: dd7e01
    LD HL,$2a2e                    ; ROM 02A0D: 212e2a
    RST $18                        ; ROM 02A10: df
    CALL $2add                     ; ROM 02A11: cddd2a
    RET nc                         ; ROM 02A14: d0
    LD IY,$c600                    ; ROM 02A15: fd2100c6
    LD DE,$30                      ; ROM 02A19: 113000
    LD B,$10                       ; ROM 02A1C: 0610
    LD A,(IY)                      ; ROM 02A1E: fd7e00
    CP $20                         ; ROM 02A21: fe20
    JR c,$2a29                     ; ROM 02A23: 3804
    db $FD,$36,$06,$FF ; ROM 02A25
    ADD IY,DE                      ; ROM 02A29: fd19
    DJNZ $2a1e                     ; ROM 02A2B: 10f1
    RET                            ; ROM 02A2D: c9
    db $36,$2A,$26,$29,$39,$29,$46,$29 ; ROM 02A2E
    LD C,$1d                       ; ROM 02A36: 0e1d
    JR $29c4                       ; ROM 02A38: 188a
    db $DD,$7E,$01,$21,$51,$2A,$DF,$CD,$DD,$2A,$D0,$3A,$DE,$C0,$FE,$63 ; ROM 02A3A
    db $30,$01,$3C,$32,$DE,$C0,$C9,$57,$2A,$5C,$2A,$6A,$2A,$3E,$96,$C3 ; ROM 02A4A
    db $04,$29,$3A,$01,$C3,$FE,$01,$C0,$DD,$CB,$03,$CE,$DD,$36,$01,$04 ; ROM 02A5A
    db $C9,$DD,$7E,$01,$21,$AB,$2A,$DF,$CD,$DD,$2A,$D0,$2A,$37,$C0,$26 ; ROM 02A6A
    db $00,$11,$CE,$C0,$19,$36,$80,$3A,$37,$C0,$3D,$87,$21,$DC,$1E,$CF ; ROM 02A7A
    db $C6,$9F,$DD,$E5,$CD,$17,$63,$DD,$E1,$3A,$DA,$C0,$C6,$08,$FE,$81 ; ROM 02A8A
    db $30,$03,$32,$DA,$C0,$3A,$DC,$C0,$32,$DB,$C0,$CD,$1C,$60,$C3,$AF ; ROM 02A9A
    db $1C,$B1,$2A,$5C,$2A,$6A,$2A,$AF,$32,$AE,$C0,$3A,$37,$C0,$3D,$87 ; ROM 02AAA
    db $21,$DC,$1E,$CF,$21,$CD,$2A,$CD,$07,$29,$DD,$36,$11,$1C,$DD,$36 ; ROM 02ABA
    db $13,$80,$C9,$D5,$2A,$D5,$2A,$D5,$2A,$D5,$2A,$D7,$2A,$01,$01,$01 ; ROM 02ACA
    db $F7,$FC,$00 ; ROM 02ADA
    LD A,(IX+$1d)                  ; ROM 02ADD: dd7e1d
    OR A                           ; ROM 02AE0: b7
    JR nz,$2aea                    ; ROM 02AE1: 2007
    BIT 2,(IX+3)                   ; ROM 02AE3: ddcb0356
    JR nz,$2aea                    ; ROM 02AE7: 2001
    RET                            ; ROM 02AE9: c9
    CALL $57eb                     ; ROM 02AEA: cdeb57
    LD A,$96                       ; ROM 02AED: 3e96
    LD ($de08),A                   ; ROM 02AEF: 3208de
    SCF                            ; ROM 02AF2: 37
    RET                            ; ROM 02AF3: c9
    CP $1e                         ; ROM 02AF4: fe1e
    JR c,$2b07                     ; ROM 02AF6: 380f
    JR z,$2b1d                     ; ROM 02AF8: 2823
    CP $20                         ; ROM 02AFA: fe20
    JR c,$2b2b                     ; ROM 02AFC: 382d
    JR z,$2b2b                     ; ROM 02AFE: 282b
    CP $2a                         ; ROM 02B00: fe2a
    JR c,$2b2c                     ; ROM 02B02: 3828
    JR z,$2b3c                     ; ROM 02B04: 2836
    RET                            ; ROM 02B06: c9
    LD B,A                         ; ROM 02B07: 47
    LD C,0                         ; ROM 02B08: 0e00
    SRL B                          ; ROM 02B0A: cb38
    RR C                           ; ROM 02B0C: cb19
    LD HL,$a801                    ; ROM 02B0E: 2101a8
    ADD HL,BC                      ; ROM 02B11: 09
    LD A,4                         ; ROM 02B12: 3e04
    LD ($ffff),A                   ; ROM 02B14: 32ffff
    LD BC,$80                      ; ROM 02B17: 018000
    JP $0384                       ; ROM 02B1A: c38403
    LD HL,$32c0                    ; ROM 02B1D: 21c032
    CALL $2b44                     ; ROM 02B20: cd442b
    CALL $2b55                     ; ROM 02B23: cd552b
    CALL $2b44                     ; ROM 02B26: cd442b
    JR $2b55                       ; ROM 02B29: 182a
    RET                            ; ROM 02B2B: c9
    SUB $21                        ; ROM 02B2C: d621
    LD L,A                         ; ROM 02B2E: 6f
    LD H,0                         ; ROM 02B2F: 2600
    ADD HL,HL                      ; ROM 02B31: 29
    ADD HL,HL                      ; ROM 02B32: 29
    ADD HL,HL                      ; ROM 02B33: 29
    ADD HL,HL                      ; ROM 02B34: 29
    ADD HL,HL                      ; ROM 02B35: 29
    LD BC,$3040                    ; ROM 02B36: 014030
    ADD HL,BC                      ; ROM 02B39: 09
    JR $2b44                       ; ROM 02B3A: 1808
    LD HL,$bbb9                    ; ROM 02B3C: 21b9bb
    LD A,4                         ; ROM 02B3F: 3e04
    JP $0327                       ; ROM 02B41: c32703
    LD B,$20                       ; ROM 02B44: 0620
    EX DE,HL                       ; ROM 02B46: eb
    RST $28                        ; ROM 02B47: ef
    EX DE,HL                       ; ROM 02B48: eb
    INC HL                         ; ROM 02B49: 23
    IN A,($00be)                   ; ROM 02B4A: dbbe
    LD C,A                         ; ROM 02B4C: 4f
    RST $28                        ; ROM 02B4D: ef
    LD A,C                         ; ROM 02B4E: 79
    INC DE                         ; ROM 02B4F: 13
    OUT ($00be),A                  ; ROM 02B50: d3be
    DJNZ $2b46                     ; ROM 02B52: 10f2
    RET                            ; ROM 02B54: c9
    PUSH HL                        ; ROM 02B55: e5
    LD HL,0                        ; ROM 02B56: 210000
    LD BC,$10                      ; ROM 02B59: 011000
    CALL $0397                     ; ROM 02B5C: cd9703
    LD L,$20                       ; ROM 02B5F: 2e20
    ADD HL,DE                      ; ROM 02B61: 19
    EX DE,HL                       ; ROM 02B62: eb
    POP HL                         ; ROM 02B63: e1
    RET                            ; ROM 02B64: c9
    db $EE,$4A,$BE,$2D,$3A,$39,$27,$3A,$CC,$39,$EB,$57,$A4,$4B,$E2,$28 ; ROM 02B65
    db $4E,$29,$72,$29,$9E,$29,$E2,$29,$0A,$2A,$3A,$2A,$6B,$2A,$A5,$3D ; ROM 02B75
    db $69,$3E,$8C,$3E,$CC,$3E,$7D,$3F,$B0,$3F,$E3,$3F,$06,$40,$29,$40 ; ROM 02B85
    db $4C,$40,$8E,$40,$B1,$40,$E1,$40,$82,$41,$81,$42,$B4,$42,$5D,$4C ; ROM 02B95
    db $5D,$4C,$5D,$4C,$72,$4C,$72,$4C,$72,$4C,$78,$4C,$78,$4C,$78,$4C ; ROM 02BA5
    db $B4,$4C,$B4,$4C,$BA,$4C,$C0,$4C,$C6,$4C,$CC,$4C,$CC,$4C,$D2,$4C ; ROM 02BB5
    db $D8,$4C,$D8,$4C,$DE,$4C,$E4,$4C,$EA,$4C,$F0,$4C,$F6,$4C,$FC,$4C ; ROM 02BC5
    db $FC,$4C,$02,$4D,$02,$4D,$08,$4D,$0E,$4D,$0E,$4D,$14,$4D,$1A,$4D ; ROM 02BD5
    db $20,$4D,$26,$4D,$2C,$4D,$2C,$4D,$2C,$4D,$32,$4D,$38,$4D,$38,$4D ; ROM 02BE5
    db $38,$4D,$44,$4F,$44,$4F,$B1,$4F,$B7,$4F,$B7,$4F,$D2,$4F,$D2,$4F ; ROM 02BF5
    db $D2,$4F,$D8,$4F,$F3,$4F,$08,$50,$08,$50,$0E,$50,$14,$50,$14,$50 ; ROM 02C05
    db $1A,$50,$1A,$50,$43,$50,$49,$50,$49,$50,$59,$50,$5F,$50,$5F,$50 ; ROM 02C15
    db $65,$50,$65,$50,$6B,$50,$6B,$50,$71,$50,$2B,$51,$93,$51,$AE,$51 ; ROM 02C25
    db $AE,$51,$D3,$54,$D3,$54,$D9,$54,$F1,$55,$EB,$57,$EB,$57,$8C,$43 ; ROM 02C35
    db $AF,$43,$D2,$43,$2B,$44,$57,$44,$18,$45,$B4,$46,$F7,$47,$6B,$50 ; ROM 02C45
    db $6B,$50,$AE,$51,$AE,$51,$D3,$54,$EB,$57,$EB,$57,$EB,$57 ; ROM 02C55
    LD IX,$c300                    ; ROM 02C63: dd2100c3
    XOR A                          ; ROM 02C67: af
    LD ($c312),A                   ; ROM 02C68: 3212c3
    LD ($c310),A                   ; ROM 02C6B: 3210c3
    LD ($c304),A                   ; ROM 02C6E: 3204c3
    LD ($c30c),A                   ; ROM 02C71: 320cc3
    LD ($c30b),A                   ; ROM 02C74: 320bc3
    LD (IX),2                      ; ROM 02C77: dd360002
    LD (IX+1),0                    ; ROM 02C7B: dd360100
    LD (IX+2),$f0                  ; ROM 02C7F: dd3602f0
    LD (IX+3),3                    ; ROM 02C83: dd360303
    CALL $369f                     ; ROM 02C87: cd9f36
    CALL $2d7c                     ; ROM 02C8A: cd7c2d
    LD A,($c0f2)                   ; ROM 02C8D: 3af2c0
    DEC A                          ; ROM 02C90: 3d
    ADD A,A                        ; ROM 02C91: 87
    LD L,A                         ; ROM 02C92: 6f
    LD A,($c0f1)                   ; ROM 02C93: 3af1c0
    DEC A                          ; ROM 02C96: 3d
    ADD A,A                        ; ROM 02C97: 87
    ADD A,A                        ; ROM 02C98: 87
    LD H,A                         ; ROM 02C99: 67
    LD A,($c0bf)                   ; ROM 02C9A: 3abfc0
    OR A                           ; ROM 02C9D: b7
    LD A,H                         ; ROM 02C9E: 7c
    JR z,$2ca2                     ; ROM 02C9F: 2801
    XOR A                          ; ROM 02CA1: af
    ADD A,L                        ; ROM 02CA2: 85
    LD ($c31a),A                   ; ROM 02CA3: 321ac3
    CALL $2d8a                     ; ROM 02CA6: cd8a2d
    LD ($c319),A                   ; ROM 02CA9: 3219c3
    LD A,($c311)                   ; ROM 02CAC: 3a11c3
    LD E,A                         ; ROM 02CAF: 5f
    LD A,($c313)                   ; ROM 02CB0: 3a13c3
    LD D,A                         ; ROM 02CB3: 57
    LD A,D                         ; ROM 02CB4: 7a
    AND 8                          ; ROM 02CB5: e608
    RRCA                           ; ROM 02CB7: 0f
    RRCA                           ; ROM 02CB8: 0f
    RRCA                           ; ROM 02CB9: 0f
    LD C,A                         ; ROM 02CBA: 4f
    LD A,E                         ; ROM 02CBB: 7b
    AND 8                          ; ROM 02CBC: e608
    RRCA                           ; ROM 02CBE: 0f
    RRCA                           ; ROM 02CBF: 0f
    OR C                           ; ROM 02CC0: b1
    LD C,A                         ; ROM 02CC1: 4f
    LD A,E                         ; ROM 02CC2: 7b
    OR D                           ; ROM 02CC3: b2
    AND 7                          ; ROM 02CC4: e607
    JR z,$2cca                     ; ROM 02CC6: 2802
    SET 7,C                        ; ROM 02CC8: cbf9
    LD A,C                         ; ROM 02CCA: 79
    LD ($c06b),A                   ; ROM 02CCB: 326bc0
    LD BC,$f4f4                    ; ROM 02CCE: 01f4f4
    CALL $230e                     ; ROM 02CD1: cd0e23
    DEC L                          ; ROM 02CD4: 2d
    LD DE,$c048                    ; ROM 02CD5: 1148c0
    LD BC,$3ff                     ; ROM 02CD8: 01ff03
    LDI                            ; ROM 02CDB: eda0
    LDI                            ; ROM 02CDD: eda0
    LDI                            ; ROM 02CDF: eda0
    LDI                            ; ROM 02CE1: eda0
    LDI                            ; ROM 02CE3: eda0
    LDI                            ; ROM 02CE5: eda0
    LDI                            ; ROM 02CE7: eda0
    LDI                            ; ROM 02CE9: eda0
    LD A,$38                       ; ROM 02CEB: 3e38
    ADD A,L                        ; ROM 02CED: 85
    LD L,A                         ; ROM 02CEE: 6f
    JR nc,$2cf2                    ; ROM 02CEF: 3001
    INC H                          ; ROM 02CF1: 24
    DJNZ $2cdb                     ; ROM 02CF2: 10e7
    LD DE,$29be                    ; ROM 02CF4: 11be29
    ADD HL,DE                      ; ROM 02CF7: 19
    LD ($c060),HL                  ; ROM 02CF8: 2260c0
    LD A,($c0ec)                   ; ROM 02CFB: 3aecc0
    OR A                           ; ROM 02CFE: b7
    JR nz,$2d11                    ; ROM 02CFF: 2010
    LD HL,$c049                    ; ROM 02D01: 2149c0
    LD BC,$c20                     ; ROM 02D04: 01200c
    LD A,(HL)                      ; ROM 02D07: 7e
    AND C                          ; ROM 02D08: a1
    JR z,$2d0d                     ; ROM 02D09: 2802
    SET 7,(HL)                     ; ROM 02D0B: cbfe
    INC L                          ; ROM 02D0D: 2c
    INC L                          ; ROM 02D0E: 2c
    DJNZ $2d07                     ; ROM 02D0F: 10f6
    LD A,($c040)                   ; ROM 02D11: 3a40c0
    CP 1                           ; ROM 02D14: fe01
    JR z,$2d3d                     ; ROM 02D16: 2825
    JR c,$2d20                     ; ROM 02D18: 3806
    LD IY,$2569                    ; ROM 02D1A: fd216925
    JR $2d24                       ; ROM 02D1E: 1804
    LD IY,$2544                    ; ROM 02D20: fd214425
    CALL $386e                     ; ROM 02D24: cd6e38
    JR z,$2d3e                     ; ROM 02D27: 2815
    CALL $3885                     ; ROM 02D29: cd8538
    JR z,$2d3e                     ; ROM 02D2C: 2810
    CALL $3885                     ; ROM 02D2E: cd8538
    JR z,$2d3e                     ; ROM 02D31: 280b
    CALL $386e                     ; ROM 02D33: cd6e38
    JR z,$2d3e                     ; ROM 02D36: 2806
    CALL $386e                     ; ROM 02D38: cd6e38
    JR z,$2d3e                     ; ROM 02D3B: 2801
    XOR A                          ; ROM 02D3D: af
    LD ($c041),A                   ; ROM 02D3E: 3241c0
    LD A,($c0f0)                   ; ROM 02D41: 3af0c0
    OR A                           ; ROM 02D44: b7
    JR z,$2d7b                     ; ROM 02D45: 2834
    LD A,($c053)                   ; ROM 02D47: 3a53c0
    LD HL,$c055                    ; ROM 02D4A: 2155c0
    AND (HL)                       ; ROM 02D4D: a6
    AND $c0                        ; ROM 02D4E: e6c0
    BIT 6,A                        ; ROM 02D50: cb77
    JR z,$2d7b                     ; ROM 02D52: 2827
    RLCA                           ; ROM 02D54: 07
    JR nc,$2d6c                    ; ROM 02D55: 3015
    LD HL,$c049                    ; ROM 02D57: 2149c0
    LD B,12                        ; ROM 02D5A: 060c
    BIT 6,(HL)                     ; ROM 02D5C: cb76
    JR z,$2d64                     ; ROM 02D5E: 2804
    RES 7,(HL)                     ; ROM 02D60: cbbe
    JR $2d66                       ; ROM 02D62: 1802
    SET 7,(HL)                     ; ROM 02D64: cbfe
    INC HL                         ; ROM 02D66: 23
    INC HL                         ; ROM 02D67: 23
    DJNZ $2d5c                     ; ROM 02D68: 10f2
    JR $2d7b                       ; ROM 02D6A: 180f
    LD HL,$c049                    ; ROM 02D6C: 2149c0
    LD B,12                        ; ROM 02D6F: 060c
    BIT 6,(HL)                     ; ROM 02D71: cb76
    JR z,$2d77                     ; ROM 02D73: 2802
    RES 7,(HL)                     ; ROM 02D75: cbbe
    INC HL                         ; ROM 02D77: 23
    INC HL                         ; ROM 02D78: 23
    DJNZ $2d71                     ; ROM 02D79: 10f6
    RET                            ; ROM 02D7B: c9
    LD HL,$c330                    ; ROM 02D7C: 2130c3
    LD DE,$c331                    ; ROM 02D7F: 1131c3
    LD BC,$17f                     ; ROM 02D82: 017f01
    LD (HL),0                      ; ROM 02D85: 3600
    LDIR                           ; ROM 02D87: edb0
    RET                            ; ROM 02D89: c9
    LD HL,$c0df                    ; ROM 02D8A: 21dfc0
    LD E,(HL)                      ; ROM 02D8D: 5e
    LD D,0                         ; ROM 02D8E: 1600
    INC HL                         ; ROM 02D90: 23
    ADD HL,DE                      ; ROM 02D91: 19
    LD L,(HL)                      ; ROM 02D92: 6e
    LD H,D                         ; ROM 02D93: 62
    EX DE,HL                       ; ROM 02D94: eb
    ADD HL,HL                      ; ROM 02D95: 29
    ADD HL,HL                      ; ROM 02D96: 29
    ADD HL,DE                      ; ROM 02D97: 19
    LD DE,$2d9e                    ; ROM 02D98: 119e2d
    ADD HL,DE                      ; ROM 02D9B: 19
    LD A,(HL)                      ; ROM 02D9C: 7e
    RET                            ; ROM 02D9D: c9
    db $00,$02,$06,$0A,$00,$04,$0C,$00,$00,$00,$00,$00,$00,$00,$00,$00 ; ROM 02D9E
    db $00,$04,$08,$00,$00,$00,$00,$00,$00,$08,$0C,$00,$00,$00,$00,$00 ; ROM 02DAE
    CALL $2c8d                     ; ROM 02DBE: cd8d2c
    CALL $2f18                     ; ROM 02DC1: cd182f
    LD A,($c021)                   ; ROM 02DC4: 3a21c0
    AND $20                        ; ROM 02DC7: e620
    JR z,$2def                     ; ROM 02DC9: 2824
    LD A,($c301)                   ; ROM 02DCB: 3a01c3
    DEC A                          ; ROM 02DCE: 3d
    JR nz,$2def                    ; ROM 02DCF: 201e
    LD A,($c318)                   ; ROM 02DD1: 3a18c3
    OR A                           ; ROM 02DD4: b7
    JR z,$2def                     ; ROM 02DD5: 2818
    LD A,($c041)                   ; ROM 02DD7: 3a41c0
    CP 5                           ; ROM 02DDA: fe05
    JR z,$2def                     ; ROM 02DDC: 2811
    CP 3                           ; ROM 02DDE: fe03
    JR nz,$2de7                    ; ROM 02DE0: 2005
    db $CD,$42,$30,$18,$08 ; ROM 02DE2
    LD A,($c0df)                   ; ROM 02DE7: 3adfc0
    ADD A,A                        ; ROM 02DEA: 87
    LD HL,$2edb                    ; ROM 02DEB: 21db2e
    RST $18                        ; ROM 02DEE: df
    LD A,($c301)                   ; ROM 02DEF: 3a01c3
    ADD A,A                        ; ROM 02DF2: 87
    LD HL,$2ef3                    ; ROM 02DF3: 21f32e
    RST $18                        ; ROM 02DF6: df
    LD A,($c301)                   ; ROM 02DF7: 3a01c3
    CP 9                           ; ROM 02DFA: fe09
    RET z                          ; ROM 02DFC: c8
    LD A,($c318)                   ; ROM 02DFD: 3a18c3
    OR A                           ; ROM 02E00: b7
    JR nz,$2e08                    ; ROM 02E01: 2005
    db $DD,$36,$01,$08,$C9 ; ROM 02E03
    LD A,($c31d)                   ; ROM 02E08: 3a1dc3
    OR A                           ; ROM 02E0B: b7
    JP z,$2eb6                     ; ROM 02E0C: cab62e
    db $DD,$6E,$1E,$DD,$66,$1F,$E5,$FD,$E1,$FD,$CB,$03,$66,$CA,$B3,$2E ; ROM 02E0F
    db $3E,$0C,$32,$FF,$FF,$21,$69,$A2,$3A,$F2,$C0,$CF,$FD,$BE,$19,$38 ; ROM 02E1F
    db $6F,$3A,$01,$C3,$3D,$20,$69,$3A,$41,$C0,$FE,$03,$28,$62,$21,$00 ; ROM 02E2F
    db $00,$3A,$0A,$C3,$B7,$28,$0F,$FE,$02,$38,$14,$28,$2A,$FD,$7E,$17 ; ROM 02E3F
    db $B7,$F2,$9F,$2E,$18,$28,$FD,$7E,$15,$B7,$FA,$9F,$2E,$18,$07,$FD ; ROM 02E4F
    db $7E,$15,$B7,$F2,$9F,$2E,$FD,$5E,$14,$57,$B3,$28,$33,$ED,$52,$FD ; ROM 02E5F
    db $75,$14,$FD,$74,$15,$18,$16,$FD,$7E,$17,$B7,$FA,$9F,$2E,$FD,$5E ; ROM 02E6F
    db $16,$57,$B3,$28,$1B,$ED,$52,$FD,$75,$16,$FD,$74,$17,$FD,$36,$04 ; ROM 02E7F
    db $0A,$FD,$CB,$03,$8E,$AF,$32,$1D,$C3,$3E,$98,$32,$06,$DE,$18,$17 ; ROM 02E8F
    db $CD,$DA,$37,$DD,$6E,$1E,$DD,$66,$1F,$5D,$54,$1C,$01,$2F,$00,$70 ; ROM 02E9F
    db $ED,$B0,$18,$03,$CD,$DA,$37 ; ROM 02EAF
    LD A,($c041)                   ; ROM 02EB6: 3a41c0
    CP 4                           ; ROM 02EB9: fe04
    JR nz,$2ecb                    ; ROM 02EBB: 200e
    db $3A,$05,$C3,$B7,$20,$08,$3A,$1D,$C3,$C6,$04,$32,$1D,$C3 ; ROM 02EBD
    LD A,($c31d)                   ; ROM 02ECB: 3a1dc3
    OR A                           ; ROM 02ECE: b7
    JR z,$2eda                     ; ROM 02ECF: 2809
    db $DD,$36,$05,$30,$3E,$91,$32,$06,$DE ; ROM 02ED1
    RET                            ; ROM 02EDA: c9
    db $AA,$2F,$B4,$2F,$BE,$2F,$D2,$2F,$50,$30,$77,$30,$A7,$30,$21,$30 ; ROM 02EDB
    db $D6,$30,$E8,$30,$24,$31,$E7,$31,$92,$32,$95,$32,$A7,$34,$AE,$34 ; ROM 02EEB
    db $BD,$34,$C4,$34,$B3,$37,$BD,$37,$1D,$37,$36,$37,$6C,$37,$7D,$37 ; ROM 02EFB
    db $0D,$2F,$AF,$32,$0B,$C3,$DD,$CB,$03,$C6,$C3,$9F,$36 ; ROM 02F0B
    LD A,($c040)                   ; ROM 02F18: 3a40c0
    OR A                           ; ROM 02F1B: b7
    RET nz                         ; ROM 02F1C: c0
    LD A,($c313)                   ; ROM 02F1D: 3a13c3
    LD B,A                         ; ROM 02F20: 47
    LD A,($c311)                   ; ROM 02F21: 3a11c3
    LD C,A                         ; ROM 02F24: 4f
    OR B                           ; ROM 02F25: b0
    AND 7                          ; ROM 02F26: e607
    RET nz                         ; ROM 02F28: c0
    LD A,($c052)                   ; ROM 02F29: 3a52c0
    CP $b5                         ; ROM 02F2C: feb5
    JR z,$2f50                     ; ROM 02F2E: 2820
    CP $b6                         ; ROM 02F30: feb6
    JR z,$2f48                     ; ROM 02F32: 2814
    CP $b7                         ; ROM 02F34: feb7
    JR z,$2f50                     ; ROM 02F36: 2818
    CP $b8                         ; ROM 02F38: feb8
    JR z,$2f48                     ; ROM 02F3A: 280c
    LD A,($c054)                   ; ROM 02F3C: 3a54c0
    CP $b5                         ; ROM 02F3F: feb5
    JR z,$2f4c                     ; ROM 02F41: 2809
    CP $b7                         ; ROM 02F43: feb7
    JR z,$2f4c                     ; ROM 02F45: 2805
    RET                            ; ROM 02F47: c9
    db $3E,$F8,$18,$02,$3E,$08,$80,$47,$78,$E6,$F8,$32,$13,$C3,$79,$D6 ; ROM 02F48
    db $08,$E6,$F0,$F6,$08,$32,$11,$C3,$3E,$A3,$32,$06,$DE,$06,$10,$C5 ; ROM 02F58
    db $DD,$E5,$3A,$0A,$C3,$3C,$E6,$03,$32,$0A,$C3,$CD,$9F,$36,$CD,$38 ; ROM 02F68
    db $09,$CD,$95,$0B,$DD,$E1,$C1,$10,$E6,$AF,$32,$01,$C3,$3A,$DD,$C0 ; ROM 02F78
    db $D6,$1E,$30,$01,$AF,$32,$DD,$C0,$3A,$13,$C3,$E6,$F0,$0F,$0F,$0F ; ROM 02F88
    db $0F,$6F,$3A,$11,$C3,$E6,$F0,$85,$6F,$26,$DC,$06,$03,$70,$4D,$C3 ; ROM 02F98
    db $D4,$35 ; ROM 02FA8
    LD (IX+1),2                    ; ROM 02FAA: dd360102
    LD A,$90                       ; ROM 02FAE: 3e90
    LD ($de06),A                   ; ROM 02FB0: 3206de
    RET                            ; ROM 02FB3: c9
    LD (IX+1),4                    ; ROM 02FB4: dd360104
    LD A,$99                       ; ROM 02FB8: 3e99
    LD ($de06),A                   ; ROM 02FBA: 3206de
    RET                            ; ROM 02FBD: c9
    db $3A,$BF,$C0,$B7,$C8,$AF,$32,$BF,$C0,$32,$E2,$C0,$3E,$97,$32,$06 ; ROM 02FBE
    db $DE,$C3,$26,$72,$3A,$72,$C0,$B7,$C8,$3A,$AD,$C0,$B7,$C0,$3E,$01 ; ROM 02FCE
    db $32,$AD,$C0,$3E,$A9,$32,$08,$DE,$06,$28,$C5,$3E,$05,$32,$FF,$FF ; ROM 02FDE
    db $CD,$BE,$BD,$CD,$95,$0B,$C1,$10,$F1,$21,$A0,$DC,$11,$C0,$DC,$01 ; ROM 02FEE
    db $20,$00,$ED,$B0,$3E,$05,$32,$FF,$FF,$CD,$78,$BE,$21,$A0,$DC,$11 ; ROM 02FFE
    db $C0,$DC,$06,$20,$1A,$4E,$77,$79,$12,$23,$13,$10,$F7,$CD,$CE,$0A ; ROM 0300E
    db $C3,$26,$72 ; ROM 0301E
    CALL $30bb                     ; ROM 03021: cdbb30
    RET c                          ; ROM 03024: d8
    LD A,$97                       ; ROM 03025: 3e97
    LD ($de06),A                   ; ROM 03027: 3206de
    LD A,($c041)                   ; ROM 0302A: 3a41c0
    CP 2                           ; ROM 0302D: fe02
    LD HL,$c318                    ; ROM 0302F: 2118c3
    LD A,($c0da)                   ; ROM 03032: 3adac0
    LD E,A                         ; ROM 03035: 5f
    LD A,$10                       ; ROM 03036: 3e10
    JR nz,$303b                    ; ROM 03038: 2001
    db $87 ; ROM 0303A
    ADD A,(HL)                     ; ROM 0303B: 86
    CP E                           ; ROM 0303C: bb
    JR c,$3040                     ; ROM 0303D: 3801
    db $7B ; ROM 0303F
    LD (HL),A                      ; ROM 03040: 77
    RET                            ; ROM 03041: c9
    db $3A,$30,$C3,$B7,$C0,$3E,$AA,$32,$06,$DE,$3E,$05,$18,$3B ; ROM 03042
    LD A,($c330)                   ; ROM 03050: 3a30c3
    OR A                           ; ROM 03053: b7
    RET nz                         ; ROM 03054: c0
    LD A,($c0c6)                   ; ROM 03055: 3ac6c0
    OR A                           ; ROM 03058: b7
    JR nz,$3061                    ; ROM 03059: 2006
    CALL $30bb                     ; ROM 0305B: cdbb30
    JP c,$7226                     ; ROM 0305E: da2672
    LD A,($c0c6)                   ; ROM 03061: 3ac6c0
    INC A                          ; ROM 03064: 3c
    AND 3                          ; ROM 03065: e603
    LD ($c0c6),A                   ; ROM 03067: 32c6c0
    LD (IX+1),10                   ; ROM 0306A: dd36010a
    LD A,$92                       ; ROM 0306E: 3e92
    LD ($de06),A                   ; ROM 03070: 3206de
    LD A,3                         ; ROM 03073: 3e03
    JR $308b                       ; ROM 03075: 1814
    db $3A,$30,$C3,$B7,$C0,$CD,$BB,$30,$D8,$DD,$36,$01,$0A,$3E,$93,$32 ; ROM 03077
    db $06,$DE,$3E,$04 ; ROM 03087
    LD HL,$c300                    ; ROM 0308B: 2100c3
    LD DE,$c330                    ; ROM 0308E: 1130c3
    LD BC,$30                      ; ROM 03091: 013000
    LDIR                           ; ROM 03094: edb0
    LD ($c330),A                   ; ROM 03096: 3230c3
    XOR A                          ; ROM 03099: af
    LD ($c331),A                   ; ROM 0309A: 3231c3
    LD ($c346),A                   ; ROM 0309D: 3246c3
    LD ($c344),A                   ; ROM 030A0: 3244c3
    LD ($c33b),A                   ; ROM 030A3: 323bc3
    RET                            ; ROM 030A6: c9
    db $CD,$BB,$30,$D8,$3A,$E6,$C0,$32,$90,$C0,$DD,$36,$01,$06,$3E,$94 ; ROM 030A7
    db $32,$06,$DE,$C9 ; ROM 030B7
    LD HL,$30d2                    ; ROM 030BB: 21d230
    LD A,($c0df)                   ; ROM 030BE: 3adfc0
    AND 3                          ; ROM 030C1: e603
    ADD A,L                        ; ROM 030C3: 85
    LD L,A                         ; ROM 030C4: 6f
    JR nc,$30c8                    ; ROM 030C5: 3001
    db $24 ; ROM 030C7
    LD L,(HL)                      ; ROM 030C8: 6e
    LD A,($c0db)                   ; ROM 030C9: 3adbc0
    SUB L                          ; ROM 030CC: 95
    RET c                          ; ROM 030CD: d8
    LD ($c0db),A                   ; ROM 030CE: 32dbc0
    RET                            ; ROM 030D1: c9
    db $08,$08,$20,$18 ; ROM 030D2
    LD HL,$c318                    ; ROM 030D6: 2118c3
    LD A,($c0da)                   ; ROM 030D9: 3adac0
    CP (HL)                        ; ROM 030DC: be
    RET z                          ; ROM 030DD: c8
    CALL $601c                     ; ROM 030DE: cd1c60
    XOR A                          ; ROM 030E1: af
    LD ($c0e8),A                   ; ROM 030E2: 32e8c0
    JP $7226                       ; ROM 030E5: c32672
    db $3A,$40,$C0,$B7,$C0,$2A,$C2,$C0,$CD,$E2,$18,$CD,$78,$1F,$21,$30 ; ROM 030E8
    db $C3,$11,$31,$C3,$01,$CF,$05,$36,$00,$ED,$B0,$CD,$0B,$19,$3E,$08 ; ROM 030F8
    db $32,$1D,$C0,$AF,$32,$E9,$C0,$CD,$26,$72 ; ROM 03108
    LD A,1                         ; ROM 03112: 3e01
    LD ($c30a),A                   ; ROM 03114: 320ac3
    LD HL,$7000                    ; ROM 03117: 210070
    LD ($c310),HL                  ; ROM 0311A: 2210c3
    LD HL,$8800                    ; ROM 0311D: 210088
    LD ($c312),HL                  ; ROM 03120: 2212c3
    RET                            ; ROM 03123: c9
    db $3E,$A4,$32,$06,$DE,$3A,$40,$C0,$B7,$C0,$21,$00,$DC,$01,$00,$A0 ; ROM 03124
    db $7E,$FE,$3F,$20,$03,$36,$3A,$0C,$23,$10,$F5,$79,$B7,$CA,$D8,$31 ; ROM 03134
    db $2A,$D0,$CA,$29,$29,$29,$29,$29,$EB,$EF,$21,$00,$D1,$06,$20,$DB ; ROM 03144
    db $BE,$F5,$F1,$77,$23,$10,$F8,$21,$00,$D1,$11,$20,$D1,$01,$60,$00 ; ROM 03154
    db $ED,$B0,$2A,$F8,$CA,$29,$29,$29,$29,$29,$EB,$01,$7F,$08,$CD,$95 ; ROM 03164
    db $0B,$CD,$95,$0B,$C5,$D5,$21,$00,$D1,$06,$00,$CB,$B2,$EF,$D5,$DB ; ROM 03174
    db $BE,$A1,$5F,$79,$2F,$A6,$B3,$D1,$CB,$F2,$F5,$EF,$F1,$D3,$BE,$23 ; ROM 03184
    db $13,$04,$78,$E6,$03,$20,$08,$CB,$09,$CB,$09,$CB,$09,$CB,$09,$78 ; ROM 03194
    db $FE,$80,$20,$D7,$D1,$C1,$CB,$09,$10,$C4,$DD,$E5,$DD,$21,$00,$C6 ; ROM 031A4
    db $06,$10,$C5,$DD,$7E,$00,$B7,$28,$0E,$DD,$CB,$03,$46,$20,$05,$CD ; ROM 031B4
    db $EB,$57,$18,$03,$CD,$A7,$27,$01,$30,$00,$DD,$09,$C1,$10,$E3,$DD ; ROM 031C4
    db $E1,$AF,$18,$05,$3A,$AC,$C0,$B7,$C0,$3C,$32,$AC,$C0,$CD,$50,$1A ; ROM 031D4
    db $C3,$E2,$1D,$3A,$40,$C0,$B7,$C0,$CD,$DA,$20,$3E,$02,$32,$FF,$FF ; ROM 031E4
    db $CD,$7C,$83,$21,$71,$BD,$11,$40,$7F,$3E,$05,$CD,$27,$03,$2A,$B9 ; ROM 031F4
    db $C0,$E5,$CD,$44,$04,$21,$00,$DC,$11,$00,$94,$01,$A0,$00,$ED,$B0 ; ROM 03204
    db $CD,$3A,$04,$21,$10,$00,$22,$B9,$C0,$06,$0F,$C5,$CD,$0B,$19,$0E ; ROM 03214
    db $00,$06,$00,$3E,$02,$32,$FF,$FF,$CD,$4D,$84,$04,$78,$FE,$08,$38 ; ROM 03224
    db $F2,$0C,$79,$FE,$05,$38,$EA,$C1,$2A,$B9,$C0,$23,$22,$B9,$C0,$10 ; ROM 03234
    db $DA,$2A,$B9,$C0,$23,$22,$B9,$C0,$7C,$B7,$28,$CD,$E1,$22,$B9,$C0 ; ROM 03244
    db $CD,$44,$04,$21,$00,$94,$11,$00,$DC,$01,$A0,$00,$ED,$B0,$CD,$3A ; ROM 03254
    db $04,$3E,$03,$32,$BF,$DC,$CD,$95,$0B,$CD,$60,$0A,$3E,$02,$32,$FF ; ROM 03264
    db $FF,$DD,$E5,$CD,$EC,$83,$DD,$E1,$CD,$78,$09,$3A,$21,$C0,$E6,$30 ; ROM 03274
    db $28,$E4,$CD,$DA,$20,$CD,$26,$72,$CD,$EF,$16,$C3,$E2,$1D ; ROM 03284
    INC (IX+1)                     ; ROM 03292: dd3401
    LD A,(IX+4)                    ; ROM 03295: dd7e04
    OR A                           ; ROM 03298: b7
    JR nz,$3312                    ; ROM 03299: 2077
    LD ($c314),A                   ; ROM 0329B: 3214c3
    LD ($c315),A                   ; ROM 0329E: 3215c3
    LD ($c316),A                   ; ROM 032A1: 3216c3
    LD ($c317),A                   ; ROM 032A4: 3217c3
    LD D,A                         ; ROM 032A7: 57
    LD E,(IX+10)                   ; ROM 032A8: dd5e0a
    LD A,($c068)                   ; ROM 032AB: 3a68c0
    OR A                           ; ROM 032AE: b7
    JP p,$32b8                     ; ROM 032AF: f2b832
    db $E6,$03,$32,$68,$C0,$5F ; ROM 032B2
    LD HL,$3315                    ; ROM 032B8: 211533
    ADD HL,DE                      ; ROM 032BB: 19
    LD A,($c020)                   ; ROM 032BC: 3a20c0
    AND (HL)                       ; ROM 032BF: a6
    JR nz,$32c5                    ; ROM 032C0: 2003
    LD A,($c020)                   ; ROM 032C2: 3a20c0
    RRCA                           ; ROM 032C5: 0f
    JR c,$32d4                     ; ROM 032C6: 380c
    INC D                          ; ROM 032C8: 14
    RRCA                           ; ROM 032C9: 0f
    JR c,$32d4                     ; ROM 032CA: 3808
    INC D                          ; ROM 032CC: 14
    RRCA                           ; ROM 032CD: 0f
    JR c,$32d4                     ; ROM 032CE: 3804
    INC D                          ; ROM 032D0: 14
    RRCA                           ; ROM 032D1: 0f
    JR nc,$3312                    ; ROM 032D2: 303e
    LD (IX+10),D                   ; ROM 032D4: dd720a
    LD A,($c020)                   ; ROM 032D7: 3a20c0
    AND $20                        ; ROM 032DA: e620
    JR nz,$3312                    ; ROM 032DC: 2034
    LD A,($c041)                   ; ROM 032DE: 3a41c0
    LD C,A                         ; ROM 032E1: 4f
    ADD A,A                        ; ROM 032E2: 87
    ADD A,A                        ; ROM 032E3: 87
    ADD A,A                        ; ROM 032E4: 87
    ADD A,A                        ; ROM 032E5: 87
    ADD A,C                        ; ROM 032E6: 81
    LD C,A                         ; ROM 032E7: 4f
    LD B,0                         ; ROM 032E8: 0600
    LD HL,$33db                    ; ROM 032EA: 21db33
    LD A,($c0ee)                   ; ROM 032ED: 3aeec0
    OR A                           ; ROM 032F0: b7
    JR z,$32f6                     ; ROM 032F1: 2803
    db $21,$41,$34 ; ROM 032F3
    ADD HL,BC                      ; ROM 032F6: 09
    LD A,(HL)                      ; ROM 032F7: 7e
    LD (IX+4),A                    ; ROM 032F8: dd7704
    INC HL                         ; ROM 032FB: 23
    LD ($c069),HL                  ; ROM 032FC: 2269c0
    LD IY,$c048                    ; ROM 032FF: fd2148c0
    LD A,D                         ; ROM 03303: 7a
    ADD A,A                        ; ROM 03304: 87
    LD HL,$3319                    ; ROM 03305: 211933
    RST $18                        ; ROM 03308: df
    LD A,(IX+11)                   ; ROM 03309: dd7e0b
    INC A                          ; ROM 0330C: 3c
    AND 3                          ; ROM 0330D: e603
    LD (IX+11),A                   ; ROM 0330F: dd770b
    JP $369f                       ; ROM 03312: c39f36
    db $01,$02,$04,$08,$21,$33,$41,$33,$60,$33,$8D,$33 ; ROM 03315
    CALL $38ac                     ; ROM 03321: cdac38
    BIT 7,(IY+3)                   ; ROM 03324: fdcb037e
    JR nz,$3335                    ; ROM 03328: 200b
    BIT 7,(IY+5)                   ; ROM 0332A: fdcb057e
    JR nz,$3359                    ; ROM 0332E: 2029
    LD E,0                         ; ROM 03330: 1e00
    JP $33ba                       ; ROM 03332: c3ba33
    db $FD,$CB,$05,$7E,$C0,$FD,$CB,$0F,$7E,$C0,$18,$52 ; ROM 03335
    CALL $38f6                     ; ROM 03341: cdf638
    BIT 7,(IY+$15)                 ; ROM 03344: fdcb157e
    JR nz,$3354                    ; ROM 03348: 200a
    BIT 7,(IY+$13)                 ; ROM 0334A: fdcb137e
    JR nz,$333a                    ; ROM 0334E: 20ea
    LD E,1                         ; ROM 03350: 1e01
    JR $33ba                       ; ROM 03352: 1866
    db $FD,$CB,$13,$7E,$C0,$FD,$CB,$09,$7E,$C0,$18,$06 ; ROM 03354
    BIT 7,(IY+9)                   ; ROM 03360: fdcb097e
    JR nz,$336a                    ; ROM 03364: 2004
    LD E,2                         ; ROM 03366: 1e02
    JR $33ba                       ; ROM 03368: 1850
    BIT 7,(IY+1)                   ; ROM 0336A: fdcb017e
    JR nz,$337c                    ; ROM 0336E: 200c
    db $FD,$CB,$03,$7E,$20,$06,$FD,$CB,$05,$7E,$28,$B4 ; ROM 03370
    BIT 7,(IY+$11)                 ; ROM 0337C: fdcb117e
    RET nz                         ; ROM 03380: c0
    db $FD,$CB,$13,$7E,$C0,$FD,$CB,$15,$7E,$C0,$18,$C3,$FD,$CB,$0F,$7E ; ROM 03381
    db $20,$04,$1E,$03,$18,$23,$FD,$CB,$07,$7E,$20,$0C,$FD,$CB,$05,$7E ; ROM 03391
    db $20,$06,$FD,$CB,$03,$7E,$28,$87,$FD,$CB,$17,$7E,$C0,$FD,$CB,$15 ; ROM 033A1
    db $7E,$C0,$FD,$CB,$13,$7E,$C0,$18,$96 ; ROM 033B1
    LD A,D                         ; ROM 033BA: 7a
    CP E                           ; ROM 033BB: bb
    JR z,$33c3                     ; ROM 033BC: 2805
    db $F6,$80,$32,$68,$C0 ; ROM 033BE
    LD (IX+10),E                   ; ROM 033C3: dd730a
    LD D,0                         ; ROM 033C6: 1600
    LD HL,($c069)                  ; ROM 033C8: 2a69c0
    EX DE,HL                       ; ROM 033CB: eb
    ADD HL,HL                      ; ROM 033CC: 29
    ADD HL,HL                      ; ROM 033CD: 29
    ADD HL,DE                      ; ROM 033CE: 19
    LD DE,$c314                    ; ROM 033CF: 1114c3
    LDI                            ; ROM 033D2: eda0
    LDI                            ; ROM 033D4: eda0
    LDI                            ; ROM 033D6: eda0
    LDI                            ; ROM 033D8: eda0
    RET                            ; ROM 033DA: c9
    db $05,$67,$FE,$00,$00,$9A,$01,$00,$00,$00,$00,$67,$FE,$00,$00,$9A ; ROM 033DB
    db $01,$0A,$34,$FF,$00,$00,$CD,$00,$00,$00,$00,$00,$34,$FF,$00,$00 ; ROM 033EB
    db $CD,$00,$07,$DC,$FE,$00,$00,$25,$01,$00,$00,$00,$00,$DC,$FE,$00 ; ROM 033FB
    db $00,$25,$01,$06,$AB,$FE,$00,$00,$56,$01,$00,$00,$00,$00,$AB,$FE ; ROM 0340B
    db $00,$00,$56,$01,$07,$DC,$FE,$00,$00,$25,$01,$00,$00,$00,$00,$DC ; ROM 0341B
    db $FE,$00,$00,$25,$01,$0C,$56,$FF,$00,$00,$AB,$00,$00,$00,$00,$00 ; ROM 0342B
    db $56,$FF,$00,$00,$AB,$00,$04,$00,$FE,$00,$00,$01,$02,$00,$00,$00 ; ROM 0343B
    db $00,$00,$FE,$00,$00,$01,$02,$06,$AB,$FE,$00,$00,$56,$01,$00,$00 ; ROM 0344B
    db $00,$00,$AB,$FE,$00,$00,$56,$01,$05,$67,$FE,$00,$00,$9A,$01,$00 ; ROM 0345B
    db $00,$00,$00,$67,$FE,$00,$00,$9A,$01,$04,$00,$FE,$00,$00,$01,$02 ; ROM 0346B
    db $00,$00,$00,$00,$00,$FE,$00,$00,$01,$02,$06,$AB,$FE,$00,$00,$56 ; ROM 0347B
    db $01,$00,$00,$00,$00,$AB,$FE,$00,$00,$56,$01,$0A,$34,$FF,$00,$00 ; ROM 0348B
    db $CD,$00,$00,$00,$00,$00,$34,$FF,$00,$00,$CD,$00 ; ROM 0349B
    LD (IX+14),$ff                 ; ROM 034A7: dd360eff
    INC (IX+1)                     ; ROM 034AB: dd3401
    LD A,($c0ee)                   ; ROM 034AE: 3aeec0
    OR A                           ; ROM 034B1: b7
    LD HL,$3635                    ; ROM 034B2: 213536
    JR z,$34ba                     ; ROM 034B5: 2803
    db $21,$42,$36 ; ROM 034B7
    JP $3661                       ; ROM 034BA: c36136
    LD (IX+14),$ff                 ; ROM 034BD: dd360eff
    INC (IX+1)                     ; ROM 034C1: dd3401
    LD A,($c0ee)                   ; ROM 034C4: 3aeec0
    OR A                           ; ROM 034C7: b7
    LD HL,$364b                    ; ROM 034C8: 214b36
    JR z,$34d0                     ; ROM 034CB: 2803
    db $21,$58,$36 ; ROM 034CD
    CALL $3661                     ; ROM 034D0: cd6136
    LD A,($c040)                   ; ROM 034D3: 3a40c0
    OR A                           ; ROM 034D6: b7
    RET nz                         ; ROM 034D7: c0
    LD A,($c30e)                   ; ROM 034D8: 3a0ec3
    CP 7                           ; ROM 034DB: fe07
    RET nz                         ; ROM 034DD: c0
    LD A,($c30a)                   ; ROM 034DE: 3a0ac3
    ADD A,A                        ; ROM 034E1: 87
    ADD A,A                        ; ROM 034E2: 87
    ADD A,A                        ; ROM 034E3: 87
    LD L,A                         ; ROM 034E4: 6f
    LD A,($c06b)                   ; ROM 034E5: 3a6bc0
    ADD A,A                        ; ROM 034E8: 87
    OR L                           ; ROM 034E9: b5
    LD HL,$34f0                    ; ROM 034EA: 21f034
    JP $0018                       ; ROM 034ED: c31800
    db $10,$35,$21,$35,$2C,$35,$37,$35,$3C,$35,$4D,$35,$58,$35,$58,$35 ; ROM 034F0
    db $58,$35,$59,$35,$5E,$35,$69,$35,$58,$35,$74,$35,$79,$35,$84,$35 ; ROM 03500
    db $3A,$11,$C3,$FE,$18,$D8,$01,$E0,$F0,$CD,$8D,$35,$01,$E0,$00,$18 ; ROM 03510
    db $6C,$3A,$11,$C3,$FE,$18,$D8,$01,$E0,$F8,$18,$61,$01,$E8,$F0,$CD ; ROM 03520
    db $8D,$35,$01,$E8,$00,$18,$56 ; ROM 03530
    LD BC,$f8e8                    ; ROM 03537: 01e8f8
    JR $358d                       ; ROM 0353A: 1851
    db $3A,$11,$C3,$FE,$A0,$D0,$01,$00,$F0,$CD,$8D,$35,$01,$00,$00,$18 ; ROM 0353C
    db $40 ; ROM 0354C
    LD A,($c311)                   ; ROM 0354D: 3a11c3
    CP $a0                         ; ROM 03550: fea0
    RET nc                         ; ROM 03552: d0
    LD BC,$f800                    ; ROM 03553: 0100f8
    JR $358d                       ; ROM 03556: 1835
    db $C9,$01,$F0,$E8,$18,$2F,$01,$E8,$F0,$CD,$8D,$35,$01,$F8,$F0,$18 ; ROM 03558
    db $24,$01,$E8,$E8,$CD,$8D,$35,$01,$F8,$E8,$18,$19,$01,$F0,$08,$18 ; ROM 03568
    db $14,$01,$E8,$00,$CD,$8D,$35,$01,$F8,$00,$18,$09,$01,$E8,$08,$CD ; ROM 03578
    db $8D,$35,$01,$F8,$08 ; ROM 03588
    LD IY,$3620                    ; ROM 0358D: fd212036
    CALL $232f                     ; ROM 03591: cd2f23
    LD DE,4                        ; ROM 03594: 110400
    LD A,(IY)                      ; ROM 03597: fd7e00
    OR A                           ; ROM 0359A: b7
    RET z                          ; ROM 0359B: c8
    CP (HL)                        ; ROM 0359C: be
    JR z,$35a3                     ; ROM 0359D: 2804
    ADD IY,DE                      ; ROM 0359F: fd19
    JR $3597                       ; ROM 035A1: 18f4
    db $FD,$7E,$01,$E5,$CD,$B7,$35,$E1,$11,$10,$00,$19,$7E,$FD,$BE,$02 ; ROM 035A3
    db $C0,$FD,$7E,$03,$47,$4D,$77,$3A,$6E,$C0,$B9,$20,$0F,$CD,$D4,$35 ; ROM 035B3
    db $CD,$3D,$19,$C0,$3E,$A8,$32,$08,$DE,$C3,$7C,$1A,$3E,$9B,$32,$06 ; ROM 035C3
    db $DE,$68,$26,$00,$29,$29,$29,$11,$00,$C9,$19,$E5,$79,$E6,$0F,$87 ; ROM 035D3
    db $87,$5F,$16,$00,$79,$E6,$F0,$6F,$62,$29,$29,$29,$19,$11,$00,$D6 ; ROM 035E3
    db $19,$EB,$2A,$34,$C0,$3E,$02,$77,$2C,$77,$2C,$77,$2C,$73,$2C,$72 ; ROM 035F3
    db $2C,$22,$34,$C0,$E1,$ED,$A0,$ED,$A0,$ED,$A0,$ED,$A0,$3E,$3C,$83 ; ROM 03603
    db $5F,$30,$01,$14,$ED,$A0,$ED,$A0,$ED,$A0,$ED,$A0,$C9,$80,$17,$27 ; ROM 03613
    db $01,$81,$03,$28,$03,$82,$32,$29,$00,$83,$33,$39,$3A,$84,$32,$29 ; ROM 03623
    db $00,$00,$04,$04,$05,$05,$05,$05,$05,$05,$05,$04,$04,$04,$00,$04 ; ROM 03633
    db $05,$05,$05,$05,$05,$04,$04,$00,$04,$04,$04,$05,$05,$05,$06,$06 ; ROM 03643
    db $06,$07,$07,$07,$00,$04,$04,$05,$05,$06,$06,$07,$07,$00 ; ROM 03653
    LD A,($c020)                   ; ROM 03661: 3a20c0
    AND 15                         ; ROM 03664: e60f
    CP 1                           ; ROM 03666: fe01
    JR nz,$366d                    ; ROM 03668: 2003
    XOR A                          ; ROM 0366A: af
    JR $3683                       ; ROM 0366B: 1816
    CP 2                           ; ROM 0366D: fe02
    JR nz,$3675                    ; ROM 0366F: 2004
    db $3E,$01,$18,$0E ; ROM 03671
    CP 4                           ; ROM 03675: fe04
    JR nz,$367d                    ; ROM 03677: 2004
    db $3E,$02,$18,$06 ; ROM 03679
    CP 8                           ; ROM 0367D: fe08
    JR nz,$3686                    ; ROM 0367F: 2005
    db $3E,$03 ; ROM 03681
    LD ($c30a),A                   ; ROM 03683: 320ac3
    LD A,($c30e)                   ; ROM 03686: 3a0ec3
    INC A                          ; ROM 03689: 3c
    LD ($c30e),A                   ; ROM 0368A: 320ec3
    ADD A,L                        ; ROM 0368D: 85
    LD L,A                         ; ROM 0368E: 6f
    JR nc,$3692                    ; ROM 0368F: 3001
    db $24 ; ROM 03691
    LD A,(HL)                      ; ROM 03692: 7e
    LD ($c30b),A                   ; ROM 03693: 320bc3
    OR A                           ; ROM 03696: b7
    JR nz,$369f                    ; ROM 03697: 2006
    LD ($c301),A                   ; ROM 03699: 3201c3
    LD ($c30e),A                   ; ROM 0369C: 320ec3
    LD A,($c041)                   ; ROM 0369F: 3a41c0
    CP 3                           ; ROM 036A2: fe03
    JR z,$36fc                     ; ROM 036A4: 2856
    LD C,0                         ; ROM 036A6: 0e00
    LD A,($c0df)                   ; ROM 036A8: 3adfc0
    DEC A                          ; ROM 036AB: 3d
    JR nz,$36b3                    ; ROM 036AC: 2005
    LD A,($c0e1)                   ; ROM 036AE: 3ae1c0
    INC A                          ; ROM 036B1: 3c
    LD C,A                         ; ROM 036B2: 4f
    LD A,($c041)                   ; ROM 036B3: 3a41c0
    CP 2                           ; ROM 036B6: fe02
    JR nz,$36bc                    ; ROM 036B8: 2002
    SET 2,C                        ; ROM 036BA: cbd1
    LD HL,$80a0                    ; ROM 036BC: 21a080
    LD A,C                         ; ROM 036BF: 79
    ADD A,A                        ; ROM 036C0: 87
    ADD A,A                        ; ROM 036C1: 87
    ADD A,A                        ; ROM 036C2: 87
    ADD A,L                        ; ROM 036C3: 85
    LD L,A                         ; ROM 036C4: 6f
    JR nc,$36c8                    ; ROM 036C5: 3001
    INC H                          ; ROM 036C7: 24
    LD ($c308),HL                  ; ROM 036C8: 2208c3
    LD DE,$3b67                    ; ROM 036CB: 11673b
    LD A,C                         ; ROM 036CE: 79
    ADD A,A                        ; ROM 036CF: 87
    ADD A,A                        ; ROM 036D0: 87
    OR (IX+10)                     ; ROM 036D1: ddb60a
    ADD A,A                        ; ROM 036D4: 87
    ADD A,A                        ; ROM 036D5: 87
    ADD A,A                        ; ROM 036D6: 87
    OR (IX+11)                     ; ROM 036D7: ddb60b
    LD L,A                         ; ROM 036DA: 6f
    LD H,0                         ; ROM 036DB: 2600
    LD A,($c041)                   ; ROM 036DD: 3a41c0
    CP 5                           ; ROM 036E0: fe05
    JR nz,$36e8                    ; ROM 036E2: 2004
    LD A,L                         ; ROM 036E4: 7d
    AND $e7                        ; ROM 036E5: e6e7
    LD L,A                         ; ROM 036E7: 6f
    ADD HL,HL                      ; ROM 036E8: 29
    ADD HL,DE                      ; ROM 036E9: 19
    LD A,(HL)                      ; ROM 036EA: 7e
    INC HL                         ; ROM 036EB: 23
    LD H,(HL)                      ; ROM 036EC: 66
    LD L,A                         ; ROM 036ED: 6f
    LD ($c043),HL                  ; ROM 036EE: 2243c0
    LD A,4                         ; ROM 036F1: 3e04
    BIT 2,C                        ; ROM 036F3: cb51
    JR z,$36f8                     ; ROM 036F5: 2801
    INC A                          ; ROM 036F7: 3c
    LD ($c042),A                   ; ROM 036F8: 3242c0
    RET                            ; ROM 036FB: c9
    LD A,($c30b)                   ; ROM 036FC: 3a0bc3
    AND 1                          ; ROM 036FF: e601
    LD L,A                         ; ROM 03701: 6f
    LD A,($c30a)                   ; ROM 03702: 3a0ac3
    ADD A,A                        ; ROM 03705: 87
    OR L                           ; ROM 03706: b5
    ADD A,A                        ; ROM 03707: 87
    LD HL,$3d67                    ; ROM 03708: 21673d
    RST 8                          ; ROM 0370B: cf
    LD ($c043),HL                  ; ROM 0370C: 2243c0
    LD A,5                         ; ROM 0370F: 3e05
    LD ($c042),A                   ; ROM 03711: 3242c0
    LD (IX+8),$a0                  ; ROM 03714: dd3608a0
    LD (IX+9),$80                  ; ROM 03718: dd360980
    RET                            ; ROM 0371C: c9
    db $3E,$9A,$32,$06,$DE,$CD,$7C,$2D,$21,$00,$00,$22,$16,$C3,$22,$14 ; ROM 0371D
    db $C3,$3E,$5A,$32,$04,$C3,$DD,$34,$01,$AF,$32,$05,$C3,$32,$1D,$C3 ; ROM 0372D
    db $32,$0B,$C3,$DD,$CB,$03,$8E,$DD,$CB,$03,$C6,$3A,$2F,$C0,$E6,$02 ; ROM 0373D
    db $21,$77,$3D,$CF,$CD,$0C,$37,$21,$08,$DE,$3A,$04,$C3,$FE,$50,$20 ; ROM 0374D
    db $02,$36,$B0,$B7,$C0,$DD,$CB,$03,$86,$3E,$14,$32,$1D,$C0,$C9 ; ROM 0375D
    LD HL,$83e3                    ; ROM 0376C: 21e383
    LD ($c308),HL                  ; ROM 0376F: 2208c3
    LD (IX+14),$ff                 ; ROM 03772: dd360eff
    LD (IX+11),0                   ; ROM 03776: dd360b00
    INC (IX+1)                     ; ROM 0377A: dd3401
    LD A,($c30e)                   ; ROM 0377D: 3a0ec3
    INC A                          ; ROM 03780: 3c
    LD ($c30e),A                   ; ROM 03781: 320ec3
    CP 3                           ; ROM 03784: fe03
    JR nz,$378c                    ; ROM 03786: 2004
    LD (IX+1),0                    ; ROM 03788: dd360100
    LD A,($c30a)                   ; ROM 0378C: 3a0ac3
    ADD A,A                        ; ROM 0378F: 87
    ADD A,A                        ; ROM 03790: 87
    LD C,A                         ; ROM 03791: 4f
    LD A,($c041)                   ; ROM 03792: 3a41c0
    CP 2                           ; ROM 03795: fe02
    JR nz,$379b                    ; ROM 03797: 2002
    db $CB,$C9 ; ROM 03799
    LD B,0                         ; ROM 0379B: 0600
    LD HL,$3d7b                    ; ROM 0379D: 217b3d
    ADD HL,BC                      ; ROM 037A0: 09
    LD A,(HL)                      ; ROM 037A1: 7e
    INC HL                         ; ROM 037A2: 23
    LD H,(HL)                      ; ROM 037A3: 66
    LD L,A                         ; ROM 037A4: 6f
    LD ($c043),HL                  ; ROM 037A5: 2243c0
    LD A,4                         ; ROM 037A8: 3e04
    BIT 1,C                        ; ROM 037AA: cb49
    JR z,$37af                     ; ROM 037AC: 2801
    db $3C ; ROM 037AE
    LD ($c042),A                   ; ROM 037AF: 3242c0
    RET                            ; ROM 037B2: c9
    db $AF,$32,$05,$C3,$32,$1D,$C3,$DD,$34,$01,$3A,$90,$C0,$B7,$20,$03 ; ROM 037B3
    db $32,$01,$C3,$DD,$36,$08,$A0,$DD,$36,$09,$80,$21,$41,$A2,$22,$43 ; ROM 037C3
    db $C0,$3E,$04,$32,$42,$C0,$C9,$FD,$7E,$0A,$FE,$02,$30,$0A,$3A,$11 ; ROM 037D3
    db $C3,$FD,$BE,$11,$30,$1F,$18,$0A,$3A,$13,$C3,$FD,$BE,$13,$30,$37 ; ROM 037E3
    db $18,$26,$21,$4B,$C0,$3A,$4D,$C0,$B6,$47,$21,$11,$C3,$7E,$FE,$11 ; ROM 037F3
    db $D8,$16,$F8,$18,$2F,$21,$5B,$C0,$3A,$5D,$C0,$B6,$47,$21,$11,$C3 ; ROM 03803
    db $7E,$FE,$A0,$D0,$16,$08,$18,$1C,$ED,$4B,$50,$C0,$21,$13,$C3,$7E ; ROM 03813
    db $FE,$11,$D8,$16,$F8,$18,$0D,$ED,$4B,$56,$C0,$21,$13,$C3,$7E,$FE ; ROM 03823
    db $F0,$D0,$16,$08,$0E,$04,$1E,$F8,$3A,$13,$C3,$81,$A3,$32,$13,$C3 ; ROM 03833
    db $3A,$11,$C3,$81,$A3,$32,$11,$C3,$AF,$32,$0B,$C3,$32,$04,$C3,$32 ; ROM 03843
    db $01,$C3,$32,$16,$C3,$32,$17,$C3,$32,$14,$C3,$32,$15,$C3,$32,$12 ; ROM 03853
    db $C3,$32,$10,$C3,$CB,$78,$C0,$7E,$82,$77,$C9 ; ROM 03863
    LD BC,4                        ; ROM 0386E: 010400
    ADD IY,BC                      ; ROM 03871: fd09
    LD A,($c052)                   ; ROM 03873: 3a52c0
    LD L,(IY-4)                    ; ROM 03876: fd6efc
    LD H,(IY-3)                    ; ROM 03879: fd66fd
    LD C,(IY-2)                    ; ROM 0387C: fd4efe
    CPIR                           ; ROM 0387F: edb1
    JR z,$38a8                     ; ROM 03881: 2825
    JR $3899                       ; ROM 03883: 1814
    LD BC,4                        ; ROM 03885: 010400
    ADD IY,BC                      ; ROM 03888: fd09
    LD A,($c052)                   ; ROM 0388A: 3a52c0
    LD L,(IY-4)                    ; ROM 0388D: fd6efc
    LD H,(IY-3)                    ; ROM 03890: fd66fd
    LD C,(IY-2)                    ; ROM 03893: fd4efe
    CPIR                           ; ROM 03896: edb1
    RET nz                         ; ROM 03898: c0
    LD A,($c054)                   ; ROM 03899: 3a54c0
    LD L,(IY-4)                    ; ROM 0389C: fd6efc
    LD H,(IY-3)                    ; ROM 0389F: fd66fd
    LD C,(IY-2)                    ; ROM 038A2: fd4efe
    CPIR                           ; ROM 038A5: edb1
    RET nz                         ; ROM 038A7: c0
    LD A,(IY-1)                    ; ROM 038A8: fd7eff
    RET                            ; ROM 038AB: c9
    LD A,($c040)                   ; ROM 038AC: 3a40c0
    OR A                           ; ROM 038AF: b7
    RET nz                         ; ROM 038B0: c0
    LD A,($c0ed)                   ; ROM 038B1: 3aedc0
    OR A                           ; ROM 038B4: b7
    RET z                          ; ROM 038B5: c8
    db $3A,$6B,$C0,$FE,$03,$C0,$01,$F0,$00,$CD,$2F,$23,$FE,$02,$C0,$06 ; ROM 038B6
    db $01,$36,$6D,$7D,$D6,$10,$6F,$38,$0E,$7E,$FE,$0C,$20,$09,$36,$6C ; ROM 038C6
    db $04,$7D,$D6,$10,$6F,$30,$F2,$CB,$20,$0E,$03,$ED,$43,$98,$C0,$3A ; ROM 038D6
    db $11,$C3,$D6,$10,$32,$9A,$C0,$3A,$13,$C3,$D6,$08,$32,$9B,$C0,$C9 ; ROM 038E6
    LD A,($c040)                   ; ROM 038F6: 3a40c0
    OR A                           ; ROM 038F9: b7
    RET nz                         ; ROM 038FA: c0
    LD A,($c0ed)                   ; ROM 038FB: 3aedc0
    OR A                           ; ROM 038FE: b7
    RET z                          ; ROM 038FF: c8
    db $3A,$6B,$C0,$3D,$C0,$01,$00,$00,$CD,$2F,$23,$FE,$0C,$C0,$01,$6C ; ROM 03900
    db $00,$7E,$71,$04,$FE,$02,$20,$03,$34,$18,$08,$7D,$C6,$10,$6F,$FE ; ROM 03910
    db $A0,$38,$EE,$CB,$20,$0E,$04,$ED,$43,$98,$C0,$3A,$11,$C3,$32,$9A ; ROM 03920
    db $C0,$3A,$13,$C3,$D6,$08,$32,$9B,$C0,$C9 ; ROM 03930
    LD A,(IX+1)                    ; ROM 0393A: dd7e01
    ADD A,A                        ; ROM 0393D: 87
    LD HL,$3944                    ; ROM 0393E: 214439
    JP $0018                       ; ROM 03941: c31800
    db $48,$39,$8D,$39 ; ROM 03944
    LD (IX+3),3                    ; ROM 03948: dd360303
    LD HL,$8411                    ; ROM 0394C: 211184
    LD DE,8                        ; ROM 0394F: 110800
    LD A,($c0e4)                   ; ROM 03952: 3ae4c0
    DEC A                          ; ROM 03955: 3d
    JR z,$3959                     ; ROM 03956: 2801
    ADD HL,DE                      ; ROM 03958: 19
    LD (IX+8),L                    ; ROM 03959: dd7508
    LD (IX+9),H                    ; ROM 0395C: dd7409
    LD (IX+12),4                   ; ROM 0395F: dd360c04
    LD (IX+13),1                   ; ROM 03963: dd360d01
    LD A,(IX+10)                   ; ROM 03967: dd7e0a
    ADD A,A                        ; ROM 0396A: 87
    LD HL,$39bc                    ; ROM 0396B: 21bc39
    RST 8                          ; ROM 0396E: cf
    LD (IX+$15),L                  ; ROM 0396F: dd7515
    LD (IX+$17),H                  ; ROM 03972: dd7417
    LD A,(IX+10)                   ; ROM 03975: dd7e0a
    ADD A,A                        ; ROM 03978: 87
    LD HL,$39c4                    ; ROM 03979: 21c439
    RST 8                          ; ROM 0397C: cf
    ADD A,(IX+$11)                 ; ROM 0397D: dd8611
    LD (IX+$11),A                  ; ROM 03980: dd7711
    LD A,H                         ; ROM 03983: 7c
    ADD A,(IX+$13)                 ; ROM 03984: dd8613
    LD (IX+$13),A                  ; ROM 03987: dd7713
    INC (IX+1)                     ; ROM 0398A: dd3401
    LD (IX+4),2                    ; ROM 0398D: dd360402
    LD BC,0                        ; ROM 03991: 010000
    CALL $230e                     ; ROM 03994: cd0e23
    LD A,D                         ; ROM 03997: 7a
    AND $e0                        ; ROM 03998: e6e0
    CP $80                         ; ROM 0399A: fe80
    JP z,$57eb                     ; ROM 0399C: caeb57
    CP $a0                         ; ROM 0399F: fea0
    JP z,$57eb                     ; ROM 039A1: caeb57
    LD A,(IX+$13)                  ; ROM 039A4: dd7e13
    CP $f8                         ; ROM 039A7: fef8
    JP nc,$57eb                    ; ROM 039A9: d2eb57
    CP 8                           ; ROM 039AC: fe08
    JP c,$57eb                     ; ROM 039AE: daeb57
    LD A,(IX+$11)                  ; ROM 039B1: dd7e11
    ADD A,8                        ; ROM 039B4: c608
    CP $a8                         ; ROM 039B6: fea8
    JP nc,$57eb                    ; ROM 039B8: d2eb57
    RET                            ; ROM 039BB: c9
    db $FD,$00,$03,$00,$00,$FD,$00,$03,$F8,$00,$00,$00,$FA,$F8,$FA,$08 ; ROM 039BC
    db $DD,$7E,$01,$87,$21,$D6,$39,$C3,$18,$00,$DA,$39,$16,$3A,$DD,$36 ; ROM 039CC
    db $03,$03,$DD,$36,$08,$8D,$DD,$36,$09,$3D,$DD,$36,$0C,$02,$DD,$36 ; ROM 039DC
    db $0D,$01,$2A,$E0,$C0,$11,$9E,$2D,$26,$00,$19,$7E,$DD,$77,$19,$DD ; ROM 039EC
    db $7E,$0A,$87,$21,$1F,$3A,$CF,$DD,$75,$15,$DD,$74,$17,$DD,$35,$11 ; ROM 039FC
    db $DD,$35,$11,$DD,$34,$01,$DD,$36,$04,$08,$DD,$7E,$04,$B7,$CA,$EB ; ROM 03A0C
    db $57,$18,$85,$FC,$00,$04,$00,$00,$FC,$00,$04,$DD,$7E,$01,$87,$21 ; ROM 03A1C
    db $31,$3A,$C3,$18,$00,$35,$3A,$5A,$3A,$DD,$36,$03,$03,$DD,$36,$08 ; ROM 03A2C
    db $61,$DD,$36,$09,$84,$DD,$36,$0C,$04,$DD,$36,$0D,$02,$DD,$7E,$0A ; ROM 03A3C
    db $87,$21,$92,$3A,$CF,$DD,$75,$15,$DD,$74,$17,$DD,$34,$01,$DD,$36 ; ROM 03A4C
    db $04,$02,$01,$F8,$00,$CD,$0E,$23,$7A,$E6,$80,$C2,$EB,$57,$DD,$7E ; ROM 03A5C
    db $13,$FE,$F8,$D2,$EB,$57,$FE,$08,$DA,$EB,$57,$DD,$7E,$11,$C6,$08 ; ROM 03A6C
    db $FE,$A9,$D2,$EB,$57,$ED,$5B,$34,$C0,$D5,$CD,$9A,$3A,$D1,$3A,$34 ; ROM 03A7C
    db $C0,$BB,$C2,$EB,$57,$C9,$FE,$00,$02,$00,$00,$FE,$00,$02,$3A,$BA ; ROM 03A8C
    db $C0,$B7,$20,$22,$21,$F7,$3A,$CD,$A9,$3A,$21,$FF,$3A,$DD,$7E,$0A ; ROM 03A9C
    db $87,$CF,$4D,$44,$FD,$21,$EE,$3A,$3A,$E5,$C0,$3D,$CA,$91,$35,$FD ; ROM 03AAC
    db $21,$E2,$3A,$C3,$91,$35,$21,$F7,$3A,$CD,$CB,$3A,$21,$FF,$3A,$DD ; ROM 03ABC
    db $7E,$0A,$87,$CF,$4D,$44,$FD,$21,$D9,$3A,$C3,$91,$35,$0B,$00,$00 ; ROM 03ACC
    db $00,$31,$2B,$00,$00,$00,$38,$00,$29,$00,$85,$3F,$00,$00,$3D,$3A ; ROM 03ADC
    db $39,$3A,$13,$00,$29,$00,$86,$1F,$00,$00,$00,$F4,$FC,$FC,$FC,$F4 ; ROM 03AEC
    db $FC,$F4,$04,$F4,$04,$FC,$04,$FC,$FC,$FC,$04 ; ROM 03AFC
    LD A,($c042)                   ; ROM 03B07: 3a42c0
    OR A                           ; ROM 03B0A: b7
    RET z                          ; ROM 03B0B: c8
    LD ($ffff),A                   ; ROM 03B0C: 32ffff
    LD HL,($c043)                  ; ROM 03B0F: 2a43c0
    LD E,(HL)                      ; ROM 03B12: 5e
    INC HL                         ; ROM 03B13: 23
    LD A,0                         ; ROM 03B14: 3e00
    OUT ($00bf),A                  ; ROM 03B16: d3bf
    LD A,$7e                       ; ROM 03B18: 3e7e
    OUT ($00bf),A                  ; ROM 03B1A: d3bf
    XOR A                          ; ROM 03B1C: af
    LD ($c042),A                   ; ROM 03B1D: 3242c0
    LD C,$be                       ; ROM 03B20: 0ebe
    OUTI                           ; ROM 03B22: eda3
    OUTI                           ; ROM 03B24: eda3
    OUTI                           ; ROM 03B26: eda3
    OUT ($00be),A                  ; ROM 03B28: d3be
    OUTI                           ; ROM 03B2A: eda3
    OUTI                           ; ROM 03B2C: eda3
    OUTI                           ; ROM 03B2E: eda3
    OUT ($00be),A                  ; ROM 03B30: d3be
    OUTI                           ; ROM 03B32: eda3
    OUTI                           ; ROM 03B34: eda3
    OUTI                           ; ROM 03B36: eda3
    OUT ($00be),A                  ; ROM 03B38: d3be
    OUTI                           ; ROM 03B3A: eda3
    OUTI                           ; ROM 03B3C: eda3
    OUTI                           ; ROM 03B3E: eda3
    OUT ($00be),A                  ; ROM 03B40: d3be
    OUTI                           ; ROM 03B42: eda3
    OUTI                           ; ROM 03B44: eda3
    OUTI                           ; ROM 03B46: eda3
    OUT ($00be),A                  ; ROM 03B48: d3be
    OUTI                           ; ROM 03B4A: eda3
    OUTI                           ; ROM 03B4C: eda3
    OUTI                           ; ROM 03B4E: eda3
    OUT ($00be),A                  ; ROM 03B50: d3be
    OUTI                           ; ROM 03B52: eda3
    OUTI                           ; ROM 03B54: eda3
    OUTI                           ; ROM 03B56: eda3
    OUT ($00be),A                  ; ROM 03B58: d3be
    OUTI                           ; ROM 03B5A: eda3
    OUTI                           ; ROM 03B5C: eda3
    OUTI                           ; ROM 03B5E: eda3
    OUT ($00be),A                  ; ROM 03B60: d3be
    DEC E                          ; ROM 03B62: 1d
    JP nz,$3b22                    ; ROM 03B63: c2223b
    RET                            ; ROM 03B66: c9
    db $C3,$81,$01,$81,$C3,$81,$62,$81,$24,$82,$85,$82,$24,$82,$85,$82 ; ROM 03B67
    db $D8,$83,$16,$83,$D8,$83,$77,$83,$39,$84,$9A,$84,$39,$84,$9A,$84 ; ROM 03B77
    db $ED,$85,$2B,$85,$ED,$85,$8C,$85,$4E,$86,$AF,$86,$4E,$86,$AF,$86 ; ROM 03B87
    db $02,$88,$40,$87,$02,$88,$A1,$87,$63,$88,$C4,$88,$63,$88,$C4,$88 ; ROM 03B97
    db $C3,$81,$01,$81,$C3,$81,$62,$81,$24,$82,$85,$82,$24,$82,$85,$82 ; ROM 03BA7
    db $D8,$83,$16,$83,$D8,$83,$77,$83,$39,$84,$9A,$84,$39,$84,$9A,$84 ; ROM 03BB7
    db $ED,$85,$2B,$85,$ED,$85,$8C,$85,$4E,$86,$AF,$86,$4E,$86,$AF,$86 ; ROM 03BC7
    db $02,$88,$40,$87,$02,$88,$A1,$87,$63,$88,$C4,$88,$63,$88,$C4,$88 ; ROM 03BD7
    db $C3,$81,$01,$81,$C3,$81,$62,$81,$55,$89,$E6,$89,$8F,$8A,$20,$8B ; ROM 03BE7
    db $A3,$8C,$E1,$8B,$A3,$8C,$42,$8C,$04,$8D,$95,$8D,$3E,$8E,$CF,$8E ; ROM 03BF7
    db $ED,$85,$2B,$85,$ED,$85,$8C,$85,$90,$8F,$21,$90,$CA,$90,$5B,$91 ; ROM 03C07
    db $DE,$92,$1C,$92,$DE,$92,$7D,$92,$3F,$93,$D0,$93,$79,$94,$0A,$95 ; ROM 03C17
    db $C3,$81,$01,$81,$C3,$81,$62,$81,$CB,$95,$5C,$96,$05,$97,$96,$97 ; ROM 03C27
    db $19,$99,$57,$98,$19,$99,$B8,$98,$7A,$99,$0B,$9A,$B4,$9A,$45,$9B ; ROM 03C37
    db $ED,$85,$2B,$85,$ED,$85,$8C,$85,$06,$9C,$97,$9C,$40,$9D,$D1,$9D ; ROM 03C47
    db $54,$9F,$92,$9E,$54,$9F,$F3,$9E,$B5,$9F,$46,$A0,$EF,$A0,$80,$A1 ; ROM 03C57
    db $00,$80,$61,$80,$00,$80,$61,$80,$C2,$80,$23,$81,$C2,$80,$23,$81 ; ROM 03C67
    db $B4,$81,$15,$82,$B4,$81,$15,$82,$76,$82,$D7,$82,$76,$82,$D7,$82 ; ROM 03C77
    db $68,$83,$C9,$83,$68,$83,$C9,$83,$2A,$84,$8B,$84,$2A,$84,$8B,$84 ; ROM 03C87
    db $1C,$85,$7D,$85,$1C,$85,$7D,$85,$DE,$85,$3F,$86,$DE,$85,$3F,$86 ; ROM 03C97
    db $00,$80,$61,$80,$00,$80,$61,$80,$C2,$80,$23,$81,$C2,$80,$23,$81 ; ROM 03CA7
    db $B4,$81,$15,$82,$B4,$81,$15,$82,$76,$82,$D7,$82,$76,$82,$D7,$82 ; ROM 03CB7
    db $68,$83,$C9,$83,$68,$83,$C9,$83,$2A,$84,$8B,$84,$2A,$84,$8B,$84 ; ROM 03CC7
    db $1C,$85,$7D,$85,$1C,$85,$7D,$85,$DE,$85,$3F,$86,$DE,$85,$3F,$86 ; ROM 03CD7
    db $00,$80,$61,$80,$00,$80,$61,$80,$D0,$86,$61,$87,$0A,$88,$9B,$88 ; ROM 03CE7
    db $5C,$89,$BD,$89,$5C,$89,$BD,$89,$1E,$8A,$AF,$8A,$58,$8B,$E9,$8B ; ROM 03CF7
    db $68,$83,$C9,$83,$68,$83,$C9,$83,$AA,$8C,$3B,$8D,$E4,$8D,$75,$8E ; ROM 03D07
    db $36,$8F,$97,$8F,$36,$8F,$97,$8F,$F8,$8F,$89,$90,$32,$91,$C3,$91 ; ROM 03D17
    db $00,$80,$61,$80,$00,$80,$61,$80,$84,$92,$15,$93,$BE,$93,$4F,$94 ; ROM 03D27
    db $10,$95,$71,$95,$10,$95,$71,$95,$D2,$95,$63,$96,$0C,$97,$9D,$97 ; ROM 03D37
    db $68,$83,$C9,$83,$68,$83,$C9,$83,$5E,$98,$EF,$98,$98,$99,$29,$9A ; ROM 03D47
    db $EA,$9A,$4B,$9B,$EA,$9A,$4B,$9B,$AC,$9B,$3D,$9C,$E6,$9C,$77,$9D ; ROM 03D57
    db $38,$9E,$99,$9E,$FA,$9E,$5B,$9F,$BC,$9F,$1D,$A0,$7E,$A0,$DF,$A0 ; ROM 03D67
    db $40,$A1,$A1,$A1,$85,$82,$23,$81,$9A,$84,$D7,$82,$AF,$86,$8B,$84 ; ROM 03D77
    db $C4,$88,$3F,$86,$02,$A2,$95,$3D,$95,$3D,$95,$3D,$95,$3D,$99,$3D ; ROM 03D87
    db $9F,$3D,$81,$00,$01,$F7,$FC,$98,$81,$00,$01,$F7,$FC,$86 ; ROM 03D97
    LD A,(IX+1)                    ; ROM 03DA5: dd7e01
    OR A                           ; ROM 03DA8: b7
    JP nz,$3dfa                    ; ROM 03DA9: c2fa3d
    LD HL,$3e53                    ; ROM 03DAC: 21533e
    LD A,(HL)                      ; ROM 03DAF: 7e
    LD (IX+8),A                    ; ROM 03DB0: dd7708
    INC HL                         ; ROM 03DB3: 23
    LD A,(HL)                      ; ROM 03DB4: 7e
    LD (IX+9),A                    ; ROM 03DB5: dd7709
    INC HL                         ; ROM 03DB8: 23
    LD A,(HL)                      ; ROM 03DB9: 7e
    LD (IX+$19),A                  ; ROM 03DBA: dd7719
    INC HL                         ; ROM 03DBD: 23
    LD A,(HL)                      ; ROM 03DBE: 7e
    ADD A,(IX+$11)                 ; ROM 03DBF: dd8611
    LD (IX+$11),A                  ; ROM 03DC2: dd7711
    INC HL                         ; ROM 03DC5: 23
    LD A,(HL)                      ; ROM 03DC6: 7e
    LD (IX+12),A                   ; ROM 03DC7: dd770c
    INC HL                         ; ROM 03DCA: 23
    LD A,(HL)                      ; ROM 03DCB: 7e
    LD (IX+13),A                   ; ROM 03DCC: dd770d
    INC HL                         ; ROM 03DCF: 23
    LD A,(IX+10)                   ; ROM 03DD0: dd7e0a
    ADD A,A                        ; ROM 03DD3: 87
    ADD A,A                        ; ROM 03DD4: 87
    ADD A,L                        ; ROM 03DD5: 85
    LD L,A                         ; ROM 03DD6: 6f
    JR nc,$3dda                    ; ROM 03DD7: 3001
    db $24 ; ROM 03DD9
    LD A,(HL)                      ; ROM 03DDA: 7e
    LD (IX+$14),A                  ; ROM 03DDB: dd7714
    INC HL                         ; ROM 03DDE: 23
    LD A,(HL)                      ; ROM 03DDF: 7e
    LD (IX+$15),A                  ; ROM 03DE0: dd7715
    INC HL                         ; ROM 03DE3: 23
    LD A,(HL)                      ; ROM 03DE4: 7e
    LD (IX+$16),A                  ; ROM 03DE5: dd7716
    INC HL                         ; ROM 03DE8: 23
    LD A,(HL)                      ; ROM 03DE9: 7e
    LD (IX+$17),A                  ; ROM 03DEA: dd7717
    LD (IX+1),2                    ; ROM 03DED: dd360102
    LD (IX+4),$80                  ; ROM 03DF1: dd360480
    LD (IX+3),$13                  ; ROM 03DF5: dd360313
    RET                            ; ROM 03DF9: c9
    LD A,($c0ba)                   ; ROM 03DFA: 3abac0
    CP 1                           ; ROM 03DFD: fe01
    JR z,$3e2a                     ; ROM 03DFF: 2829
    LD B,0                         ; ROM 03E01: 0600
    LD A,(IX+$11)                  ; ROM 03E03: dd7e11
    CP 8                           ; ROM 03E06: fe08
    JR nc,$3e0b                    ; ROM 03E08: 3001
    db $04 ; ROM 03E0A
    CP $98                         ; ROM 03E0B: fe98
    JR c,$3e10                     ; ROM 03E0D: 3801
    db $04 ; ROM 03E0F
    LD A,(IX+$13)                  ; ROM 03E10: dd7e13
    CP 8                           ; ROM 03E13: fe08
    JR nc,$3e18                    ; ROM 03E15: 3001
    db $04 ; ROM 03E17
    CP $f8                         ; ROM 03E18: fef8
    JR c,$3e1d                     ; ROM 03E1A: 3801
    db $04 ; ROM 03E1C
    LD A,(IX+4)                    ; ROM 03E1D: dd7e04
    OR A                           ; ROM 03E20: b7
    JR nz,$3e24                    ; ROM 03E21: 2001
    db $04 ; ROM 03E23
    LD A,B                         ; ROM 03E24: 78
    OR A                           ; ROM 03E25: b7
    JP nz,$57eb                    ; ROM 03E26: c2eb57
    RET                            ; ROM 03E29: c9
    db $06,$00,$DD,$7E,$11,$FE,$20,$30,$01,$04,$FE,$88,$38,$01,$04,$DD ; ROM 03E2A
    db $7E,$13,$FE,$20,$30,$01,$04,$FE,$E0,$38,$01,$04,$DD,$7E,$04,$B7 ; ROM 03E3A
    db $20,$01,$04,$78,$B7,$C2,$EB,$57,$C9,$D4,$8E,$04,$F8,$00,$00,$80 ; ROM 03E4A
    db $FE,$00,$00,$80,$01,$00,$00,$00,$00,$80,$FE,$00,$00,$80,$01,$DD ; ROM 03E5A
    db $7E,$01,$B7,$C2,$FA,$3D,$21,$76,$3E,$C3,$AF,$3D,$FC,$8E,$0A,$F8 ; ROM 03E6A
    db $04,$05,$40,$FE,$00,$00,$C0,$01,$00,$00,$00,$00,$40,$FE,$00,$00 ; ROM 03E7A
    db $C0,$01,$DD,$7E,$01,$B7,$20,$06,$21,$B6,$3E,$C3,$AF,$3D,$CD,$FA ; ROM 03E8A
    db $3D,$DD,$7E,$0E,$3C,$FE,$02,$38,$01,$AF,$DD,$77,$0E,$C0,$DD,$7E ; ROM 03E9A
    db $0B,$3C,$FE,$04,$38,$02,$3E,$01,$DD,$77,$0B,$C9,$48,$8F,$0E,$F8 ; ROM 03EAA
    db $00,$00,$00,$FE,$00,$00,$00,$02,$00,$00,$00,$00,$00,$FE,$00,$00 ; ROM 03EBA
    db $00,$02,$DD,$7E,$01,$B7,$C2,$FA,$3D,$21,$57,$3F,$7E,$DD,$77,$08 ; ROM 03ECA
    db $23,$7E,$DD,$77,$09,$23,$7E,$DD,$77,$19,$23,$7E,$DD,$86,$11,$DD ; ROM 03EDA
    db $77,$11,$23,$7E,$DD,$77,$0C,$23,$7E,$DD,$77,$0D,$23,$CD,$07,$3F ; ROM 03EEA
    db $DD,$36,$01,$02,$DD,$36,$04,$60,$DD,$36,$03,$13,$C9,$0E,$02,$3A ; ROM 03EFA
    db $13,$C3,$DD,$96,$13,$30,$04,$ED,$44,$CB,$D1,$47,$3A,$11,$C3,$DD ; ROM 03F0A
    db $96,$11,$30,$04,$ED,$44,$CB,$89,$B8,$30,$01,$0C,$11,$4F,$3F,$79 ; ROM 03F1A
    db $83,$5F,$30,$01,$14,$1A,$DD,$77,$0A,$79,$87,$87,$85,$6F,$30,$01 ; ROM 03F2A
    db $24,$7E,$DD,$77,$16,$23,$7E,$DD,$77,$17,$23,$7E,$DD,$77,$14,$23 ; ROM 03F3A
    db $7E,$DD,$77,$15,$C9,$00,$03,$01,$03,$00,$02,$01,$02,$82,$8F,$08 ; ROM 03F4A
    db $FC,$00,$00,$7A,$00,$D9,$FE,$27,$01,$86,$FF,$7A,$00,$27,$01,$27 ; ROM 03F5A
    db $01,$7A,$00,$86,$FF,$D9,$FE,$D9,$FE,$86,$FF,$86,$FF,$27,$01,$D9 ; ROM 03F6A
    db $FE,$7A,$00,$DD,$7E,$01,$B7,$C2,$FA,$3D,$21,$8A,$3F,$C3,$D6,$3E ; ROM 03F7A
    db $92,$8F,$0C,$FC,$02,$03,$92,$00,$9E,$FE,$62,$01,$6E,$FF,$92,$00 ; ROM 03F8A
    db $62,$01,$62,$01,$92,$00,$6E,$FF,$9E,$FE,$9E,$FE,$6E,$FF,$6E,$FF ; ROM 03F9A
    db $62,$01,$9E,$FE,$92,$00,$DD,$7E,$01,$B7,$C2,$FA,$3D,$21,$BD,$3F ; ROM 03FAA
    db $C3,$D6,$3E,$AA,$8F,$0E,$FC,$02,$02,$AB,$00,$63,$FE,$9D,$01,$55 ; ROM 03FBA
    db $FF,$AB,$00,$9D,$01,$9D,$01,$AB,$00,$55,$FF,$63,$FE,$63,$FE,$55 ; ROM 03FCA
    db $FF,$55,$FF,$9D,$01,$63,$FE,$AB,$00,$DD,$7E,$01,$B7,$C2,$FA,$3D ; ROM 03FDA
    db $21,$F0,$3F,$C3,$AF,$3D,$82,$8F,$08,$F8,$00,$00,$80,$FE,$00,$00 ; ROM 03FEA
    db $80,$01,$00,$00,$00,$00 ; ROM 03FFA
