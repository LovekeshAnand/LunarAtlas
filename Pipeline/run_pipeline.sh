#!/usr/bin/env bash
# ==============================================================================
# LUNARATLAS MULTI-STAGE DATA PROCESSING PIPELINE ORCHESTRATOR
# Executes all 8 stages of raw spectroscopy data ingestion and validation.
# ==============================================================================

set -e # Exit immediately on error

echo "======================================================================"
echo " LUNARATLAS DATA PROCESSING PIPELINE ORCHESTRATOR"
echo "======================================================================"
echo "This script runs the 8-stage PDS4 LIBS data pipeline in sequence."
echo "----------------------------------------------------------------------"

# Prompt for database ingestion option
read -p "Ingest processed datasets into the PostgreSQL database? (y/n) [default: y]: " INGEST_INPUT
INGEST_INPUT=${INGEST_INPUT:-y}

if [[ "$INGEST_INPUT" =~ ^[Yy]$ ]]; then
    INGEST="yes"
    INGEST_FLAG="y"
else
    INGEST="no"
    INGEST_FLAG="n"
fi

echo ""
echo "----------------------------------------------------------------------"
echo " CONFIG SUMMARY"
echo "----------------------------------------------------------------------"
echo " Raw Data Input Path   : D:\ch3_libs\lib-v2\data\calibrated"
echo " Processed Output Path : c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"
echo " Ingest into Database  : $INGEST"
echo "----------------------------------------------------------------------"
echo ""

# Stage 1: Folder Structure Study
python step1_structure_study.py

# Stage 2: Process L1 Data
python step2_process_l1_data.py

# Stage 3: Graph Plotting
python step3_graph_plotting.py

# Stage 4: NIST Verification Logs
python step4_nist_verification_logs.py

# Stage 5: MD5 Digital Signatures
python step5_md5_checksums.py

# Stage 6: Creation of Segregated Data Folders
python step6_segregate_data_folders.py "$INGEST_FLAG"

# Stage 7: Database Ingestion
if [ "$INGEST" == "yes" ]; then
    python step7_db_ingestion.py "y"
else
    python step7_db_ingestion.py "n"
fi

# Stage 8: Quantitative Data & Checksum Verification
if [ "$INGEST" == "yes" ]; then
    python step8_data_verification.py
else
    echo "======================================================================"
    echo " [STAGE 8: SKIPPED]"
    echo " Database verification skipped since DB ingestion was bypassed."
    echo "======================================================================"
fi

echo ""
echo "======================================================================"
echo " ✓ PIPELINE RUN SUCCESSFULLY COMPLETE"
echo " All generated files are in datasets/processed/"
echo " Check step-by-step logs and outputs for details."
echo "======================================================================"
