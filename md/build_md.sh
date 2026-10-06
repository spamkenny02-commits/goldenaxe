#!/bin/sh
set -eu
test -f src/original_rom.inc || { echo 'Missing original ROM data: run make prepare-rom ROM=/path/to/game.sms first' >&2; exit 2; }
if [ "${FETCH_TOOLCHAIN:-0}" = 1 ] && ! command -v "${PREFIX:-m68k-elf-}gcc" >/dev/null 2>&1; then
  ./md/fetch_toolchain.sh "$PWD/md/toolchain"
  PATH="$PWD/md/toolchain/bin:$PATH"; export PATH
fi
PREFIX=${PREFIX:-m68k-elf-}
CC=${PREFIX}gcc
OBJCOPY=${PREFIX}objcopy
SIZE=${PREFIX}size
command -v "$CC" >/dev/null 2>&1 || { echo "missing $CC (run md/fetch_toolchain.sh or set FETCH_TOOLCHAIN=1)" >&2; exit 2; }
CFLAGS="-m68000 ${MD_OPT_FLAGS:--O2 -flto} -ffreestanding -fno-builtin -fno-common -fomit-frame-pointer -ffunction-sections -fdata-sections -Wall -Wextra -Werror -Isrc/include -Imd/include"
mkdir -p md/build
SRC='src/ram.c src/video.c src/presentation.c src/audio.c src/irq.c src/assets.c src/scene.c src/effects.c src/reset.c src/ui.c src/inventory.c src/menu.c src/services.c src/ending.c src/intro.c src/tables.c src/entity.c src/entity_native.c src/player.c src/world_progress.c src/world.c src/core.c md/src/runtime.c md/src/platform_md.c md/src/video_convert.c md/src/main.c'
OBJ=''
for f in $SRC; do o=md/build/$(basename "$f" .c).o; "$CC" $CFLAGS -c "$f" -o "$o"; OBJ="$OBJ $o"; done
"$CC" -m68000 -c md/src/startup.s -o md/build/startup.o
"$CC" -m68000 -c md/src/vectors.s -o md/build/vectors.o
"$CC" $CFLAGS -nostdlib -Wl,-T,md/link.ld -Wl,--gc-sections -Wl,--undefined=gaw_audio_tick,--undefined=gaw_irq_service -Wl,-Map,md/build/gaw_md.map md/build/vectors.o md/build/startup.o $OBJ -lgcc -o md/build/gaw_md.elf
python3 tools/check_md_elf.py md/build/gaw_md.elf --nm "${PREFIX}nm"
"$OBJCOPY" -O binary md/build/gaw_md.elf md/build/gaw_md.bin
python3 md/fix_header.py md/build/gaw_md.bin
"$SIZE" md/build/gaw_md.elf
python3 tools/check_md_rom.py md/build/gaw_md.bin
