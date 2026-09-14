#!/usr/bin/env bash
set -Eeuo pipefail

APP_ID=73170
MOD_NAME="A Union Before Midnight V4.2"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SOURCE_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
GAME_ROOT=""
RUNTIME_ROOT="${AUBM_RUNTIME_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/aubm-deck}"
FORCE=0

usage() {
    cat <<'EOF'
Usage: install-aubm-deck.sh [options]

Options:
  --game-root PATH     Darkest Hour installation directory
  --source-root PATH   Extracted A Union Before Midnight package/repository
  --runtime-root PATH  Deck helper data directory
  --force              Adopt an existing unmarked target mod directory
  --help               Show this help
EOF
}

while (($#)); do
    case "$1" in
        --game-root)
            GAME_ROOT="${2:?--game-root requires a path}"
            shift 2
            ;;
        --source-root)
            SOURCE_ROOT="${2:?--source-root requires a path}"
            shift 2
            ;;
        --runtime-root)
            RUNTIME_ROOT="${2:?--runtime-root requires a path}"
            shift 2
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

for tool in awk cmp cp cut date find grep install mktemp mv pgrep sed sha256sum sort tar tr uniq; do
    command -v "$tool" >/dev/null || {
        printf 'Required tool is missing: %s\n' "$tool" >&2
        exit 1
    }
done

discover_game_root() {
    local -a search_roots=()
    local root manifest candidate library
    search_roots+=("$HOME/.local/share/Steam" "$HOME/.steam/steam")
    [[ -d "/run/media/${USER:-deck}" ]] && search_roots+=("/run/media/${USER:-deck}")

    for root in "${search_roots[@]}"; do
        [[ -d "$root" ]] || continue
        while IFS= read -r manifest; do
            candidate="${manifest%/steamapps/appmanifest_${APP_ID}.acf}/steamapps/common/Darkest Hour A HOI Game"
            [[ -f "$candidate/Darkest Hour.exe" ]] && {
                printf '%s\n' "$candidate"
                return 0
            }
            candidate="${manifest%/appmanifest_${APP_ID}.acf}/common/Darkest Hour A HOI Game"
            [[ -f "$candidate/Darkest Hour.exe" ]] && {
                printf '%s\n' "$candidate"
                return 0
            }
        done < <(find "$root" -maxdepth 5 -type f -name "appmanifest_${APP_ID}.acf" 2>/dev/null)

        if [[ -f "$root/steamapps/libraryfolders.vdf" ]]; then
            while IFS= read -r library; do
                library="${library//\\\\/\\}"
                candidate="$library/steamapps/common/Darkest Hour A HOI Game"
                [[ -f "$candidate/Darkest Hour.exe" ]] && {
                    printf '%s\n' "$candidate"
                    return 0
                }
            done < <(awk -F'"' '/"path"/{print $4}' "$root/steamapps/libraryfolders.vdf")
        fi
    done
    return 1
}

if [[ -z "$GAME_ROOT" ]]; then
    GAME_ROOT="$(discover_game_root || true)"
fi

SOURCE_ROOT="$(cd -- "$SOURCE_ROOT" && pwd -P)"
if [[ -n "$GAME_ROOT" ]]; then
    GAME_ROOT="$(cd -- "$GAME_ROOT" && pwd -P)"
fi

OVERLAY_ROOT="$SOURCE_ROOT/mod"
MANIFEST="$SOURCE_ROOT/installer/manifest.txt"
HASH_MANIFEST="$SOURCE_ROOT/installer/manifest-sha256.txt"
VERSION_FILE="$SOURCE_ROOT/VERSION"

for required in "$OVERLAY_ROOT" "$MANIFEST" "$HASH_MANIFEST" "$VERSION_FILE"; do
    [[ -e "$required" ]] || {
        printf 'Required package path not found: %s\n' "$required" >&2
        exit 1
    }
done

if [[ -z "$GAME_ROOT" || ! -f "$GAME_ROOT/Darkest Hour.exe" ]]; then
    printf 'Darkest Hour was not found. Pass --game-root with its Steam installation directory.\n' >&2
    exit 1
fi

BASE_MOD="$GAME_ROOT/Mods/Darkest Hour Full"
TARGET_MOD="$GAME_ROOT/Mods/$MOD_NAME"
MANAGED_FILE="$TARGET_MOD/A_UNION_BEFORE_MIDNIGHT_MANAGED_FILES.txt"
INSTALL_MARKER="$TARGET_MOD/A_UNION_BEFORE_MIDNIGHT_INSTALL.json"

if [[ ! -d "$BASE_MOD" ]]; then
    printf 'Darkest Hour Full foundation not found: %s\n' "$BASE_MOD" >&2
    exit 1
fi

case "$TARGET_MOD" in
    "$GAME_ROOT/Mods/"* ) ;;
    *)
        printf 'Refusing unsafe target path: %s\n' "$TARGET_MOD" >&2
        exit 1
        ;;
esac

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/aubm-install.XXXXXX")"
trap 'rm -rf -- "$TEMP_ROOT"' EXIT
tr -d '\r' < "$MANIFEST" > "$TEMP_ROOT/manifest.txt"
tr -d '\r' < "$HASH_MANIFEST" > "$TEMP_ROOT/manifest-sha256.txt"

if grep -Evq '^[0-9A-Fa-f]{64} [ *].+$' "$TEMP_ROOT/manifest-sha256.txt"; then
    printf 'SHA-256 manifest contains an invalid line.\n' >&2
    exit 1
fi
sed -E 's/^[0-9A-Fa-f]{64} [ *]//' "$TEMP_ROOT/manifest-sha256.txt" \
    > "$TEMP_ROOT/hash-paths.txt"
LC_ALL=C sort "$TEMP_ROOT/manifest.txt" > "$TEMP_ROOT/manifest.sorted"
LC_ALL=C sort "$TEMP_ROOT/hash-paths.txt" > "$TEMP_ROOT/hash-paths.sorted"
if ! cmp -s "$TEMP_ROOT/manifest.sorted" "$TEMP_ROOT/hash-paths.sorted"; then
    printf 'Payload manifest and SHA-256 manifest do not name the same files.\n' >&2
    exit 1
fi
if [[ -n "$(LC_ALL=C sort "$TEMP_ROOT/manifest.txt" | uniq -d | head -n 1)" ]]; then
    printf 'Payload manifest contains duplicate paths.\n' >&2
    exit 1
fi

declare -A NEW_PATHS=()
while IFS= read -r relative || [[ -n "$relative" ]]; do
    [[ -n "$relative" ]] || continue
    case "$relative" in
        /*|*\\*|..|../*|*/../*|*/..|.)
            printf 'Unsafe path in manifest: %s\n' "$relative" >&2
            exit 1
            ;;
    esac
    [[ -f "$OVERLAY_ROOT/$relative" && ! -L "$OVERLAY_ROOT/$relative" ]] || {
        printf 'Manifest path must be a regular non-symlink file: %s\n' "$relative" >&2
        exit 1
    }
    NEW_PATHS["$relative"]=1
done < "$TEMP_ROOT/manifest.txt"

printf 'Validating %s managed payload files...\n' "${#NEW_PATHS[@]}"
(cd "$OVERLAY_ROOT" && sha256sum --check --strict --quiet "$TEMP_ROOT/manifest-sha256.txt")

if [[ -d "$TARGET_MOD" && ! -f "$INSTALL_MARKER" && "$FORCE" != 1 ]]; then
    printf 'Target exists but is not a managed AUBM installation: %s\n' "$TARGET_MOD" >&2
    printf 'Use --force only if this is the intended mod directory.\n' >&2
    exit 1
fi

mkdir -p -- "$RUNTIME_ROOT/bin"
install -m 0755 "$SCRIPT_DIR/configure-aubm-deck.sh" "$RUNTIME_ROOT/bin/configure-aubm-deck"
install -m 0755 "$SCRIPT_DIR/install-aubm-controller.sh" "$RUNTIME_ROOT/bin/install-aubm-controller"
install -m 0755 "$SCRIPT_DIR/manage-aubm-saves.sh" "$RUNTIME_ROOT/bin/manage-aubm-saves"
install -m 0755 "$SCRIPT_DIR/launch-aubm-deck.sh" "$RUNTIME_ROOT/bin/launch-aubm-deck"
install -Dm 0644 "$SCRIPT_DIR/controller/aubm-steam-deck.vdf" \
    "$RUNTIME_ROOT/controller/aubm-steam-deck.vdf"
install -m 0644 "$SCRIPT_DIR/README.md" "$RUNTIME_ROOT/README.md"

mkdir -p -- "$TARGET_MOD"
if [[ ! -f "$INSTALL_MARKER" ]]; then
    printf 'Creating isolated Darkest Hour Full foundation...\n'
    cp -a "$BASE_MOD/." "$TARGET_MOD/"
fi

if [[ -f "$MANAGED_FILE" ]]; then
    tr -d '\r' < "$MANAGED_FILE" > "$TEMP_ROOT/old-managed.txt"
    while IFS= read -r old_path || [[ -n "$old_path" ]]; do
        [[ -n "$old_path" ]] || continue
        if [[ -z "${NEW_PATHS[$old_path]+present}" ]]; then
            case "$old_path" in
                /*|*\\*|..|../*|*/../*|*/..|.)
                    printf 'Unsafe path in old managed manifest: %s\n' "$old_path" >&2
                    exit 1
                    ;;
            esac
            if [[ -f "$BASE_MOD/$old_path" ]]; then
                mkdir -p -- "$(dirname -- "$TARGET_MOD/$old_path")"
                cp -a -- "$BASE_MOD/$old_path" "$TARGET_MOD/$old_path"
            else
                rm -f -- "$TARGET_MOD/$old_path"
            fi
        fi
    done < "$TEMP_ROOT/old-managed.txt"
fi

printf 'Installing managed overlay...\n'
tar -C "$OVERLAY_ROOT" --verbatim-files-from -cf - -T "$TEMP_ROOT/manifest.txt" | \
    tar -C "$TARGET_MOD" -xf -

printf 'Verifying installed overlay...\n'
(cd "$TARGET_MOD" && sha256sum --check --strict --quiet "$TEMP_ROOT/manifest-sha256.txt")

cp -- "$TEMP_ROOT/manifest.txt" "$MANAGED_FILE"
VERSION="$(tr -d '\r\n' < "$VERSION_FILE")"
INSTALLED_AT="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}
printf '{\n  "version": "%s",\n  "installedAtUtc": "%s",\n  "platform": "steam-deck",\n  "sourceRoot": "%s",\n  "managedFiles": %s\n}\n' \
    "$(json_escape "$VERSION")" "$INSTALLED_AT" "$(json_escape "$SOURCE_ROOT")" \
    "${#NEW_PATHS[@]}" > "$INSTALL_MARKER"

CONFIG_FILE="$RUNTIME_ROOT/config.env"
{
    printf 'AUBM_GAME_ROOT=%q\n' "$GAME_ROOT"
    printf 'AUBM_MOD_ROOT=%q\n' "$TARGET_MOD"
    printf 'AUBM_SAVE_ROOT=%q\n' "$TARGET_MOD/scenarios/save games"
    printf 'AUBM_SETTINGS_FILE=%q\n' "$GAME_ROOT/settings.cfg"
    printf 'AUBM_MOD_NAME=%q\n' "$MOD_NAME"
    printf 'AUBM_BACKUP_ROOT=%q\n' "$RUNTIME_ROOT/save-backups"
    printf 'AUBM_KEEP_SNAPSHOTS=%q\n' 12
    printf 'AUBM_MAX_SNAPSHOT_FILES=%q\n' 12
} > "$CONFIG_FILE"
chmod 0600 "$CONFIG_FILE"

AUBM_RUNTIME_ROOT="$RUNTIME_ROOT" "$RUNTIME_ROOT/bin/launch-aubm-deck" --configure-only
AUBM_RUNTIME_ROOT="$RUNTIME_ROOT" "$RUNTIME_ROOT/bin/manage-aubm-saves" snapshot post-install || true

LAUNCH_OPTION="\"$RUNTIME_ROOT/bin/launch-aubm-deck\" -- %command%"
printf '%s\n' "$LAUNCH_OPTION" > "$RUNTIME_ROOT/steam-launch-option.txt"

printf '\nA Union Before Midnight %s is installed for Steam Deck.\n' "$VERSION"
printf 'Steam launch option:\n%s\n' "$LAUNCH_OPTION"
printf 'Save protection: %s\n' "$RUNTIME_ROOT/save-backups"
printf 'Controller profile: %s\n' "$RUNTIME_ROOT/controller/aubm-steam-deck.vdf"
if pgrep -f '/ubuntu12_32/steam([[:space:]]|$)' >/dev/null 2>&1; then
    printf 'Controller activation is pending because Steam is running. Exit Steam, then run:\n'
    printf '%q --runtime-root %q --profile %q --replace\n' \
        "$RUNTIME_ROOT/bin/install-aubm-controller" \
        "$RUNTIME_ROOT" \
        "$RUNTIME_ROOT/controller/aubm-steam-deck.vdf"
else
    "$RUNTIME_ROOT/bin/install-aubm-controller" \
        --runtime-root "$RUNTIME_ROOT" \
        --profile "$RUNTIME_ROOT/controller/aubm-steam-deck.vdf" \
        --replace
fi
