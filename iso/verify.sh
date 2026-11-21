#!/usr/bin/env bash
# Verify a built SunshineOS ISO without mounting it.
set -euo pipefail

usage() { printf 'usage: %s PATH_TO_ISO\n' "$0" >&2; }
[ "$#" -eq 1 ] || { usage; exit 2; }
ISO=$1
[ -f "$ISO" ] || { printf 'missing ISO: %s\n' "$ISO" >&2; exit 2; }
command -v xorriso >/dev/null 2>&1 || { printf 'xorriso is required\n' >&2; exit 2; }

size=$(stat -c%s "$ISO")
if [ "$size" -lt 50000000 ]; then
    printf 'ISO is implausibly small: %s bytes\n' "$size" >&2
    exit 1
fi

printf '[sunshine-verify] size=%s bytes\n' "$size"
if xorriso -indev "$ISO" -report_el_torito plain 2>/dev/null | grep -qi 'El Torito'; then
    printf '[sunshine-verify] boot catalog: present\n'
else
    printf '[sunshine-verify] boot catalog: missing\n' >&2
    exit 1
fi

if xorriso -indev "$ISO" -find /sunshine/boot -maxdepth 4 2>/dev/null | grep -q 'vmlinuz-linux'; then
    printf '[sunshine-verify] kernel image: present\n'
else
    printf '[sunshine-verify] kernel image: missing\n' >&2
    exit 1
fi

if xorriso -indev "$ISO" -pvd_info 2>/dev/null | grep -qi 'SunshineOS'; then
    printf '[sunshine-verify] publisher/application identity: present\n'
else
    printf '[sunshine-verify] publisher/application identity: missing\n' >&2
    exit 1
fi

sha256sum "$ISO"
