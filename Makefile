# LunarAtlas — Developer Makefile
# Run any target with: make <target>
# On Windows, use: python -m make or run the commands directly.

.PHONY: help install test lint benchmark pipeline-dry clean docs

# ─── Default target ────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "LunarAtlas Developer Commands"
	@echo "─────────────────────────────────────────────────"
	@echo "  make install       Install all Python dependencies"
	@echo "  make test          Run the full pytest test suite"
	@echo "  make lint          Run flake8 code quality checks"
	@echo "  make benchmark     Run the downsampling benchmark suite"
	@echo "  make pipeline-dry  Validate pipeline scripts (dry-run check)"
	@echo "  make clean         Remove __pycache__ and .pytest_cache"
	@echo "  make docs          Show documentation paths"
	@echo ""

# ─── Setup ─────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt
	@echo "[OK] Dependencies installed."

# ─── Tests ─────────────────────────────────────────────────────────────────
test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v \
		--cov=core/server/app/core \
		--cov-report=term-missing \
		--cov-report=html:docs/coverage

# ─── Lint ──────────────────────────────────────────────────────────────────
lint:
	flake8 Pipeline/ core/server/app/core/ --max-line-length=100

# ─── Benchmarks ────────────────────────────────────────────────────────────
benchmark:
	python Benchmarks/run_benchmarks.py

# ─── Pipeline dry-run (syntax check only) ──────────────────────────────────
pipeline-dry:
	@echo "Checking Pipeline scripts for syntax errors..."
	python -m py_compile Pipeline/step1_structure_study.py && echo "[OK] step1"
	python -m py_compile Pipeline/step2_process_l1_data.py && echo "[OK] step2"
	python -m py_compile Pipeline/step3_graph_plotting.py  && echo "[OK] step3"
	python -m py_compile Pipeline/step4_nist_verification_logs.py && echo "[OK] step4"
	python -m py_compile Pipeline/step5_md5_checksums.py   && echo "[OK] step5"
	python -m py_compile Pipeline/step6_segregate_data_folders.py && echo "[OK] step6"
	python -m py_compile Pipeline/step7_db_ingestion.py    && echo "[OK] step7"
	python -m py_compile Pipeline/step8_data_verification.py && echo "[OK] step8"
	@echo "All pipeline scripts pass syntax check."

# ─── Clean ─────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "[OK] Cleaned build artifacts."

# ─── Docs ──────────────────────────────────────────────────────────────────
docs:
	@echo ""
	@echo "Documentation locations:"
	@echo "  Paper (SoftwareX draft): docs/paper/paper.md"
	@echo "  Data Availability:       DATA_AVAILABILITY.md"
	@echo "  Pipeline validation:     experiment/LunarAtlas_Ablation_Study_Guide.pdf"
	@echo "  Evaluation framework:    evaluation/evaluation_framework.md"
	@echo "  Downsampling rationale:  docs/what_and_why_downsampling.md"
	@echo "  Changelog:               CHANGELOG.md"
	@echo ""
