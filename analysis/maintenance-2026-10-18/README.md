# Workspace cleanup and vertical-scroll diagnosis

At the user's request, 71377 untracked emulator full-state dumps were removed
from validation: 73967128576 bytes (73.97 GB / 68.89 GiB). No tracked file,
numbered ROM, Git object, source file or analysis archive was deleted. Extracted
RAM, VRAM, CRAM, VDP registers, screenshots and reports remain available.
The plan, deletion report and post-cleanup inventory are saved here.

`tools/clean_validation_states.py` defaults to a dry run; `--apply` deletes only
untracked `state_[0-9]+.bin` files below validation, excluding symlinks and
checking resolved paths stay within that directory.

`tools/run_core.py` now retains complete emulator states only with the explicit
`--save-states` option (`save_states=True` for Python callers). No existing
project tool reads these dumps. Extracted captures remain enabled. The SMS and
MD checks compare ten extracted files each between storage modes, in isolated
processes, and verify both presence and absence of optional full-state files.
Reproduce using `python tools/validate_capture_storage.py`.

Vertical-scroll research also measured the natural initial south and north
routes against new original SMS captures. NTSC drops a publication partway
through scrolling; the issue is broader than the terminal pose hold observed
in v0203. A two-copy assembly experiment did not eliminate it. The v0204 ROM
and sampled visual evidence are preserved as diagnostics in the numbered
archive and `../vertical-cadence-diagnostic-v0204`. The production source and
root ROM were restored exactly to v0203. Further source/foreground/audio/VDP
scheduling measurement is needed; no new cadence correction is claimed.
