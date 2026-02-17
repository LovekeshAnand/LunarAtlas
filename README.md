# LunarAtlas  
A Provenance-Aware Lunar Scientific Data System  
(MVP Focus: Chandrayaan-3 LIBS)

---

## Overview

LunarAtlas is a structured and reproducible lunar mission data system designed to transform raw scientific datasets into analysis-ready, verifiable, and interactive formats while preserving full authenticity and PDS4 standards.

The current MVP focuses on Chandrayaan-3 LIBS (Laser Induced Breakdown Spectroscopy) calibrated Level-1 datasets.

This system does not claim to generate official Level-2 data products.  
Instead, it produces a structured, cleaned, and analysis-ready transformation of Level-1 calibrated data while preserving scientific traceability.

---

## Problem Statement

Planetary mission datasets are typically distributed as:

- PDS4-compliant XML labels
- Associated CSV data files
- Calibrated spectral intensity measurements
- Metadata-heavy scientific formats

While scientifically rigorous, these datasets are:

- Difficult to interpret programmatically
- Hard for students to explore interactively
- Not structured for reproducible querying
- Not easily verifiable against reference databases

LunarAtlas builds a reproducible system layer on top of existing datasets without modifying their scientific authenticity.

---

## Current MVP Scope (LIBS Only)

The MVP currently supports:

- Ingestion of LIBS Level-1 calibrated data
- Parsing of PDS4 XML labels
- Extraction of column definitions directly from XML
- Schema generation based on PDS4 standards
- Cleaning and normalization of spectral intensity data
- Structured transformation of Level-1 data into analysis-ready format
- Spectral plotting and peak identification
- Element verification using NIST Atomic Spectra Database references
- API endpoints for structured data access and spectral queries

Note:
The processed datasets are derived from Level-1 calibrated data.  
They are not official Level-2 products, but structured transformations designed for reproducible scientific analysis.

---

## Core Design Principles

### 1. PDS4 Standard Preservation

All metadata definitions, column names, units, and structural rules are derived directly from the PDS4 XML labels.

XML labels define:

- Column structure
- Data types
- Units
- Measurement context

These definitions are programmatically used to generate database schema structures.

Scientific authenticity is preserved at every stage.

---

### 2. Versioned and Origin-Aware Data Pipeline

Each dataset processed through LunarAtlas maintains:

- Source traceability
- Clear processing stage distinction (Original L1 → Processed form)
- Cleaned data isolation
- Reproducible transformation logic

This ensures transparency and scientific auditability.

---

### 3. Scientific API Layer

LunarAtlas provides structured API access for:

- Spectral data retrieval
- Element-based peak queries
- Processed dataset extraction
- Metadata inspection
- Instrument-level dataset exploration

The API is designed around scientific use cases, not generic CRUD operations.

---

## Data Flow Architecture (MVP)

1. PDS4 XML label is parsed.
2. Column definitions and metadata are extracted.
3. CSV data is validated against XML structure.
4. Cleaning and normalization is applied to calibrated intensity data.
5. Structured transformation is applied to produce analysis-ready dataset.
6. Database schema is generated from XML definitions.
7. Spectral peaks are plotted and verified against reference databases.
8. API endpoints expose structured and queryable scientific data.

---

## Technology Stack (Current)

- Python (data pipeline and processing)
- XML parsing (PDS4 labels)
- Pandas / NumPy (data cleaning and structuring)
- PostgreSQL (schema derived directly from XML definitions)
- Scientific plotting libraries
- NIST Atomic Spectra Database (reference verification)
- REST API layer for scientific queries

---

## Future Scope

LunarAtlas is designed to scale beyond LIBS.

Planned expansion includes:

- Support for additional Chandrayaan-3 instruments
- Multi-instrument dataset integration
- Cross-instrument comparative analysis
- Advanced spectral processing techniques
- Performance-optimized query architecture
- Expanded scientific API layer
- Interactive visualization and exploration interface

---

## Project Status

MVP in active development.

Current milestone:

- Cleaned LIBS Level-1 calibrated datasets
- Structured analysis-ready transformation layer
- Preserved PDS4 compliance
- Spectral verification against reference data
- API development in progress

---

## Vision

LunarAtlas aims to provide a reproducible, structured, and scientifically authentic data system for lunar mission datasets — enabling researchers, students, and developers to explore mission data without compromising its original integrity.
