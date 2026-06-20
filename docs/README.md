# LunarAtlas Documentation Index

Welcome to the LunarAtlas documentation. This index maps every document
in the `docs/` directory to its purpose.

---

## Paper Submission

| Document | Purpose |
|---|---|
| [`paper/paper.md`](paper/paper.md) | **Main manuscript** — SoftwareX submission draft |
| [`paper/paper.bib`](paper/paper.bib) | BibTeX bibliography |
| [`paper/new.tex`](paper/new.tex) | Full LaTeX draft (alternative journal format) |
| [`paper/latest_draft.tex`](paper/latest_draft.tex) | Current working LaTeX draft |

---

## Scientific Documentation

| Document | Purpose |
|---|---|
| [`what_and_why_downsampling.md`](what_and_why_downsampling.md) | Scientific rationale for LTTB + Peak Lock approach |
| [`ablation_study/`](ablation_study/) | LaTeX ablation tables and section text |

---

## API Reference

| Document | Purpose |
|---|---|
| [`api/README.md`](api/README.md) | Full REST API endpoint reference |

---

## From the Repository Root

These documents also form part of the research-grade repository standard:

| File | Purpose |
|---|---|
| [`../CITATION.cff`](../CITATION.cff) | Machine-readable citation metadata (GitHub + Zenodo) |
| [`../DATA_AVAILABILITY.md`](../DATA_AVAILABILITY.md) | Elsevier-required data availability statement |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Version history following Keep a Changelog |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Contributor guide |
| [`../CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | Contributor Covenant Code of Conduct |

---

## Validation and Performance Benchmarks

| File | Purpose |
|---|---|
| [`../Benchmarks/benchmarks.md`](../Benchmarks/benchmarks.md) | Downsampling performance benchmarks and latency reports |
| [`../Benchmarks/run_benchmarks.py`](../Benchmarks/run_benchmarks.py) | Automated benchmarking script for downsampling algorithms |

---

## Submission Checklist

Before submitting to Elsevier SoftwareX, verify:

- [x] `CITATION.cff` has real author names, institution, and Zenodo DOI filled in
- [x] `DATA_AVAILABILITY.md` has the actual Zenodo DOI for processed dataset
- [x] `README.md` badges link to real CI and Zenodo DOI
- [x] `paper/paper.md` has author names and ORCID IDs
- [x] All tests pass: `python -m pytest tests/ -v` → 33 passed
- [x] GitHub repository is **public**
- [x] At least one GitHub release tagged (e.g. `v1.0.0`) for Zenodo auto-DOI
