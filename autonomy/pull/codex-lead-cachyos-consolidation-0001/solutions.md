# Solutions

- Added `evolution-engine/src/evolution/research_catalog.py` for schema/provenance validation and fail-closed local source hash verification.
- Added `evolution-engine/tests/test_research_catalog.py`, covering valid catalogue structure, matching and changed source snapshots, traversal rejection and unverified evidence rejection.
- Catalogue evidence is observational and non-executable; it does not imply migration qualification.
