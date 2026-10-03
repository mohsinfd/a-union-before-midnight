#!/usr/bin/env bash
set -Eeuo pipefail

RUNTIME_ROOT="${AUBM_RUNTIME_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/aubm-deck}"
CONFIG_FILE="$RUNTIME_ROOT/config.env"
BACKUP_ROOT="${AUBM_BACKUP_ROOT:-$RUNTIME_ROOT/save-backups}"
KEEP_SNAPSHOTS="${AUBM_KEEP_SNAPSHOTS:-12}"
MAX_SNAPSHOT_FILES="${AUBM_MAX_SNAPSHOT_FILES:-12}"

usage() {
    cat <<'EOF'
Usage: manage-aubm-saves.sh COMMAND

Commands:
  snapshot [LABEL]  Archive the newest save pairs when they have changed
  mirror            Copy all current saves into the protected mirror
  list              List available snapshots
  restore-latest    Restore the newest snapshot without deleting other saves
  status            Show save and backup locations
EOF
}

if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
fi

MOD_ROOT="${AUBM_MOD_ROOT:-}"
SAVE_ROOT="${AUBM_SAVE_ROOT:-${MOD_ROOT:+$MOD_ROOT/scenarios/save games}}"
SYNC_DIR="${AUBM_DECK_SYNC_DIR:-}"

if [[ -z "$SAVE_ROOT" ]]; then
    printf 'No save directory is configured. Run install-aubm-deck.sh first.\n' >&2
    exit 1
fi

if [[ ! "$KEEP_SNAPSHOTS" =~ ^[1-9][0-9]*$ || ! "$MAX_SNAPSHOT_FILES" =~ ^[1-9][0-9]*$ ]]; then
    printf 'Snapshot retention values must be positive integers.\n' >&2
    exit 1
fi

case "$BACKUP_ROOT" in
    /|""|.)
        printf 'Unsafe backup directory: %s\n' "$BACKUP_ROOT" >&2
        exit 1
        ;;
esac

mkdir -p -- "$BACKUP_ROOT/snapshots" "$BACKUP_ROOT/current"

collect_recent_files() {
    local entry rel
    RECENT_FILES=()
    [[ -d "$SAVE_ROOT" ]] || return 0

    mapfile -d '' -t ranked < <(
        cd "$SAVE_ROOT"
        find . -maxdepth 1 -type f \( -iname '*.eug' -o -iname '*.eug.cfg' \) \
            -printf '%T@ %P\0' | sort -z -nr
    )

    for entry in "${ranked[@]}"; do
        rel="${entry#* }"
        [[ -n "$rel" ]] || continue
        RECENT_FILES+=("$rel")
        ((${#RECENT_FILES[@]} >= MAX_SNAPSHOT_FILES)) && break
    done
    return 0
}

mirror_saves() {
    local file
    [[ -d "$SAVE_ROOT" ]] || return 0
    while IFS= read -r -d '' file; do
        cp --preserve=mode,timestamps -- "$file" "$BACKUP_ROOT/current/"
        if [[ -n "$SYNC_DIR" ]]; then
            mkdir -p -- "$SYNC_DIR"
            cp --preserve=mode,timestamps -- "$file" "$SYNC_DIR/"
        fi
    done < <(find "$SAVE_ROOT" -maxdepth 1 -type f \( -iname '*.eug' -o -iname '*.eug.cfg' \) -print0)
}

prune_snapshots() {
    local -a snapshots=()
    local index
    mapfile -d '' -t snapshots < <(
        find "$BACKUP_ROOT/snapshots" -maxdepth 1 -type f -name '*.tar.gz' \
            -printf '%T@ %p\0' | sort -z -nr
    )
    for ((index=KEEP_SNAPSHOTS; index<${#snapshots[@]}; index++)); do
        rm -f -- "${snapshots[$index]#* }"
    done
}

snapshot_saves() {
    local label="${1:-manual}" safe_label signature previous timestamp archive file
    collect_recent_files
    if ((${#RECENT_FILES[@]} == 0)); then
        printf 'No Darkest Hour saves found in %s\n' "$SAVE_ROOT"
        return 0
    fi

    safe_label="$(printf '%s' "$label" | tr -cs 'A-Za-z0-9._-' '-')"
    signature="$({
        cd "$SAVE_ROOT"
        for file in "${RECENT_FILES[@]}"; do
            stat --printf '%n\t%s\t%Y\n' -- "$file"
        done
    } | sha256sum | awk '{print $1}')"
    previous="$(cat "$BACKUP_ROOT/last-signature" 2>/dev/null || true)"

    mirror_saves
    if [[ "$signature" == "$previous" ]]; then
        printf 'Saves are unchanged; protected mirror is current.\n'
        return 0
    fi

    timestamp="$(date -u +'%Y%m%dT%H%M%SZ')"
    archive="$BACKUP_ROOT/snapshots/${timestamp}-${safe_label}.tar.gz"
    tar -C "$SAVE_ROOT" -czf "$archive" -- "${RECENT_FILES[@]}"
    printf '%s\n' "$signature" > "$BACKUP_ROOT/last-signature"
    prune_snapshots
    printf 'Created save snapshot: %s\n' "$archive"
}

restore_latest() {
    local latest entry
    latest="$(find "$BACKUP_ROOT/snapshots" -maxdepth 1 -type f -name '*.tar.gz' \
        -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2- || true)"
    if [[ -z "$latest" ]]; then
        printf 'No snapshots are available.\n' >&2
        exit 1
    fi
    while IFS= read -r entry; do
        case "$entry" in
            ""|/*|..|../*|*/../*|*/..)
                printf 'Unsafe path in snapshot: %s\n' "$entry" >&2
                exit 1
                ;;
        esac
    done < <(tar -tzf "$latest")
    mkdir -p -- "$SAVE_ROOT"
    snapshot_saves pre-restore
    tar -C "$SAVE_ROOT" -xzf "$latest"
    printf 'Restored snapshot: %s\n' "$latest"
}

command="${1:-status}"
case "$command" in
    snapshot)
        snapshot_saves "${2:-manual}"
        ;;
    mirror)
        mirror_saves
        printf 'Protected save mirror updated: %s\n' "$BACKUP_ROOT/current"
        ;;
    list)
        find "$BACKUP_ROOT/snapshots" -maxdepth 1 -type f -name '*.tar.gz' \
            -printf '%TY-%Tm-%Td %TH:%TM  %f\n' | sort -r
        ;;
    restore-latest)
        restore_latest
        ;;
    status)
        printf 'Game saves:      %s\n' "$SAVE_ROOT"
        printf 'Protected mirror: %s\n' "$BACKUP_ROOT/current"
        printf 'Snapshots:        %s\n' "$BACKUP_ROOT/snapshots"
        [[ -n "$SYNC_DIR" ]] && printf 'Optional sync:     %s\n' "$SYNC_DIR"
        ;;
    --help|-h|help)
        usage
        ;;
    *)
        printf 'Unknown command: %s\n' "$command" >&2
        usage >&2
        exit 2
        ;;
esac
