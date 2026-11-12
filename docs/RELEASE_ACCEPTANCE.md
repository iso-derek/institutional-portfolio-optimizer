# Release-candidate acceptance

## Five completed assurance milestones

1. **Clean-install reproducibility:** tested direct dependencies are pinned and a
   fresh Windows installation succeeded from a documented short path.
2. **Security and dependency review:** `pip check`, a vulnerability audit,
   secret-handling boundaries and an ongoing CI audit are documented.
3. **Point-in-time universe control:** validated manifests require a dated,
   sourced, unique and explicitly verified membership set.
4. **Unseen holdout control:** protocols bind the universe hash, require a
   pre-holdout lock and keep holdout rows sealed until explicit unblinding.
5. **Release-candidate gate:** required evidence, direct pins, compilation,
   automated tests and visual acceptance are checked before handoff.

## Acceptance status

The software is a release candidate for review, not an approved public
deployment. Deployment remains blocked until a dependency audit confirms that
the Pillow 13.0.0 upgrade described in `SECURITY.md` clears the earlier
advisories, and by the absence of a verified confirmatory
dataset, and the requirement for explicit user approval of a hosting target and
operating-cost/privacy configuration.
