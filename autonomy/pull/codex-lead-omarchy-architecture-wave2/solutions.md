Added `OMR_004` to `evolution-engine/tests/test_omarchy_recovery_consistency.py`. It validates catalogue schema and checks control phrases for per-user migration markers, bypassable package guards, snapshot marker staleness, direct update/config ownership, and notification separation.

No upstream scripts are copied or executed. The fixture remains provenance, not migration policy.
