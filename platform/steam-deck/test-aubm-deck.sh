#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/aubm-deck-test.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

SOURCE_ROOT="$TEST_ROOT/source"
GAME_ROOT="$TEST_ROOT/steamapps/common/Darkest Hour A HOI Game"
RUNTIME_ROOT="$TEST_ROOT/runtime"
MOD_ROOT="$GAME_ROOT/Mods/A Union Before Midnight V4.2"
TEST_LOG="$TEST_ROOT/game-arguments.log"
ACCOUNT_ID=123456789
CONTROLLER_CONFIG_ROOT="$TEST_ROOT/steam/steamapps/common/Steam Controller Configs/$ACCOUNT_ID/config"
export AUBM_STEAM_ROOT="$TEST_ROOT/steam"

fail() {
    printf 'FAIL: %s\n' "$1" >&2
    exit 1
}

assert_file_contains() {
    grep -Fq -- "$2" "$1" || fail "$1 does not contain: $2"
}

mkdir -p "$SOURCE_ROOT/mod/db" "$SOURCE_ROOT/mod/gfx" "$SOURCE_ROOT/installer"
mkdir -p "$GAME_ROOT/Mods/Darkest Hour Full/db"
mkdir -p "$CONTROLLER_CONFIG_ROOT"

printf '4.2.0-deck-test\n' > "$SOURCE_ROOT/VERSION"
printf 'overlay-one\n' > "$SOURCE_ROOT/mod/db/foundation.txt"
printf 'new-file-one\n' > "$SOURCE_ROOT/mod/gfx/deck-test.txt"
printf 'foundation-original\n' > "$GAME_ROOT/Mods/Darkest Hour Full/db/foundation.txt"

printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$@" > "$AUBM_TEST_LOG"\n' > "$GAME_ROOT/Darkest Hour.exe"
chmod +x "$GAME_ROOT/Darkest Hour.exe"
printf 'launcher-placeholder\n' > "$GAME_ROOT/Darkest Hour Launcher.exe"
cat > "$CONTROLLER_CONFIG_ROOT/configset_controller_neptune.vdf" <<'EOF'
"controller_config"
{
}
EOF

cat > "$GAME_ROOT/settings.cfg" <<'EOF'
0 # LANGUAGE
1 # MUSIC
https://example.invalid # Update URL
0 # Display resolution: 0 = do not change, 6 = user specified
1024 # Screen Width (used if 6 is selected)
768 # Screen Height (used if 6 is selected)
1 # Display mode: 0 = full screen, 1 = windowed
1 # Start-up movie: 0 = skip, 1 = play
0 # Extra debug logs (savedebug.txt): 0 = disabled, 1 = enabled
1 # Load game sounds: 0 = no sounds, 1 = load sounds
1 # Load unit sprites: 0 = no sprites, 1 = load unit sprites
1 # Load country specific unit and brigade pictures/models: 0 = generic, 1 = all
0 # Refresh map on resolutions higher then 1024x768
Mods # MODDIR folder. Default is Mods
Darkest Hour Full # Selected mod (must be a folder into MODDIR)
registry-placeholder
EOF

write_manifests() {
    (
        cd "$SOURCE_ROOT/mod"
        find . -type f -printf '%P\n' | sort > "$SOURCE_ROOT/installer/manifest.txt"
        while IFS= read -r file; do
            sha256sum "$file"
        done < "$SOURCE_ROOT/installer/manifest.txt" > "$SOURCE_ROOT/installer/manifest-sha256.txt"
    )
}

write_manifests
"$SCRIPT_DIR/install-aubm-deck.sh" \
    --source-root "$SOURCE_ROOT" \
    --game-root "$GAME_ROOT" \
    --runtime-root "$RUNTIME_ROOT"

assert_file_contains "$MOD_ROOT/db/foundation.txt" 'overlay-one'
assert_file_contains "$MOD_ROOT/gfx/deck-test.txt" 'new-file-one'
assert_file_contains "$GAME_ROOT/settings.cfg" '1280 # Screen Width'
assert_file_contains "$GAME_ROOT/settings.cfg" '800 # Screen Height'
assert_file_contains "$GAME_ROOT/settings.cfg" 'A Union Before Midnight V4.2 # Selected mod'
[[ -f "$MOD_ROOT/A_UNION_BEFORE_MIDNIGHT_INSTALL.json" ]] || fail 'install marker was not written'
[[ -f "$RUNTIME_ROOT/controller/aubm-steam-deck.vdf" ]] || fail 'controller profile was not installed'

AUBM_STEAM_ROOT="$TEST_ROOT/steam" \
    "$RUNTIME_ROOT/bin/install-aubm-controller" \
    --profile "$RUNTIME_ROOT/controller/aubm-steam-deck.vdf"
[[ -f "$CONTROLLER_CONFIG_ROOT/73170/controller_neptune.vdf" ]] || \
    fail 'per-game controller profile was not installed'
assert_file_contains "$CONTROLLER_CONFIG_ROOT/configset_controller_neptune.vdf" '"73170"'
assert_file_contains "$CONTROLLER_CONFIG_ROOT/configset_controller_neptune.vdf" '"autosave"'

# The second install proves stale managed files are restored from the DH Full base.
rm -f "$SOURCE_ROOT/mod/db/foundation.txt"
printf 'new-file-two\n' > "$SOURCE_ROOT/mod/gfx/deck-test.txt"
write_manifests
"$SCRIPT_DIR/install-aubm-deck.sh" \
    --source-root "$SOURCE_ROOT" \
    --game-root "$GAME_ROOT" \
    --runtime-root "$RUNTIME_ROOT"

assert_file_contains "$MOD_ROOT/db/foundation.txt" 'foundation-original'
assert_file_contains "$MOD_ROOT/gfx/deck-test.txt" 'new-file-two'

mkdir -p "$MOD_ROOT/scenarios/save games"
printf 'save-data\n' > "$MOD_ROOT/scenarios/save games/autosave.eug"
printf 'save-config\n' > "$MOD_ROOT/scenarios/save games/autosave.eug.cfg"

AUBM_RUNTIME_ROOT="$RUNTIME_ROOT" AUBM_TEST_LOG="$TEST_LOG" \
    "$RUNTIME_ROOT/bin/launch-aubm-deck" -- \
    "$GAME_ROOT/Darkest Hour Launcher.exe" --deck-test

assert_file_contains "$TEST_LOG" '--deck-test'
[[ "$(find "$RUNTIME_ROOT/save-backups/snapshots" -type f -name '*.tar.gz' | wc -l)" -eq 1 ]] || \
    fail 'save snapshot was not created'
[[ -f "$RUNTIME_ROOT/save-backups/current/autosave.eug" ]] || fail 'save mirror was not created'

printf 'changed-save\n' > "$MOD_ROOT/scenarios/save games/autosave.eug"
AUBM_RUNTIME_ROOT="$RUNTIME_ROOT" "$RUNTIME_ROOT/bin/manage-aubm-saves" restore-latest
assert_file_contains "$MOD_ROOT/scenarios/save games/autosave.eug" 'save-data'

# Hash failure must stop an update before the installed payload is touched.
printf 'tampered-payload\n' > "$SOURCE_ROOT/mod/gfx/deck-test.txt"
if "$SCRIPT_DIR/install-aubm-deck.sh" \
    --source-root "$SOURCE_ROOT" \
    --game-root "$GAME_ROOT" \
    --runtime-root "$RUNTIME_ROOT" >/dev/null 2>&1; then
    fail 'installer accepted a payload that did not match its SHA-256 manifest'
fi
assert_file_contains "$MOD_ROOT/gfx/deck-test.txt" 'new-file-two'

printf 'PASS: install, controller, managed update, settings, launcher, save restore, and hash rejection\n'
