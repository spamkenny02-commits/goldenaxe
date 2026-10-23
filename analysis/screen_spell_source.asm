; Golden Axe Warrior original SMS screen-spell routines.
; Mixed code/data ranges: coordinates/tables after 6BF6 and 6CF0 are raw tables, not instructions.
30A7  cd bb 30               CALL 0x30bb
30AA  d8                     RET c
30AB  3a e6 c0               LD A,(0xc0e6)
30AE  32 90 c0               LD (0xc090),A
30B1  dd 36 01 06            LD (IX+1),6
30B5  3e 94                  LD A,0x94
30B7  32 06 de               LD (0xde06),A
30BA  c9                     RET
30BB  21 d2 30               LD HL,0x30d2
30BE  3a df c0               LD A,(0xc0df)
30C1  e6 03                  AND 3
30C3  85                     ADD A,L
30C4  6f                     LD L,A
30C5  30 01                  JR nc,0x30c8
30C7  24                     INC H
30C8  6e                     LD L,(HL)
30C9  3a db c0               LD A,(0xc0db)
30CC  95                     SUB L
30CD  d8                     RET c
30CE  32 db c0               LD (0xc0db),A
30D1  c9                     RET
30D2  08                     EX AF,AF'
30D3  08                     EX AF,AF'
30D4  20 18                  JR nz,0x30ee
37B3  af                     XOR A
37B4  32 05 c3               LD (0xc305),A
37B7  32 1d c3               LD (0xc31d),A
37BA  dd 34 01               INC (IX+1)
37BD  3a 90 c0               LD A,(0xc090)
37C0  b7                     OR A
37C1  20 03                  JR nz,0x37c6
37C3  32 01 c3               LD (0xc301),A
37C6  dd 36 08 a0            LD (IX+8),0xa0
37CA  dd 36 09 80            LD (IX+9),0x80
37CE  21 41 a2               LD HL,0xa241
37D1  22 43 c0               LD (0xc043),HL
37D4  3e 04                  LD A,4
37D6  32 42 c0               LD (0xc042),A
37D9  c9                     RET
6AF1  c0                     RET nz
6AF2  90                     SUB B
6AF3  fb                     EI
6AF4  6a                     LD L,D
6AF5  2e 6c                  LD L,0x6c
6AF7  2c                     INC L
6AF8  6d                     LD L,L
6AF9  40                     LD B,B
6AFA  6d                     LD L,L
6AFB  cd df 20               CALL 0x20df
6AFE  cd ea 6d               CALL 0x6dea
6B01  3e 05                  LD A,5
6B03  21 3b a3               LD HL,0xa33b
6B06  11 00 40               LD DE,0x4000
6B09  cd 27 03               CALL 0x0327
6B0C  dd 21 00 d2            LD IX,0xd200
6B10  21 f6 6b               LD HL,0x6bf6
6B13  11 20 00               LD DE,0x20
6B16  01 ff 16               LD BC,0x16ff
6B19  dd 70 00               LD (IX),B
6B1C  dd 71 01               LD (IX+1),C
6B1F  0d                     DEC C
6B20  7e                     LD A,(HL)
6B21  23                     INC HL
6B22  dd 77 02               LD (IX+2),A
6B25  7e                     LD A,(HL)
6B26  23                     INC HL
6B27  dd 77 03               LD (IX+3),A
6B2A  dd 19                  ADD IX,DE
6B2C  10 eb                  DJNZ 0x6b19
6B2E  3e 05                  LD A,5
6B30  32 ff ff               LD (0xffff),A
6B33  dd 21 00 d2            LD IX,0xd200
6B37  06 16                  LD B,0x16
6B39  c5                     PUSH BC
6B3A  dd 7e 00               LD A,(IX)
6B3D  b7                     OR A
6B3E  28 4c                  JR z,0x6b8c
6B40  21 22 6c               LD HL,0x6c22
6B43  dd 7e 01               LD A,(IX+1)
6B46  fe 0e                  CP 14
6B48  30 0d                  JR nc,0x6b57
6B4A  87                     ADD A,A
6B4B  dd 86 01               ADD A,(IX+1)
6B4E  87                     ADD A,A
6B4F  87                     ADD A,A
6B50  5f                     LD E,A
6B51  16 00                  LD D,0
6B53  21 93 a2               LD HL,0xa293
6B56  19                     ADD HL,DE
6B57  dd 5e 02               LD E,(IX+2)
6B5A  dd 56 03               LD D,(IX+3)
6B5D  01 ff 04               LD BC,0x4ff
6B60  ed a0                  LDI
6B62  1c                     INC E
6B63  ed a0                  LDI
6B65  1c                     INC E
6B66  ed a0                  LDI
6B68  3e 3b                  LD A,0x3b
6B6A  83                     ADD A,E
6B6B  5f                     LD E,A
6B6C  30 01                  JR nc,0x6b6f
6B6E  14                     INC D
6B6F  10 ef                  DJNZ 0x6b60
6B71  dd 34 01               INC (IX+1)
6B74  dd 7e 01               LD A,(IX+1)
6B77  fe 16                  CP 0x16
6B79  20 11                  JR nz,0x6b8c
6B7B  dd 36 01 00            LD (IX+1),0
6B7F  dd 34 04               INC (IX+4)
6B82  dd 7e 04               LD A,(IX+4)
6B85  d6 03                  SUB 3
6B87  20 03                  JR nz,0x6b8c
6B89  dd 77 00               LD (IX),A
6B8C  c1                     POP BC
6B8D  11 20 00               LD DE,0x20
6B90  dd 19                  ADD IX,DE
6B92  10 a5                  DJNZ 0x6b39
6B94  3a 60 d3               LD A,(0xd360)
6B97  b7                     OR A
6B98  cc 7c 2d               CALL z,0x2d7c
6B9B  cd 3f 6e               CALL 0x6e3f
6B9E  cd c3 22               CALL 0x22c3
6BA1  3a a0 d4               LD A,(0xd4a0)
6BA4  b7                     OR A
6BA5  20 87                  JR nz,0x6b2e
6BA7  cd 8a 2d               CALL 0x2d8a
6BAA  4f                     LD C,A
6BAB  dd 21 00 c6            LD IX,0xc600
6BAF  11 30 00               LD DE,0x30
6BB2  06 10                  LD B,0x10
6BB4  dd 7e 00               LD A,(IX)
6BB7  b7                     OR A
6BB8  28 22                  JR z,0x6bdc
6BBA  dd 7e 1b               LD A,(IX+0x1b)
6BBD  b7                     OR A
6BBE  28 1c                  JR z,0x6bdc
6BC0  dd cb 03 4e            BIT 1,(IX+3)
6BC4  28 16                  JR z,0x6bdc
6BC6  79                     LD A,C
6BC7  dd 96 1a               SUB (IX+0x1a)
6BCA  30 02                  JR nc,0x6bce
6BCC  3e 01                  LD A,1
6BCE  dd 86 1d               ADD A,(IX+0x1d)
6BD1  dd 77 1d               LD (IX+0x1d),A
6BD4  dd 36 1e 00            LD (IX+0x1e),0
6BD8  dd 36 1f c3            LD (IX+0x1f),0xc3
6BDC  dd 19                  ADD IX,DE
6BDE  10 d4                  DJNZ 0x6bb4
6BE0  af                     XOR A
6BE1  32 90 c0               LD (0xc090),A
6BE4  cd 7c 2d               CALL 0x2d7c
6BE7  cd 38 09               CALL 0x0938
6BEA  cd df 20               CALL 0x20df
6BED  cd 26 72               CALL 0x7226
6BF0  cd ef 16               CALL 0x16ef
6BF3  c3 e2 1d               JP 0x1de2
6BF6  1a                     LD A,(DE)
6BF7  d6 54                  SUB 0x54
6BF9  d6 8e                  SUB 0x8e
6BFB  d6 c8                  SUB 0xc8
6BFD  d6 02                  SUB 2
6BFF  d7                     RST 0x10
6C00  00                     NOP
6C01  d8                     RET c
6C02  02                     LD (BC),A
6C03  d9                     EXX
6C04  48                     LD C,B
6C05  d9                     EXX
6C06  8e                     ADC A,(HL)
6C07  d9                     EXX
6C08  d4 d9 1a               CALL nc,0x1ad9
6C0B  da 20 da               JP c,0xda20
6C0E  e6 d9                  AND 0xd9
6C10  ac                     XOR H
6C11  d9                     EXX
6C12  72                     LD (HL),D
6C13  d9                     EXX
6C14  38 d9                  JR c,0x6bef
6C16  3a d8 38               LD A,(0x38d8)
6C19  d7                     RST 0x10
6C1A  f2 d6 ac               JP p,0xacd6
6C1D  d6 66                  SUB 0x66
6C1F  d6 20                  SUB 0x20
6C21  d6 ff                  SUB 0xff
6C23  ff                     RST 0x38
6C24  ff                     RST 0x38
6C25  ff                     RST 0x38
6C26  ff                     RST 0x38
6C27  ff                     RST 0x38
6C28  ff                     RST 0x38
6C29  ff                     RST 0x38
6C2A  ff                     RST 0x38
6C2B  ff                     RST 0x38
6C2C  ff                     RST 0x38
6C2D  ff                     RST 0x38
6C2E  cd ea 6d               CALL 0x6dea
6C31  cd e4 20               CALL 0x20e4
6C34  3e 05                  LD A,5
6C36  21 48 ad               LD HL,0xad48
6C39  11 00 40               LD DE,0x4000
6C3C  cd 27 03               CALL 0x0327
6C3F  21 b0 dc               LD HL,0xdcb0
6C42  11 a0 dc               LD DE,0xdca0
6C45  01 10 00               LD BC,0x10
6C48  ed b0                  LDIR
6C4A  3e 17                  LD A,0x17
6C4C  32 a2 dc               LD (0xdca2),A
6C4F  dd 21 00 d2            LD IX,0xd200
6C53  11 20 00               LD DE,0x20
6C56  af                     XOR A
6C57  06 04                  LD B,4
6C59  dd 70 00               LD (IX),B
6C5C  dd 77 01               LD (IX+1),A
6C5F  c6 10                  ADD A,0x10
6C61  dd 19                  ADD IX,DE
6C63  10 f4                  DJNZ 0x6c59
6C65  dd 21 00 d2            LD IX,0xd200
6C69  06 04                  LD B,4
6C6B  c5                     PUSH BC
6C6C  3e 05                  LD A,5
6C6E  32 ff ff               LD (0xffff),A
6C71  dd 7e 02               LD A,(IX+2)
6C74  87                     ADD A,A
6C75  dd 86 02               ADD A,(IX+2)
6C78  87                     ADD A,A
6C79  5f                     LD E,A
6C7A  16 00                  LD D,0
6C7C  fd 21 f0 6c            LD IY,0x6cf0
6C80  fd 19                  ADD IY,DE
6C82  dd 5e 01               LD E,(IX+1)
6C85  fd 6e 00               LD L,(IY)
6C88  fd 66 01               LD H,(IY+1)
6C8B  19                     ADD HL,DE
6C8C  eb                     EX DE,HL
6C8D  fd 6e 02               LD L,(IY+2)
6C90  fd 66 03               LD H,(IY+3)
6C93  0e ff                  LD C,0xff
6C95  fd 46 04               LD B,(IY+4)
6C98  d5                     PUSH DE
6C99  fd 7e 05               LD A,(IY+5)
6C9C  ed a0                  LDI
6C9E  ed a0                  LDI
6CA0  3d                     DEC A
6CA1  20 f9                  JR nz,0x6c9c
6CA3  d1                     POP DE
6CA4  3e 40                  LD A,0x40
6CA6  83                     ADD A,E
6CA7  5f                     LD E,A
6CA8  30 01                  JR nc,0x6cab
6CAA  14                     INC D
6CAB  10 eb                  DJNZ 0x6c98
6CAD  dd 34 08               INC (IX+8)
6CB0  dd 7e 08               LD A,(IX+8)
6CB3  3d                     DEC A
6CB4  20 14                  JR nz,0x6cca
6CB6  dd 77 08               LD (IX+8),A
6CB9  dd 34 02               INC (IX+2)
6CBC  dd 7e 02               LD A,(IX+2)
6CBF  fe 0a                  CP 10
6CC1  38 07                  JR c,0x6cca
6CC3  dd 36 02 07            LD (IX+2),7
6CC7  dd 34 09               INC (IX+9)
6CCA  c1                     POP BC
6CCB  11 20 00               LD DE,0x20
6CCE  dd 19                  ADD IX,DE
6CD0  10 99                  DJNZ 0x6c6b
6CD2  cd 3f 6e               CALL 0x6e3f
6CD5  3a 2f c0               LD A,(0xc02f)
6CD8  e6 03                  AND 3
6CDA  3e 03                  LD A,3
6CDC  28 01                  JR z,0x6cdf
6CDE  af                     XOR A
6CDF  32 a1 dc               LD (0xdca1),A
6CE2  cd c3 22               CALL 0x22c3
6CE5  3a 09 d2               LD A,(0xd209)
6CE8  fe 07                  CP 7
6CEA  c2 65 6c               JP nz,0x6c65
6CED  c3 a7 6b               JP 0x6ba7
6CF0  c4 da 08               CALL nz,0x08da
6CF3  a8                     XOR B
6CF4  01 04 84               LD BC,0x8404
6CF7  da 10 a8               JP c,0xa810
6CFA  02                     LD (BC),A
6CFB  04                     INC B
6CFC  82                     ADD A,D
6CFD  da 20 a8               JP c,0xa820
6D00  02                     LD (BC),A
6D01  06 82                  LD B,0x82
6D03  d9                     EXX
6D04  38 a8                  JR c,0x6cae
6D06  06 06                  LD B,6
6D08  82                     ADD A,D
6D09  d8                     RET c
6D0A  80                     ADD A,B
6D0B  a8                     XOR B
6D0C  0a                     LD A,(BC)
6D0D  06 82                  LD B,0x82
6D0F  d7                     RST 0x10
6D10  f8                     RET m
6D11  a8                     XOR B
6D12  0e 06                  LD C,6
6D14  82                     ADD A,D
6D15  d6 a0                  SUB 0xa0
6D17  a9                     XOR C
6D18  12                     LD (DE),A
6D19  06 02                  LD B,2
6D1B  d6 78                  SUB 0x78
6D1D  aa                     XOR D
6D1E  14                     INC D
6D1F  06 02                  LD B,2
6D21  d6 68                  SUB 0x68
6D23  ab                     XOR E
6D24  14                     INC D
6D25  06 02                  LD B,2
6D27  d6 58                  SUB 0x58
6D29  ac                     XOR H
6D2A  14                     INC D
6D2B  06 cd                  LD B,0xcd
6D2D  a6                     AND (HL)
6D2E  6d                     LD L,L
6D2F  3a 9a c0               LD A,(0xc09a)
6D32  d6 08                  SUB 8
6D34  32 9a c0               LD (0xc09a),A
6D37  dd 35 01               DEC (IX+1)
6D3A  c0                     RET nz
6D3B  dd 36 00 00            LD (IX),0
6D3F  c9                     RET
6D40  cd a6 6d               CALL 0x6da6
6D43  3a 9a c0               LD A,(0xc09a)
6D46  c6 08                  ADD A,8
6D48  32 9a c0               LD (0xc09a),A
6D4B  dd 35 01               DEC (IX+1)
6D4E  c0                     RET nz
6D4F  dd 36 00 00            LD (IX),0
6D53  c9                     RET
6D54  f5                     PUSH AF
6D55  c5                     PUSH BC
6D56  d5                     PUSH DE
6D57  e5                     PUSH HL
6D58  4e                     LD C,(HL)
6D59  11 00 d6               LD DE,0xd600
6D5C  7d                     LD A,L
6D5D  e6 0f                  AND 15
6D5F  87                     ADD A,A
6D60  87                     ADD A,A
6D61  83                     ADD A,E
6D62  5f                     LD E,A
6D63  7d                     LD A,L
6D64  e6 f0                  AND 0xf0
6D66  6f                     LD L,A
6D67  26 00                  LD H,0
6D69  29                     ADD HL,HL
6D6A  29                     ADD HL,HL
6D6B  29                     ADD HL,HL
6D6C  19                     ADD HL,DE
6D6D  eb                     EX DE,HL
6D6E  2a 34 c0               LD HL,(0xc034)
6D71  3e 02                  LD A,2
6D73  77                     LD (HL),A
6D74  2c                     INC L
6D75  77                     LD (HL),A
6D76  2c                     INC L
6D77  77                     LD (HL),A
6D78  2c                     INC L
6D79  73                     LD (HL),E
6D7A  2c                     INC L
6D7B  72                     LD (HL),D
6D7C  2c                     INC L
6D7D  22 34 c0               LD (0xc034),HL
6D80  69                     LD L,C
6D81  26 00                  LD H,0
6D83  29                     ADD HL,HL
6D84  29                     ADD HL,HL
6D85  29                     ADD HL,HL
6D86  01 00 c9               LD BC,0xc900
6D89  09                     ADD HL,BC
6D8A  ed a0                  LDI
6D8C  ed a0                  LDI
6D8E  ed a0                  LDI
6D90  ed a0                  LDI
6D92  3e 3c                  LD A,0x3c
6D94  83                     ADD A,E
6D95  5f                     LD E,A
6D96  30 01                  JR nc,0x6d99
6D98  14                     INC D
6D99  ed a0                  LDI
6D9B  ed a0                  LDI
6D9D  ed a0                  LDI
6D9F  ed a0                  LDI
6DA1  e1                     POP HL
6DA2  d1                     POP DE
6DA3  c1                     POP BC
6DA4  f1                     POP AF
6DA5  c9                     RET
6DA6  ed 4b 9a c0            LD BC,(0xc09a)
6DAA  11 00 78               LD DE,0x7800
6DAD  79                     LD A,C
6DAE  6f                     LD L,A
6DAF  63                     LD H,E
6DB0  29                     ADD HL,HL
6DB1  29                     ADD HL,HL
6DB2  29                     ADD HL,HL
6DB3  78                     LD A,B
6DB4  0f                     RRCA
6DB5  0f                     RRCA
6DB6  b5                     OR L
6DB7  6f                     LD L,A
6DB8  19                     ADD HL,DE
6DB9  eb                     EX DE,HL
6DBA  ef                     RST 0x28
6DBB  21 00 5e               LD HL,0x5e00
6DBE  19                     ADD HL,DE
6DBF  eb                     EX DE,HL
6DC0  79                     LD A,C
6DC1  e6 f0                  AND 0xf0
6DC3  6f                     LD L,A
6DC4  78                     LD A,B
6DC5  e6 f0                  AND 0xf0
6DC7  0f                     RRCA
6DC8  0f                     RRCA
6DC9  0f                     RRCA
6DCA  0f                     RRCA
6DCB  b5                     OR L
6DCC  6f                     LD L,A
6DCD  26 dc                  LD H,0xdc
6DCF  6e                     LD L,(HL)
6DD0  26 00                  LD H,0
6DD2  29                     ADD HL,HL
6DD3  29                     ADD HL,HL
6DD4  29                     ADD HL,HL
6DD5  79                     LD A,C
6DD6  e6 08                  AND 8
6DD8  0f                     RRCA
6DD9  b5                     OR L
6DDA  6f                     LD L,A
6DDB  01 00 c9               LD BC,0xc900
6DDE  09                     ADD HL,BC
6DDF  06 04                  LD B,4
6DE1  7e                     LD A,(HL)
6DE2  d3 be                  OUT (0x00be),A
6DE4  12                     LD (DE),A
6DE5  23                     INC HL
6DE6  13                     INC DE
6DE7  10 f8                  DJNZ 0x6de1
6DE9  c9                     RET
6DEA  21 00 d2               LD HL,0xd200
6DED  11 01 d2               LD DE,0xd201
6DF0  01 ff 03               LD BC,0x3ff
6DF3  36 00                  LD (HL),0
6DF5  ed b0                  LDIR
6DF7  cd 7c 2d               CALL 0x2d7c
6DFA  dd 21 30 c3            LD IX,0xc330
6DFE  11 30 00               LD DE,0x30
6E01  af                     XOR A
6E02  06 08                  LD B,8
6E04  dd 36 00 01            LD (IX),1
6E08  dd 36 08 ae            LD (IX+8),0xae
6E0C  dd 36 09 6e            LD (IX+9),0x6e
6E10  dd 36 0c 02            LD (IX+12),2
6E14  dd 36 0d 06            LD (IX+13),6
6E18  dd 77 10               LD (IX+0x10),A
6E1B  c6 20                  ADD A,0x20
6E1D  dd 19                  ADD IX,DE
6E1F  10 e3                  DJNZ 0x6e04
6E21  21 80 c7               LD HL,0xc780
6E24  11 81 c7               LD DE,0xc781
6E27  01 7f 01               LD BC,0x17f
6E2A  36 00                  LD (HL),0
6E2C  ed b0                  LDIR
6E2E  3e 0f                  LD A,15
6E30  32 ff ff               LD (0xffff),A
6E33  21 00 80               LD HL,0x8000
6E36  11 a0 dc               LD DE,0xdca0
6E39  01 10 00               LD BC,0x10
6E3C  ed b0                  LDIR
6E3E  c9                     RET
6E3F  dd 21 30 c3            LD IX,0xc330
6E43  06 08                  LD B,8
6E45  c5                     PUSH BC
6E46  cd 54 6e               CALL 0x6e54
6E49  c1                     POP BC
6E4A  11 30 00               LD DE,0x30
6E4D  dd 19                  ADD IX,DE
6E4F  10 f4                  DJNZ 0x6e45
6E51  c3 38 09               JP 0x0938
6E54  dd 7e 00               LD A,(IX)
6E57  b7                     OR A
6E58  c8                     RET z
6E59  21 2f c0               LD HL,0xc02f
6E5C  7e                     LD A,(HL)
6E5D  e6 07                  AND 7
6E5F  cb 5e                  BIT 3,(HL)
6E61  28 04                  JR z,0x6e67
6E63  ed 44                  NEG
6E65  c6 08                  ADD A,8
6E67  c6 10                  ADD A,0x10
6E69  4f                     LD C,A
6E6A  dd cb 03 86            RES 0,(IX+3)
6E6E  dd 7e 10               LD A,(IX+0x10)
6E71  cd 4e 04               CALL 0x044e
6E74  3a 13 c3               LD A,(0xc313)
6E77  84                     ADD A,H
6E78  dd 77 13               LD (IX+0x13),A
6E7B  cb 7c                  BIT 7,H
6E7D  28 01                  JR z,0x6e80
6E7F  3f                     CCF
6E80  38 19                  JR c,0x6e9b
6E82  c6 04                  ADD A,4
6E84  fe 08                  CP 8
6E86  38 13                  JR c,0x6e9b
6E88  dd 7e 10               LD A,(IX+0x10)
6E8B  cd 50 04               CALL 0x0450
6E8E  3a 11 c3               LD A,(0xc311)
6E91  84                     ADD A,H
6E92  d6 06                  SUB 6
6E94  dd 77 11               LD (IX+0x11),A
6E97  dd cb 03 c6            SET 0,(IX+3)
6E9B  dd 7e 10               LD A,(IX+0x10)
6E9E  c6 09                  ADD A,9
6EA0  dd 77 10               LD (IX+0x10),A
6EA3  3a 2f c0               LD A,(0xc02f)
6EA6  e6 01                  AND 1
6EA8  c6 f4                  ADD A,0xf4
6EAA  dd 77 02               LD (IX+2),A
6EAD  c9                     RET
6EAE  b6                     OR (HL)
6EAF  6e                     LD L,(HL)
6EB0  b6                     OR (HL)
6EB1  6e                     LD L,(HL)
6EB2  b6                     OR (HL)
6EB3  6e                     LD L,(HL)
6EB4  b6                     OR (HL)
6EB5  6e                     LD L,(HL)
6EB6  b8                     CP B
6EB7  6e                     LD L,(HL)
6EB8  01 00 00               LD BC,0
6EBB  f8                     RET m
6EBC  fc 00 af               CALL m,0xaf00
6EBF  32 05 c3               LD (0xc305),A
6EC2  cd f3 24               CALL 0x24f3
6EC5  21 30 c3               LD HL,0xc330
6EC8  11 30 00               LD DE,0x30
6ECB  01 00 1f               LD BC,0x1f00
6ECE  7e                     LD A,(HL)
6ECF  b1                     OR C
6ED0  4f                     LD C,A
6ED1  19                     ADD HL,DE
6ED2  10 fa                  DJNZ 0x6ece
6ED4  79                     LD A,C
6ED5  b7                     OR A
6ED6  20 ea                  JR nz,0x6ec2
6ED8  af                     XOR A
6ED9  32 ae c0               LD (0xc0ae),A
6EDC  06 d8                  LD B,0xd8
6EDE  cd c8 70               CALL 0x70c8
6EE1  af                     XOR A
6EE2  32 01 c3               LD (0xc301),A
6EE5  cd d4 70               CALL 0x70d4
6EE8  3a 11 c3               LD A,(0xc311)
6EEB  fe 50                  CP 0x50
6EED  28 0e                  JR z,0x6efd
6EEF  3e 01                  LD A,1
