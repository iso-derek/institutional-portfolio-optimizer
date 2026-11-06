# Confirmatory study governance

The current empirical work is exploratory. A confirmatory claim requires a
point-in-time universe and outcomes that were not inspected while choosing the
specification.

## Workflow

1. Replace `research/universe_manifest.template.json` with a citable archived
   membership source and set `point_in_time_verified` only after verification.
2. Validate it and record the canonical SHA-256 produced by
   `scripts/validate_confirmatory.py`.
3. Copy `research/confirmatory_protocol.template.json`, insert that hash, fix all
   parameters and primary outcomes, set an aware `locked_at` timestamp, and
   change status to `locked` before acquiring or inspecting holdout outcomes.
4. Preserve frozen adjusted-price bytes and their source/licensing sidecar.
5. Run development analysis only. `split_confirmatory_prices` returns no holdout
   data while the protocol is locked.
6. After the analysis plan is complete, record the unblinding decision, change
   status to `unblinded`, evaluate once, and report all pre-specified outcomes,
   failures and negative findings.

The committed JSON files are templates, not verified universes or completed
studies. The application must not describe exploratory results as confirmatory.
