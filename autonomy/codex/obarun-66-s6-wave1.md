# Obarun 66/s6 survey and discovery change — Wave 1

Date: 2026-11-21  
Scope: source identity and service-manager discovery in the migration engine.

## Findings grounded in repository code

The discovery pipeline in `evolution-engine/src/discovery/__init__.py::discover`
runs base-system discovery before package, boot, storage, service, and capability
passes. `evolution-engine/src/discovery/system.py::_detect_init_system` already
distinguished runtime PID 1 evidence from installed files, but recognized
systemd, OpenRC, runit, and SysV only. It could therefore report an s6 PID 1
command name verbatim (for example `s6-svscan`) and had no independent record of
the 66 service manager. `evolution-engine/src/discovery/capabilities.py::derive_capabilities`
granted `service-management` only from systemd unit observations.

The repository's Wave 1 catalogue at
`autonomy/results/lead-migration-0001.md` lists candidate host paths such as
`/usr/bin/66`, `/etc/66/`, `/run/service/`, `/var/lib/66/`, and `/usr/lib/66/`.
These are useful paths to inspect, but that document explicitly describes them
as a capture set and does not contain captured Obarun filesystem evidence. Other
prior result files make conflicting claims about `/etc/s6-overlay/`, OpenRC,
`/66+`, and service definitions. This change does not treat those as verified
facts. It uses only independent, root-scoped markers and reports absence rather
than inferring an installation.

## Catalogue

| Concern | Exact current implementation path | Recorded semantics |
|---|---|---|
| PID 1 and init identity | `evolution-engine/src/discovery/system.py::_detect_init_system` | Direct PID 1 evidence wins; names beginning `s6-` normalize to init family `s6`. |
| 66 manager markers | `evolution-engine/src/discovery/system.py::_detect_66_manager` | Checks `/usr/bin/66`, `/usr/sbin/66`, `/etc/66` under the supplied root. One marker is MEDIUM/INSTALLED; two or more are HIGH/INSTALLED. No runtime or functional claim is made. |
| Service capability vocabulary | `evolution-engine/src/discovery/capabilities.py::derive_capabilities` | Adds `66-service-manager` on HIGH-confidence 66 evidence; makes a high-confidence 66 observation available as one corroborating signal for generic `service-management`. |
| Regression fixture | `evolution-engine/tests/test_discovery.py::DiscoveryTests.test_obarun_66_s6_is_detected_without_confusing_manager_and_init` | `T-OBARUN-66-001`; simulates PID 1 `s6-svscan`, `/usr/bin/66`, and `/etc/66` beneath a fake root. |
| Architecture constraints | `reports/ARCHITECTURE_DECISIONS.md` AD-04, AD-09, AD-14; `reports/USER_MIGRATION_MANDATE_2026-11-21.md` M-01..M-10 | Discovery stays capability-based, read-only, confidence-qualified, and source-state authoritative. |

## Change summary

- Added `s6` as a recognized init family using `s6` markers; normalized common
  `s6-*` PID 1 process names to `s6` while preserving the raw process in
  observation evidence.
- Added the independent `services.66` observation. Its evidence lists only
  which rooted markers exist. It never executes a host `66` command.
- Added the `66-service-manager` capability when two independent marker signals
  support a HIGH-confidence installed-manager observation.
- Added Obarun-like regression coverage. This is fixture-level behavior
  evidence, not a claim that an Obarun VM or image was surveyed.

## Verification and evidence

- Test ID: `T-OBARUN-66-001`.
- Command: `cd evolution-engine && python3 -m unittest tests.test_discovery`.
- Result: PASS; 7 tests ran.
- Detailed output: `autonomy/codex/obarun-66-s6-wave1-test.log`.
- Code paths: `evolution-engine/src/discovery/system.py`,
  `evolution-engine/src/discovery/capabilities.py`.
- Regression path: `evolution-engine/tests/test_discovery.py`.

## Limits

No Obarun image or source checkout was present in the inspected local ISO
corpus, so this wave implements identity discovery based on the repository's
candidate capture paths rather than claiming a byte-level source survey. The
presence of markers does not establish service state, package ownership, bundle
semantics, or safe executor support. Those require captured source-system
evidence and separate qualified transitions before any migration action.
