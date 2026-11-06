# Security policy

## Supported code

The latest `main` branch is the only supported development line. This is an
independent educational portfolio application, not a production banking system.

## Reporting

Do not open a public issue containing credentials, private datasets or an
exploitable proof of concept. Use GitHub's private vulnerability-reporting
channel when enabled, or contact the repository owner privately.

## Controls and boundaries

- No credentials are required for deterministic demonstration mode.
- Live market access uses public provider endpoints and fails closed; it does not
  silently replace missing live observations with synthetic data.
- Secrets belong in environment variables or uncommitted Streamlit secrets.
- Uploaded files are not supported. The application does not execute user code.
- CI installs the tested direct dependency set, runs `pip check`, performs a
  vulnerability audit, and executes the repository release gate.

## Current dependency finding

The 6 November 2026 clean-environment audit reported 39 advisories against the
transitive `Pillow 12.3.0` package, all naming `13.0.0` as the fix. Streamlit
1.65.0 constrains Pillow below 13, so that fix cannot be applied without an
upstream-compatible Streamlit release. The app does not accept image uploads or
process untrusted images, reducing exposure but not eliminating dependency risk.
The audit remains visible and non-blocking in CI; deployment approval is withheld
until the dependency constraint can be resolved or a documented risk decision is
made. Recheck before every release.
