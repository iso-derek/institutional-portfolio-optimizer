# Clean-install rehearsal

**Rehearsal date:** 6 November 2026  
**Platform:** Windows, Python 3.12  
**Dependency input:** `requirements-tested.txt`

The first rehearsal under the repository's deeply nested checkout failed while
installing Streamlit because a packaged asset path exceeded the effective Windows
path limit. Repeating the installation in the short environment path
`C:\Users\derek\Documents\Codex\ipo-release-venv` succeeded.

From PowerShell:

```powershell
py -3.12 -m venv C:\venvs\portfolio
C:\venvs\portfolio\Scripts\python.exe -m pip install --upgrade pip
C:\venvs\portfolio\Scripts\python.exe -m pip install -r requirements-tested.txt
C:\venvs\portfolio\Scripts\python.exe -m pip check
C:\venvs\portfolio\Scripts\python.exe -m unittest discover -s tests -v
```

Verified result: dependency installation and `pip check` succeeded; 46 tests
passed in 51.504 seconds before the new governance tests were added. The final
suite result is maintained in `docs/DEVELOPMENT_STATUS.md`.

On Windows, keep the repository and virtual-environment paths short or enable
long-path support through approved system administration. Do not change system
policy merely to run this project.
