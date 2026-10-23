# Archived release for the revision — prepared, NOT created

Nothing below has been run. Each step publishes something and needs the owner's explicit go-ahead.

## Proposed release

- **Version:** `v1.1.0` (behaviour changes: unpaired plasma excluded, clip-fraction definition, new DB
  columns, ingestion no longer drops tables). Note: `CITATION.cff` says `1.0.0`, while the manuscript and
  Zenodo record cite v1.0.1. Confirm which number the current Zenodo record carries.
- **Source:** branch `revision/audit-v2` (local only, never pushed). The latest commit hash is in
  `git log -1`; `outputs/clean_checkout/report.json` records the commit that passed the clean-checkout test.
- **Decide first:** whether `revision_v2/paper/` (manuscript, response letter) goes into the public
  repository. `.gitignore` kept `docs/` local on purpose. If not, remove it from the branch before
  pushing, and attach the manuscript to the Zenodo record only if wanted.

## Release notes (draft)

> **LunarAtlas v1.1.0 — revision for the SoftwareX resubmission**
> - Stage 2 excludes plasma acquisitions without a preceding background (previously stored
>   unsubtracted). It also records the paired background row and the clip fraction, now defined as
>   residuals that are negative before clamping.
> - Ingestion no longer drops tables, is idempotent, and uses the stage-2 plasma rule for raw records.
>   It stores `background_subtracted`, `background_row` and `clip_fraction`, and runs `ANALYZE`.
> - `revision_v2/` holds the archive audit, determinism check, isolated ingestion check, analysis,
>   figures, local benchmark, web-viewer downsampling evaluation, migration tool and rehearsal, and
>   clean-checkout test, with all outputs and logs.
> - Known limitations: the public demo still serves legacy-ingested records; the API does not return
>   the quality fields; `/api/v1/cache/clear` is unauthenticated and ineffective; the archive carries
>   two wavelength axes (inquiry pending).

## Steps (each needs approval)

1. Review and finalise `CITATION.cff` (abstract updated locally; set `version`, `date-released`).
2. `git push -u origin revision/audit-v2`, then open a PR to `main` and merge it.
3. `git tag -a v1.1.0 -m "LunarAtlas v1.1.0"` on the merge commit; `git push origin v1.1.0`.
4. Create the GitHub release from the tag. The Zenodo–GitHub integration then mints a new version DOI
   under concept DOI 10.5281/zenodo.20771542; or upload to Zenodo manually.
5. Replace "pending" in the manuscript with the new version DOI and commit hash: Code-metadata C1 and
   the Software Availability "Archived version" line in `revision_v2/paper/paper.tex`; add a `paper.bib`
   entry for the new version. Recompile.
