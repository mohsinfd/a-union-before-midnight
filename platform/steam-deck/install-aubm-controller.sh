#!/usr/bin/env bash
set -Eeuo pipefail

APP_ID=73170
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
STEAM_ROOT="${AUBM_STEAM_ROOT:-$HOME/.local/share/Steam}"
RUNTIME_ROOT="${AUBM_RUNTIME_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/aubm-deck}"
PROFILE_SOURCE="${AUBM_CONTROLLER_PROFILE:-$SCRIPT_DIR/controller/aubm-steam-deck.vdf}"
ACCOUNT_ID="${AUBM_STEAM_ACCOUNT_ID:-}"
REPLACE=0

usage() {
    cat <<'EOF'
Usage: install-aubm-controller.sh [options]

Install the AUBM Steam Deck layout as Darkest Hour's per-game autosave.
Steam must be fully stopped so it cannot overwrite the registration.

Options:
  --steam-root PATH   Steam installation root
  --runtime-root PATH AUBM helper data directory
  --profile PATH      Controller profile VDF
  --account-id ID     Steam account ID directory
  --replace           Back up and replace an existing Darkest Hour layout
  --help              Show this help
EOF
}

while (($#)); do
    case "$1" in
        --steam-root)
            STEAM_ROOT="${2:?--steam-root requires a path}"
            shift 2
            ;;
        --runtime-root)
            RUNTIME_ROOT="${2:?--runtime-root requires a path}"
            shift 2
            ;;
        --profile)
            PROFILE_SOURCE="${2:?--profile requires a path}"
            shift 2
            ;;
        --account-id)
            ACCOUNT_ID="${2:?--account-id requires an ID}"
            shift 2
            ;;
        --replace)
            REPLACE=1
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

for tool in awk cp date find grep install mkdir mktemp mv pgrep rm sha256sum sort; do
    command -v "$tool" >/dev/null || {
        printf 'Required tool is missing: %s\n' "$tool" >&2
        exit 1
    }
done

[[ -f "$PROFILE_SOURCE" ]] || {
    printf 'Controller profile not found: %s\n' "$PROFILE_SOURCE" >&2
    exit 1
}

if pgrep -f '/ubuntu12_32/steam([[:space:]]|$)' >/dev/null 2>&1; then
    printf 'Steam is running. Exit Steam completely, then run this command again.\n' >&2
    exit 3
fi

CONFIGS_ROOT="$STEAM_ROOT/steamapps/common/Steam Controller Configs"
if [[ -z "$ACCOUNT_ID" ]]; then
    mapfile -t CONFIG_SETS < <(
        find "$CONFIGS_ROOT" -mindepth 3 -maxdepth 3 -type f \
            -name configset_controller_neptune.vdf 2>/dev/null | sort
    )
    if ((${#CONFIG_SETS[@]} != 1)); then
        printf 'Expected one Steam Deck account configuration, found %s.\n' \
            "${#CONFIG_SETS[@]}" >&2
        printf 'Pass --account-id with the numeric Steam userdata directory.\n' >&2
        exit 1
    fi
    CONFIG_SET="${CONFIG_SETS[0]}"
    ACCOUNT_ID="${CONFIG_SET#"$CONFIGS_ROOT/"}"
    ACCOUNT_ID="${ACCOUNT_ID%%/*}"
else
    [[ "$ACCOUNT_ID" =~ ^[0-9]+$ ]] || {
        printf 'Steam account ID must contain digits only: %s\n' "$ACCOUNT_ID" >&2
        exit 1
    }
    CONFIG_SET="$CONFIGS_ROOT/$ACCOUNT_ID/config/configset_controller_neptune.vdf"
fi

[[ -f "$CONFIG_SET" ]] || {
    printf 'Steam Deck controller config set not found: %s\n' "$CONFIG_SET" >&2
    exit 1
}

TARGET_DIR="$CONFIGS_ROOT/$ACCOUNT_ID/config/$APP_ID"
TARGET_PROFILE="$TARGET_DIR/controller_neptune.vdf"
STAMP="$(date -u +'%Y%m%d-%H%M%S')"
BACKUP_DIR="$RUNTIME_ROOT/controller-backups/$STAMP"
mkdir -p -- "$BACKUP_DIR"
cp --preserve=mode,timestamps -- "$CONFIG_SET" "$BACKUP_DIR/configset_controller_neptune.vdf"
if [[ -f "$TARGET_PROFILE" ]]; then
    cp --preserve=mode,timestamps -- "$TARGET_PROFILE" "$BACKUP_DIR/controller_neptune.vdf"
fi

REGISTERED=0
if grep -Eq "^[[:space:]]*\"${APP_ID}\"[[:space:]]*$" "$CONFIG_SET"; then
    REGISTERED=1
    if [[ -f "$TARGET_PROFILE" ]] && \
       grep -A4 -E "^[[:space:]]*\"${APP_ID}\"[[:space:]]*$" "$CONFIG_SET" | \
           grep -Eq '"autosave"[[:space:]]+"1"'; then
        if ((REPLACE == 0)); then
            printf 'Darkest Hour already has a per-game controller layout; leaving user edits intact.\n'
            exit 0
        fi
    elif ((REPLACE == 0)); then
        printf 'Darkest Hour already has a different controller registration.\n' >&2
        printf 'Backup created at %s; no existing layout was replaced.\n' "$BACKUP_DIR" >&2
        exit 4
    elif ! grep -A4 -E "^[[:space:]]*\"${APP_ID}\"[[:space:]]*$" "$CONFIG_SET" | \
        grep -Eq '"autosave"[[:space:]]+"1"'; then
        printf 'Darkest Hour has an unsupported controller registration.\n' >&2
        printf 'Backup created at %s; registration was not rewritten.\n' "$BACKUP_DIR" >&2
        exit 4
    fi
fi

mkdir -p -- "$TARGET_DIR"
TEMP_PROFILE="$(mktemp "$TARGET_DIR/.controller_neptune.XXXXXX")"
TEMP_CONFIG=""
cleanup() {
    rm -f -- "$TEMP_PROFILE" "$TEMP_CONFIG"
}
trap cleanup EXIT

install -m 0644 "$PROFILE_SOURCE" "$TEMP_PROFILE"

if ((REGISTERED == 0)); then
    TEMP_CONFIG="$(mktemp "${CONFIG_SET}.aubm.XXXXXX")"
    awk -v app_id="$APP_ID" '
BEGIN { depth = 0; inserted = 0 }
{
    if (!inserted && depth == 1 && $0 ~ /^[[:space:]]*}[[:space:]]*$/) {
        print "\t\"" app_id "\""
        print "\t{"
        print "\t\t\"autosave\"\t\t\"1\""
        print "\t}"
        inserted = 1
    }
    print
    brace_line = $0
    opens = gsub(/\{/, "", brace_line)
    brace_line = $0
    closes = gsub(/\}/, "", brace_line)
    depth += opens - closes
}
END { if (!inserted) exit 42 }
' "$CONFIG_SET" > "$TEMP_CONFIG" || {
        printf 'Could not register the layout in Steam controller configuration.\n' >&2
        exit 1
    }

    grep -Fq "\"$APP_ID\"" "$TEMP_CONFIG" || {
        printf 'Controller registration validation failed.\n' >&2
        exit 1
    }
    grep -Fq '"autosave"' "$TEMP_CONFIG" || {
        printf 'Controller autosave validation failed.\n' >&2
        exit 1
    }
fi

mv -f -- "$TEMP_PROFILE" "$TARGET_PROFILE"
if [[ -n "$TEMP_CONFIG" ]]; then
    mv -f -- "$TEMP_CONFIG" "$CONFIG_SET"
fi
trap - EXIT

if ((REGISTERED == 1)); then
    printf 'Replaced AUBM Strategy Controls for Darkest Hour (AppID %s).\n' "$APP_ID"
else
    printf 'Installed AUBM Strategy Controls for Darkest Hour (AppID %s).\n' "$APP_ID"
fi
printf 'Profile: %s\n' "$TARGET_PROFILE"
printf 'Backup: %s\n' "$BACKUP_DIR"
printf 'SHA-256: '
sha256sum "$TARGET_PROFILE" | awk '{print $1}'
