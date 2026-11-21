# SunshineOS image artifact — 2026-11-21

## CI result

The image build workflow completed successfully on commit `82082b1`.

- Workflow: `SunshineOS image build` (`iso-build.yml`)
- Run: `44900167130`
- Artifact: `sunshineos-iso`
- Image: `sunshineos-2026.11.21-x86_64.iso`
- Size: `1,191,051,264` bytes
- SHA-256: `0bd1bd6c8bb692a7b34b8688545fcda7aff7841723e603a38b65dab572ff5e3c`

## Verification performed by the build

`iso/verify.sh` checked the produced artifact with `xorriso`:

- size is plausible for a live image
- El Torito boot catalog is present
- `/sunshine/boot/.../vmlinuz-linux` is present
- publisher/application identity reports SunshineOS
- SHA-256 manifest was generated in the artifact

All checks passed. The workflow also ran 20 ISO toolkit tests and 317
evolution-engine regression tests, staged and validated the archiso profile,
and passed the CI trust-policy audit.

This is structural verification. It does not claim a BIOS or UEFI boot test, an
installation test, or an end-to-end update/migration run on the booted image.

## Remaining validation

1. Boot the artifact in BIOS and UEFI.
2. Install it to a scratch disk or VM.
3. Run `sunshine-health`, `sunshine-sanity`, `sunshine-report` and the repair
   assessment on the booted system.
4. Exercise fixture-based `sunshine-upgrade` / `sunshine-migrate` planning and
   verify that signed Stage A inputs are required for apply.
