# Go 29 — runtime validation gate

## Improvement
- Changed the runtime launcher from five checks to **all seven** checked-in Godot runtime tests (including Duel and Galactic Fronts).
- Saves separate engine logs in `test_logs/` for troubleshooting.
- Fails if Godot returns nonzero or prints critical script/runtime errors, rather than treating a clean process exit as sufficient.
- Adds `tools/run_all_checks.sh` to run structural and engine tests together.

## Verified here
- All existing Python source-check scripts run successfully (see build output).
- Shell syntax checked with `bash -n`.
- Archive integrity verified.

## Not yet verified
- Godot executable not available in this environment; **runtime checks have not been executed**.
- Visual character realism and gameplay performance are not verified.
- Realism implementation estimate retained at 42%; this is testing infrastructure rather than new artwork.

On Linux with Godot 3.5/3.6: `bash tools/run_all_checks.sh`. If needed set `GODOT_BIN=/path/to/godot3`.
