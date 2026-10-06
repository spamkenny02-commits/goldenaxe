CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2
CPPFLAGS += -Isrc/include
SRC = src/ram.c src/tables.c src/entity.c src/entity_native.c src/player.c src/world_progress.c src/world.c src/core.c src/sms_compat.c src/recompiled.c src/platform_host.c
.PHONY: all test test-final clean
all: phase17_host_test
phase17_host_test: $(SRC) tests/test_phase17.c
	$(CC) $(CFLAGS) $(CPPFLAGS) $^ -o $@
test: phase17_host_test
	./phase17_host_test

final_host_test: $(SRC) tests/test_final.c
	$(CC) $(CFLAGS) $(CPPFLAGS) $^ -o $@
test-final: final_host_test
	./final_host_test
clean:
	rm -f phase17_host_test phase17_san final_host_test final_san
