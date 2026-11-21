# Solution

Added `evolution-engine/src/evolution/markers.py::validate_user_completion_markers`. Marker evidence must agree with a completed journal output and fresh observed output. Orphaned, empty, missing, or divergent evidence returns errors; no state is mutated.

Tests OMR-005 through OMR-008 exercise agreement, root rollback, orphan markers, and missing observation.
