CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2
CPPFLAGS += -Isrc/include
SRC = src/ram.c src/rom.c src/video.c src/video_status.c src/presentation.c src/audio.c src/irq.c src/assets.c src/scene.c src/effects.c src/reset.c src/ui.c src/inventory.c src/menu.c src/services.c src/ending.c src/intro.c src/tables.c src/entity.c src/entity_native.c src/player.c src/overworld_map.c src/world_progress.c src/world.c src/core.c src/sms_compat.c src/recompiled.c src/platform_host.c
NATIVE_SRC = $(filter-out src/sms_compat.c src/recompiled.c,$(SRC))
INPUTS = $(wildcard src/include/*.h src/*.inc)
.PHONY: all test test-final test-reset test-ui test-effects test-assets test-video test-video-status test-video-status-sanitize test-md-video test-pause test-scene test-full-effects test-transitions test-entry test-map-resources test-game-over test-presentation test-inventory test-menu test-services test-ending test-intro test-audio test-irq test-player-items test-world-scroll test-native-boot test-sanitize audit clean prepare-rom
all: phase17_host_test
prepare-rom:
	@test -n "$(ROM)" || { echo 'Use make prepare-rom ROM=/path/to/game.sms' >&2; exit 2; }
	python3 tools/embed_rom.py "$(ROM)"
src/original_rom.inc:
	@echo 'Missing original ROM data. Run make prepare-rom ROM=/path/to/game.sms' >&2
	@exit 2
%_host_test: tests/test_%.c $(SRC) $(INPUTS) src/original_rom.inc
	$(CC) $(CFLAGS) $(CPPFLAGS) $(SRC) $< -o $@
test: phase17_host_test
	./phase17_host_test
test-final: final_host_test
	./final_host_test
test-reset: reset_host_test
	./reset_host_test
test-ui: ui_host_test
	./ui_host_test
test-scene: scene_host_test
	./scene_host_test
test-full-effects: full_effects_host_test
	./full_effects_host_test
test-transitions: transitions_host_test
	./transitions_host_test
test-entry: entry_host_test
	./entry_host_test
test-map-resources: map_resources_host_test
	./map_resources_host_test
test-game-over: game_over_host_test
	./game_over_host_test
test-presentation: presentation_host_test
	./presentation_host_test
test-inventory: inventory_host_test
	./inventory_host_test
test-menu: menu_host_test
	./menu_host_test
test-services: services_host_test
	./services_host_test
test-ending: ending_host_test
	./ending_host_test
test-audio: audio_host_test
	./audio_host_test
test-irq: irq_host_test
	./irq_host_test
test-intro: intro_host_test
	./intro_host_test
test-player-items: player_items_host_test
	./player_items_host_test
test-world-scroll: world_scroll_host_test
	./world_scroll_host_test
native_boot_host_test: tests/test_native_boot.c $(NATIVE_SRC) $(INPUTS) src/original_rom.inc
	$(CC) $(CFLAGS) $(CPPFLAGS) $(NATIVE_SRC) $< -o $@
test-native-boot: native_boot_host_test
	./native_boot_host_test
test-pause: pause_host_test
	./pause_host_test
test-effects: effects_host_test
	./effects_host_test
test-assets: assets_host_test
	./assets_host_test
video_host_test: tests/test_video.c src/video.c src/video_status.c src/rom.c $(INPUTS) src/original_rom.inc
	$(CC) $(CFLAGS) $(CPPFLAGS) src/video.c src/video_status.c src/rom.c $< -o $@
test-video: video_host_test
	./video_host_test
md_video_host_test: tests/test_md_video.c md/src/video_convert.c md/src/pattern_plane.inc md/include/gaw_md_video.h
	$(CC) $(CFLAGS) -Imd/include md/src/video_convert.c $< -o $@
test-md-video: md_video_host_test
	./md_video_host_test
video_status_host_test: tests/test_video_status.c src/video.c src/video_status.c src/include/gaw_video.h
	$(CC) $(CFLAGS) $(CPPFLAGS) src/video.c src/video_status.c $< -o $@
test-video-status: video_status_host_test
	./video_status_host_test
test-video-status-sanitize:
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) src/video.c src/video_status.c tests/test_video_status.c -o video_status_san
	./video_status_san
test-sanitize:
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_final.c -o final_san
	./final_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_reset.c -o reset_san
	./reset_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_ui.c -o ui_san
	./ui_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_effects.c -o effects_san
	./effects_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_assets.c -o assets_san
	./assets_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_pause.c -o pause_san
	./pause_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_scene.c -o scene_san
	./scene_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_full_effects.c -o full_effects_san
	./full_effects_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_transitions.c -o transitions_san
	./transitions_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_entry.c -o entry_san
	./entry_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_map_resources.c -o map_resources_san
	./map_resources_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_game_over.c -o game_over_san
	./game_over_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_presentation.c -o presentation_san
	./presentation_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_inventory.c -o inventory_san
	./inventory_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_menu.c -o menu_san
	./menu_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_services.c -o services_san
	./services_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_ending.c -o ending_san
	./ending_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_intro.c -o intro_san
	./intro_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_audio.c -o audio_san
	./audio_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_irq.c -o irq_san
	./irq_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_player_items.c -o player_items_san
	./player_items_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_world_scroll.c -o world_scroll_san
	./world_scroll_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(NATIVE_SRC) tests/test_native_boot.c -o native_boot_san
	./native_boot_san
runtime_coverage_host_test: tests/runtime_coverage.c $(SRC) $(INPUTS) src/original_rom.inc
	$(CC) $(CFLAGS) $(CPPFLAGS) $(SRC) $< -o $@
audit: runtime_coverage_host_test
	python3 tools/audit_runtime_coverage.py
	python3 tools/audit_portability.py
	python3 tools/check_md_backend.py
clean:
	rm -f *_host_test *_san
