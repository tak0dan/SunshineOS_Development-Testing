# Solution

Extended `evolution-engine/src/evolution/tools/ci_policy.py::audit_workflow` with a `CI_DOCKER_IMAGE_MUTABLE` finding for untagged or `:latest` images passed to docker run, including shell line continuations. Added `CI_OMARCHY_001` and `CI_OMARCHY_002` regression cases in `evolution-engine/tests/test_ci_policy.py`.

Verification: `cd evolution-engine && python3 -m unittest tests.test_ci_policy -v` — 5 passed. Evidence: `autonomy/codex/omarchy-ci-wave1-test.log`.
