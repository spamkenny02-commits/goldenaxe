CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2
CPPFLAGS += -Isrc/include
SRC = src/ram.c src/video.c src/assets.c src/scene.c src/effects.c src/reset.c src/ui.c src/tables.c src/entity.c src/entity_native.c src/player.c src/world_progress.c src/world.c src/core.c src/sms_compat.c src/recompiled.c src/platform_host.c
INPUTS = $(wildcard src/include/*.h src/*.inc)
.PHONY: all test test-final test-reset test-ui test-effects test-assets test-video test-pause test-scene test-full-effects test-transitions test-entry test-map-resources test-sanitize audit clean prepare-rom
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
test-pause: pause_host_test
	./pause_host_test
test-effects: effects_host_test
	./effects_host_test
test-assets: assets_host_test
	./assets_host_test
video_host_test: tests/test_video.c src/video.c $(INPUTS) src/original_rom.inc
	$(CC) $(CFLAGS) $(CPPFLAGS) src/video.c $< -o $@
test-video: video_host_test
	./video_host_test
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
runtime_coverage_host_test: tests/runtime_coverage.c $(SRC) $(INPUTS) src/original_rom.inc
	$(CC) $(CFLAGS) $(CPPFLAGS) $(SRC) $< -o $@
audit: runtime_coverage_host_test
	python3 tools/audit_runtime_coverage.py
	python3 tools/audit_portability.py
	python3 tools/check_md_backend.py
clean:
	rm -f *_host_test *_san
