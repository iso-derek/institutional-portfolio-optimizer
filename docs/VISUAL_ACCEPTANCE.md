# Visual and accessibility acceptance

**Acceptance date:** 5 November 2026  
**Application mode:** Deterministic demonstration  
**Browser engine:** Installed Google Chrome, headless  

## Captured views

| View | CSS viewport | Evidence | Result |
|---|---:|---|---|
| Desktop | 1440 × 1100 | `screenshots/dashboard-desktop.png` | Pass |
| Mobile | 390 × 844 at 2× scale | `screenshots/dashboard-mobile.png` | Pass |

The screenshots are direct captures of the running Streamlit application. They
confirm that the synthetic-data disclosure remains prominent, the input sidebar
is usable on desktop and collapses on mobile, executive metrics wrap without
horizontal page overflow, and primary tab navigation remains available.

## Accessibility contract

- Every chart has a short `alt=` name describing its analytical purpose.
- Every dataframe and editable grid has a short `alt=` name for findability.
- Visible widget labels are retained for portfolio inputs and research controls.
- Disclosure and caution text use semantic Streamlit alert elements.
- `tests/test_accessibility.py` parses the application and fails if a chart,
  dataframe, table, media element or editable grid is added without `alt=`.
- `tests/test_app.py` continues to exercise the deterministic dashboard with
  Streamlit's first-party `AppTest` runner.

## Reproduction

1. Start the app on port 8501.
2. Start a local Chrome instance with remote debugging on port 9222.
3. Run `node scripts/capture_screenshots.js`.
4. Inspect both PNG files rather than accepting file creation alone.

The capture script intentionally targets localhost and writes only the two named
PNG files. Screenshots cover the initial executive view; interaction semantics
and analytical results remain covered by the automated test suite.
