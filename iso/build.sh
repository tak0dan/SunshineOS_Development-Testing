#!/usr/bin/env bash
# Build the SunshineOS live repair/migration ISO with mkarchiso.
set -euo pipefail

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
PROFILE="$ROOT/iso/profile/sunshine"
STAGED="$ROOT/iso/.staged-profile"
WORK="$ROOT/iso/work"
OUT="$ROOT/iso/out"
CHECK_ONLY=0
SKIP_TESTS=0
BUILD_ID=${SUNSHINE_ISO_VERSION:-$(date -u +%Y%m%dT%H%M%SZ)}

log() { printf '[sunshine-iso] %s\n' "$*"; }
die() { printf '[sunshine-iso] ERROR: %s\n' "$*" >&2; exit 1; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --check) CHECK_ONLY=1; shift ;;
        --skip-tests) SKIP_TESTS=1; shift ;;
        --work) WORK=${2:?--work needs a directory}; shift 2 ;;
        --out) OUT=${2:?--out needs a directory}; shift 2 ;;
        --profile) PROFILE=${2:?--profile needs a directory}; shift 2 ;;
        --build-id) BUILD_ID=${2:?--build-id needs a value}; shift 2 ;;
        -h|--help)
            sed -n '2,12p' "$0"
            exit 0 ;;
        *) die "unknown argument: $1" ;;
    esac
done

if [ "$SKIP_TESTS" -eq 0 ]; then
    log "running toolkit tests"
    python3 -m unittest discover -s "$ROOT/iso/tests" -p 'test_*.py' -v
    log "running evolution-engine tests"
    (cd "$ROOT/evolution-engine" && python3 -m unittest discover -s tests -p 'test_*.py' -v)
else
    log "tests skipped by request"
fi

log "staging profile"
SUNSHINE_ISO_VERSION="$BUILD_ID" python3 "$ROOT/iso/tools/stage_profile.py" \
    --repo "$ROOT" --profile "$PROFILE" --staged "$STAGED" --build-id "$BUILD_ID"

if [ "$CHECK_ONLY" -eq 1 ]; then
    log "check complete; staged profile at $STAGED"
    exit 0
fi

missing=()
for tool in mkarchiso pacman xorriso mksquashfs bash; do
    command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done
if [ "${#missing[@]}" -gt 0 ]; then
    die "missing build tools: ${missing[*]} (install archiso, squashfs-tools and xorriso on an Arch build host)"
fi
if [ ! -f "$STAGED/airootfs/etc/mkinitcpio.conf.d/archiso.conf" ]; then
    die "staged profile is missing mkinitcpio-archiso configuration"
fi

mkdir -p "$WORK" "$OUT"
log "running mkarchiso"
mkarchiso -v -r -w "$WORK" -o "$OUT" "$STAGED"

ISO=$(find "$OUT" -maxdepth 1 -type f -name 'sunshineos-*.iso' -print | sort | tail -n 1)
[ -n "$ISO" ] || die "mkarchiso did not produce an ISO in $OUT"
log "verifying $ISO"
"$ROOT/iso/verify.sh" "$ISO"
(cd "$OUT" && sha256sum "$(basename "$ISO")" > manifest.sha256)
log "done: $ISO"
cat "$OUT/manifest.sha256"
