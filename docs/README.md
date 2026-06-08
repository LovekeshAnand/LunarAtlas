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

## Validation and Experiments

| File | Purpose |
|---|---|
| [`../evaluation/evaluation_framework.md`](../evaluation/evaluation_framework.md) | Formal metric definitions (ε_I, δ_λ, SNR, RMSE) |
| [`../experiment/LunarAtlas_Ablation_Study_Guide.pdf`](../experiment/LunarAtlas_Ablation_Study_Guide.pdf) | Full quantitative validation PDF guide |
| [`../experiment/run_full_ablation.py`](../experiment/run_full_ablation.py) | Automated validation experiment runner |
| [`../Benchmarks/benchmarks.md`](../Benchmarks/benchmarks.md) | Downsampling performance benchmarks |

---

## Submission Checklist

Before submitting to Elsevier SoftwareX, verify:

- [ ] `CITATION.cff` has real author names, institution, and Zenodo DOI filled in
- [ ] `DATA_AVAILABILITY.md` has the actual Zenodo DOI for processed dataset
- [ ] `README.md` badges link to real CI and Zenodo DOI
- [ ] `paper/paper.md` has author names and ORCID IDs
- [ ] All tests pass: `python -m pytest tests/ -v` → 33 passed
- [ ] GitHub repository is **public**
- [ ] At least one GitHub release tagged (e.g. `v1.0.0`) for Zenodo auto-DOI
