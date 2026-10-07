#!/bin/sh
set -eu
PREFIX=${PREFIX:-m68k-elf-}
OUT=md/build/video-fixture
mkdir -p "$OUT"
CFLAGS='-m68000 -O2 -flto -ffreestanding -fno-builtin -fno-common -fomit-frame-pointer -ffunction-sections -fdata-sections -Wall -Wextra -Werror -Isrc/include -Imd/include'
OBJ=''
# These are the production video backend and shadow. No game data or game logic.
for f in src/ram.c src/video.c src/video_status.c md/src/runtime.c md/src/platform_md.c md/src/video_convert.c tests/md_video_fixture.c; do
  o="$OUT/$(basename "$f" .c).o"
  "${PREFIX}gcc" $CFLAGS -c "$f" -o "$o"
  OBJ="$OBJ $o"
done
"${PREFIX}gcc" -m68000 -c md/src/startup.s -o "$OUT/startup.o"
"${PREFIX}gcc" -m68000 -c md/src/vectors.s -o "$OUT/vectors.o"
"${PREFIX}gcc" $CFLAGS -nostdlib -Wl,-T,md/link.ld -Wl,--gc-sections "$OUT/vectors.o" "$OUT/startup.o" $OBJ -lgcc -o "$OUT/fixture.elf"
"${PREFIX}objcopy" -O binary "$OUT/fixture.elf" "$OUT/fixture.bin"
python3 md/fix_header.py "$OUT/fixture.bin"
python3 tools/check_md_rom.py "$OUT/fixture.bin"
"${PREFIX}size" "$OUT/fixture.elf"
