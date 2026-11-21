# codex-lead-0012 -> hierarchy

# Artix runit/OpenRC enforcement — Wave 1

Updated `ArtixServicePlan` to expose `activation_transition_required`. Runit `enabled` and `disabled` plans now explicitly mark persistent activation as unresolved because their commands change runtime state only. This gives callers a machine readable signal that they need a separately qualified activation transition.

**Survey and change summary:** [artix-runit-openrc-wave1-enforcement.md](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/artix-runit-openrc-wave1-enforcement.md)

**Regression coverage:** `ARTIX_SVC_001`–`ARTIX_SVC_008` in [test_artix_services.py](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/evolution-engine/tests/test_artix_services.py). Targeted tests: **8 passed**. Full suite: **173 passed**. Logs: [artix-runit-openrc-wave1-enforcement-test.log](/home/tak_0/sunshineos-audit/SunshineOS_Development-Testing/autonomy/codex/artix-runit-openrc-wave1-enforcement-test.log).

The local ISO manifest lists Artix OpenRC and dinit images, but no runit image; this work does not establish end-to-end runit qualification.

I could not commit the changes: Git could not create `.git/index.lock` because `.git` is read-only in this environment. The other existing worktree changes were left untouched.
