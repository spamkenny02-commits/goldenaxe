CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2
CPPFLAGS += -Isrc/include
SRC = src/ram.c src/reset.c src/ui.c src/tables.c src/entity.c src/entity_native.c src/player.c src/world_progress.c src/world.c src/core.c src/sms_compat.c src/recompiled.c src/platform_host.c
INPUTS = $(wildcard src/include/*.h src/*.inc)
.PHONY: all test test-final test-reset test-ui test-sanitize audit clean prepare-rom
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
test-sanitize:
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_final.c -o final_san
	./final_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_reset.c -o reset_san
	./reset_san
	$(CC) -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer $(CPPFLAGS) $(SRC) tests/test_ui.c -o ui_san
	./ui_san
runtime_coverage_host_test: tests/runtime_coverage.c $(SRC) $(INPUTS) src/original_rom.inc
	$(CC) $(CFLAGS) $(CPPFLAGS) $(SRC) $< -o $@
audit: runtime_coverage_host_test
	python3 tools/audit_runtime_coverage.py
	python3 tools/audit_portability.py
	python3 tools/check_md_backend.py
clean:
	rm -f *_host_test *_san
