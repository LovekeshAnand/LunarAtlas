# Contributing to LunarAtlas

Thank you for your interest in contributing to LunarAtlas!
This document explains how to report bugs, suggest improvements, and submit code.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Report a Bug](#how-to-report-a-bug)
3. [How to Suggest a Feature](#how-to-suggest-a-feature)
4. [Development Setup](#development-setup)
5. [Running the Tests](#running-the-tests)
6. [Submitting a Pull Request](#submitting-a-pull-request)
7. [Style Guide](#style-guide)

---

## Code of Conduct

This project is governed by the
[Contributor Covenant Code of Conduct v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
By participating, you agree to uphold this code.

---

## How to Report a Bug

1. Check the [open issues](https://github.com/[YOUR-GITHUB-USERNAME]/LunarAtlas/issues)
   to make sure the bug has not already been reported.
2. Open a new issue using the **Bug Report** template.
3. Include:
   - Python version and OS
   - The exact command you ran
   - The full error traceback
   - A minimal example CSV file if the bug is in the pipeline

---

## How to Suggest a Feature

1. Open a new issue using the **Feature Request** template.
2. Describe the scientific use case that motivates the feature.
3. If the feature affects the pipeline output format, note how it interacts
   with the database schema and the API response format.

---

## Development Setup

### Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.10 |
| Node.js | 18.0 |
| PostgreSQL | 14.0 |
| Redis | 6.0 |

### Step 1 — Clone and create environment

```bash
git clone https://github.com/[YOUR-GITHUB-USERNAME]/LunarAtlas.git
cd LunarAtlas

# Create a Python virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate          # Windows PowerShell

# Install all dependencies
pip install -r requirements.txt
```

### Step 2 — Configure the server

```bash
# Copy the template and fill in your database credentials
cp core/server/env.template core/server/.env
```

Edit `core/server/.env` with your PostgreSQL and Redis connection strings.

### Step 3 — Install the frontend

```bash
cd core/client
npm install
```

---

## Running the Tests

The test suite uses `pytest` and requires no database connection (all tests
use synthetic data).

```bash
# From the repository root:
pip install pytest

# Run all tests
pytest tests/ -v

# Run only the algorithm unit tests
pytest tests/test_lttb_algorithm.py -v

# Run only the pipeline unit tests
pytest tests/test_pipeline_processing.py -v
```

All tests must pass before submitting a pull request.

---

## Submitting a Pull Request

1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/my-feature-name
   ```

2. Make your changes. Follow the Style Guide below.

3. Add or update tests in `tests/` to cover your changes.

4. Ensure all tests pass: `pytest tests/ -v`

5. Update `CHANGELOG.md` under the `[Unreleased]` section.

6. Open a Pull Request against the `main` branch. In the PR description:
   - Explain **what** you changed and **why**
   - Link any related issues

---

## Style Guide

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all function signatures
- Include NumPy-style docstrings for all public functions
- Maximum line length: 100 characters

### TypeScript / React

- Follow the existing ESLint configuration (`core/client/eslint.config.js`)
- Use functional components with hooks only (no class components)
- Keep Web Worker message interfaces typed with explicit interfaces

### Pipeline Scripts

- Every pipeline step must print a `[SUCCESS]` or `[ERROR]` line to stdout
- Every pipeline step must be independently runnable from the command line:
  ```bash
  python Pipeline/stepN_name.py [optional_args]
  ```
- Do not add interactive `input()` calls to any pipeline step

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(pipeline): add SHA-256 alternative to MD5 manifest
fix(api): correct wavelength range filtering in /spectrum endpoint
docs(readme): update quick-start commands for Windows
test(lttb): add edge-case test for threshold=3
```

---

## Questions?

Open a [discussion](https://github.com/[YOUR-GITHUB-USERNAME]/LunarAtlas/discussions)
or email the corresponding author (see [`CITATION.cff`](CITATION.cff)).
