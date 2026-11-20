# Repair reporting and telemetry schema

- Agent: sub-repair-gui
- Model: nvidia/nemotron-3.5-lightning:free
- Completed: 2026-11-21 00:15

---

# Privacy-Preserving Repair Report Schema

**Source:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md` · `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md`  
**Purpose:** Standardized, privacy-first incident documentation for evolutionary migration repair events. All fields omit host identifiers, credentials, or PII.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `incident_id` | `string` | Stable, immutable identifier for the repair incident. | Hash or versioned ID; no hostnames, MACs, or UUIDs tied to hardware. |
| `detected_deviation` | `string` | Semantic description of the deviation from expected state. | Reference invariant IDs (e.g., `INV7`, `M-06`) not filesystem paths. |
| `actions_taken` | `array of strings` | Sequence of repair operations executed. | Each action must be recoverable per `M-06`; no credential exposure. |
| `before_hash` | `string` | Content hash of system state pre-repair. | SHA-3 or equivalent; no PII. |
| `after_hash` | `string` | Content hash of system state post-repair. | Same as above. |
| `verification_result` | `enum` | `pass` / `fail` / `staged` | Based on validation against target-state driven model (`M-01`). |
| `recovery_reference` | `string` | Identifier for compensating procedure or baseline to revert/redo. | References `B0-2026`, `B-1-2015` or evolution event IDs. |

## Invariants Enforced
- **`M-06`**: All operations in `actions_taken` must have explicit recovery procedures referenced in `recovery_reference`.
- **`M-09`**: Re-running discovery must not produce uncontrolled duplication; `incident_id` must be unique and immutable.
- **`M-10`**: `detected_deviation` and `actions_taken` separate user data from OS reconstruction; schema carries only structural metadata.

## Example Entry (Anonymized)

```yaml
incident_id: "hash:deadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678"
detected_deviation: "service_x transition failure during E038→E039 migration"
actions_taken:
  - "paused executor per M-05"
  - "validated target state against inventory schema INV7"
  - "applied compensating transition from recovery_reference"
before_hash: "sha3:0123456789abcdef...0123456789abcdef..."
after_hash: "sha3:abcdef0123456789...0123456789abcdef..."
verification_result: "pass"
recovery_reference: "B0-2026::E038"
```

## Usage
- Publish to `evidence/` or `reports/` branches under the evolutionary milestone tag.
- Reference in `evolution-engine/` transition catalog for pattern analysis.
- Never commit host-specific data, keys, or credentials per `M-07` (artifact archiving) and operational security.

**Repository citations:** `reports/USER_MIGRATION_MANDATE_2026-11-21.md` (ID: M-20261121), `reports/OPENCLAW_ORDER_3_CONVERGENCE_ARCHITECTURE.md` (ID: OC-3-CONV).
