#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SOURCE_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd -P)"
OUTPUT_DIR="$SOURCE_ROOT/dist"
VERIFY_ONLY=0

usage() {
    cat <<'EOF'
Usage: package-aubm-deck.sh [options]

Options:
  --source-root PATH  AUBM repository/package root
  --output-dir PATH   Destination directory (default: dist)
  --verify-only       Validate package inputs without creating an archive
  --help              Show this help
EOF
}

while (($#)); do
    case "$1" in
        --source-root)
            SOURCE_ROOT="${2:?--source-root requires a path}"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="${2:?--output-dir requires a path}"
            shift 2
            ;;
        --verify-only)
            VERIFY_ONLY=1
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

for tool in cmp find gzip mktemp sed sha256sum sort tar tr uniq; do
    command -v "$tool" >/dev/null || {
        printf 'Required packaging tool is missing: %s\n' "$tool" >&2
        exit 1
    }
done

SOURCE_ROOT="$(cd -- "$SOURCE_ROOT" && pwd -P)"
MANIFEST="$SOURCE_ROOT/installer/manifest.txt"
HASH_MANIFEST="$SOURCE_ROOT/installer/manifest-sha256.txt"
VERSION_FILE="$SOURCE_ROOT/VERSION"

for required in "$MANIFEST" "$HASH_MANIFEST" "$VERSION_FILE" \
    "$SOURCE_ROOT/mod" "$SOURCE_ROOT/platform/steam-deck/install-aubm-deck.sh"; do
    [[ -e "$required" ]] || {
        printf 'Required package input not found: %s\n' "$required" >&2
        exit 1
    }
done

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/aubm-package.XXXXXX")"
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

while IFS= read -r relative || [[ -n "$relative" ]]; do
    [[ -n "$relative" ]] || continue
    case "$relative" in
        /*|*\\*|..|../*|*/../*|*/..|.)
            printf 'Unsafe payload path: %s\n' "$relative" >&2
            exit 1
            ;;
    esac
    [[ -f "$SOURCE_ROOT/mod/$relative" && ! -L "$SOURCE_ROOT/mod/$relative" ]] || {
        printf 'Payload path must be a regular non-symlink file: mod/%s\n' "$relative" >&2
        exit 1
    }
done < "$TEMP_ROOT/manifest.txt"

printf 'Validating payload hashes before packaging...\n'
(cd "$SOURCE_ROOT/mod" && sha256sum --check --strict --quiet "$TEMP_ROOT/manifest-sha256.txt")

if ((VERIFY_ONLY)); then
    printf 'Steam Deck package inputs are valid.\n'
    exit 0
fi

{
    printf '%s\n' VERSION docs/STEAM_DECK.md installer/manifest.txt installer/manifest-sha256.txt
    find "$SOURCE_ROOT/platform/steam-deck" -type f -printf 'platform/steam-deck/%P\n'
    sed 's#^#mod/#' "$TEMP_ROOT/manifest.txt"
} | sort -u > "$TEMP_ROOT/archive-files.txt"

while IFS= read -r relative || [[ -n "$relative" ]]; do
    [[ -f "$SOURCE_ROOT/$relative" ]] || {
        printf 'Archive input is missing: %s\n' "$relative" >&2
        exit 1
    }
done < "$TEMP_ROOT/archive-files.txt"

VERSION="$(tr -d '\r\n' < "$VERSION_FILE")"
SAFE_VERSION="$(printf '%s' "$VERSION" | tr -cs 'A-Za-z0-9._-' '-')"
mkdir -p -- "$OUTPUT_DIR"
ARCHIVE="$OUTPUT_DIR/a-union-before-midnight-${SAFE_VERSION}-steam-deck.tar.gz"
TEMP_ARCHIVE="$ARCHIVE.partial"
STAGED_ARCHIVE="$TEMP_ROOT/aubm-steam-deck.tar.gz"
rm -f -- "$TEMP_ARCHIVE"

printf 'Creating Steam Deck package on the Linux filesystem...\n'
tar -C "$SOURCE_ROOT" --verbatim-files-from -cf - -T "$TEMP_ROOT/archive-files.txt" \
    --checkpoint=250000 --checkpoint-action='echo=Archived %u records (about 128 MB)' | \
    gzip -1 > "$STAGED_ARCHIVE"
gzip -t "$STAGED_ARCHIVE"
tar -tzf "$STAGED_ARCHIVE" >/dev/null
printf 'Copying verified package to %s...\n' "$OUTPUT_DIR"
cp -- "$STAGED_ARCHIVE" "$TEMP_ARCHIVE"
mv -f -- "$TEMP_ARCHIVE" "$ARCHIVE"
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

printf 'Created: %s\n' "$ARCHIVE"
printf 'Checksum: %s.sha256\n' "$ARCHIVE"
