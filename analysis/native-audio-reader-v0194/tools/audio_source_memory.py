"""Source bank6/fixed ROM and captured400-byte audio RAM, including SMS mirrors."""
def read_audio_byte(rom,state,address):
    address&=65535
    if address<0x8000:return rom[address]
    if address<0xc000:return rom[0x18000+(address&0x3fff)]
    offset=address&0x1fff
    if 0x1e00<=offset<0x1f90:return state[offset-0x1e00]
    raise NotImplementedError(f'Uncaptured source audio RAM {address:04X}')
