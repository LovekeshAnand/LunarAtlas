#!/usr/bin/env bash
# ==============================================================================
# LUNARATLAS MULTI-STAGE DATA PROCESSING PIPELINE ORCHESTRATOR
# Executes all 8 stages of raw spectroscopy data ingestion and validation.
# ==============================================================================

set -e # Exit immediately on error

# Resolve Python executable
if command -v python &> /dev/null; then
    PYTHON="python"
elif [ -f "../core/server/venv/Scripts/python.exe" ]; then
    PYTHON="../core/server/venv/Scripts/python.exe"
elif [ -f "../core/server/venv/Scripts/python" ]; then
    PYTHON="../core/server/venv/Scripts/python"
elif [ -f "../core/server/venv/bin/python" ]; then
    PYTHON="../core/server/venv/bin/python"
else
    echo "[ERROR] Python executable not found in PATH or virtual environment."
    exit 1
fi

echo "======================================================================"
# Show which python is being used
echo " Using Python: $PYTHON"
echo " LUNARATLAS DATA PROCESSING PIPELINE ORCHESTRATOR"
echo "======================================================================"
echo "This script runs the 8-stage PDS4 LIBS data pipeline in sequence."
echo "----------------------------------------------------------------------"

# Prompt for raw data input path
read -p "Enter raw ISRO files directory path [default: D:\ch3_libs\lib-v2\data\calibrated]: " RAW_DIR
RAW_DIR=${RAW_DIR:-"D:\ch3_libs\lib-v2\data\calibrated"}

# Prompt for processed output path
read -p "Enter processed datasets output path [default: ../datasets/processed]: " PROCESSED_DIR
PROCESSED_DIR=${PROCESSED_DIR:-"../datasets/processed"}

# Prompt for uploads directory (for Stage 6)
read -p "Enter raw uploads isolation path [default: ../datasets/uploads]: " UPLOADS_DIR
UPLOADS_DIR=${UPLOADS_DIR:-"../datasets/uploads"}

# Prompt for database ingestion option
read -p "Ingest processed datasets into the PostgreSQL database? (y/n) [default: y]: " INGEST_INPUT
INGEST_INPUT=${INGEST_INPUT:-y}

if [[ "$INGEST_INPUT" =~ ^[Yy]$ ]]; then
    INGEST="yes"
    INGEST_FLAG="y"

    # Collect database credentials directly (no .env dependency)
    echo ""
    echo "[INPUT REQUIRED] Enter PostgreSQL connection details:"
    read -p "  DB Host [default: localhost]: " DB_HOST
    DB_HOST=${DB_HOST:-"localhost"}
    
    read -p "  DB Port [default: 5432]: " DB_PORT
    DB_PORT=${DB_PORT:-"5432"}
    
    read -p "  DB Name [default: LunarAtlas]: " DB_NAME
    DB_NAME=${DB_NAME:-"LunarAtlas"}
    
    read -p "  DB User [default: postgres]: " DB_USER
    DB_USER=${DB_USER:-"postgres"}
    
    read -sp "  DB Password: " DB_PASS
    echo ""
    
    DB_URL="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
else
    INGEST="no"
    INGEST_FLAG="n"
    DB_URL=""
fi

echo ""
echo "----------------------------------------------------------------------"
echo " CONFIG SUMMARY"
echo "----------------------------------------------------------------------"
echo " Raw Data Input Path   : $RAW_DIR"
echo " Processed Output Path : $PROCESSED_DIR"
echo " Uploads Isolation Path: $UPLOADS_DIR"
echo " Ingest into Database  : $INGEST"
echo "----------------------------------------------------------------------"
echo ""
# Initialize JSON log
$PYTHON -c "import sys, pipeline_logger; pipeline_logger.init_log(sys.argv[1], sys.argv[2])" "$RAW_DIR" "$PROCESSED_DIR"

# Ensure log is copied on exit (success or failure)
trap 'mkdir -p "$PROCESSED_DIR" 2>/dev/null || true; cp pipeline_log.json "$PROCESSED_DIR/" 2>/dev/null || true' EXIT

# Stage 1: Folder Structure Study
$PYTHON step1_structure_study.py "$RAW_DIR"

# Stage 2: Process L1 Data
$PYTHON step2_process_l1_data.py "$RAW_DIR" "$PROCESSED_DIR"

# Stage 3: Graph Plotting
$PYTHON step3_graph_plotting.py "$PROCESSED_DIR"

# Stage 4: NIST Verification Logs
$PYTHON step4_nist_verification_logs.py "$PROCESSED_DIR"

# Stage 5: MD5 Digital Signatures
$PYTHON step5_md5_checksums.py "$PROCESSED_DIR"

# Stage 6: Creation of Segregated Data Folders
$PYTHON step6_segregate_data_folders.py "$INGEST_FLAG" "$RAW_DIR" "$PROCESSED_DIR" "$UPLOADS_DIR"

# Stage 7: Database Ingestion
if [ "$INGEST" == "yes" ]; then
    $PYTHON step7_db_ingestion.py "y" "$DB_URL" "$PROCESSED_DIR"
else
    $PYTHON step7_db_ingestion.py "n" "" "$PROCESSED_DIR"
fi

# Stage 8: Quantitative Data & Checksum Verification
if [ "$INGEST" == "yes" ]; then
    $PYTHON step8_data_verification.py "$PROCESSED_DIR" "$DB_URL"
else
    echo "======================================================================"
    echo " [STAGE 8: SKIPPED]"
    echo " Database verification skipped since DB ingestion was bypassed."
    echo "======================================================================"
fi

# Finalize JSON log
$PYTHON -c "import pipeline_logger; pipeline_logger.finalize_log()"

echo ""
echo "======================================================================"
echo " PIPELINE RUN SUCCESSFULLY COMPLETE"
echo " All generated files are in datasets/processed/"
echo " Check step-by-step logs and outputs for details."
echo "======================================================================"
