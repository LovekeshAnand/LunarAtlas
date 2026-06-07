# ==============================================================================
# 🌙 LUNARATLAS MULTI-STAGE DATA PROCESSING PIPELINE ORCHESTRATOR (POWERSHELL)
# Executes all 8 stages of raw spectroscopy data ingestion and validation on Windows.
# ==============================================================================

Clear-Host

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " 🌙 LUNARATLAS DATA PROCESSING PIPELINE ORCHESTRATOR" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "This script runs the 8-stage PDS4 LIBS data pipeline in sequence."
Write-Host "----------------------------------------------------------------------"

# Prompt for database ingestion option
$ingestInput = Read-Host "Ingest processed datasets into the PostgreSQL database? (y/n) [default: y]"
if ([string]::IsNullOrWhiteSpace($ingestInput)) {
    $ingestInput = "y"
}

if ($ingestInput.ToLower() -eq "y" -or $ingestInput.ToLower() -eq "yes") {
    $ingest = "yes"
    $ingestFlag = "y"
} else {
    $ingest = "no"
    $ingestFlag = "n"
}

Write-Host ""
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " CONFIG SUMMARY" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " Raw Data Input Path   : D:\ch3_libs\lib-v2\data\calibrated"
Write-Host " Processed Output Path : c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"
Write-Host " Ingest into Database  : $ingest"
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# Helper to run python script and check status
function Run-Step($script, $argsList) {
    Write-Host "[RUNNING] python $script $argsList" -ForegroundColor Yellow
    if ($argsList) {
        python $script $argsList
    } else {
        python $script
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Script $script failed with exit code $LASTEXITCODE" -ForegroundColor Red
        Exit $LASTEXITCODE
    }
}

# Stage 1: Folder Structure Study
Run-Step "step1_structure_study.py"

# Stage 2: Process L1 Data
Run-Step "step2_process_l1_data.py"

# Stage 3: Graph Plotting
Run-Step "step3_graph_plotting.py"

# Stage 4: NIST Verification Logs
Run-Step "step4_nist_verification_logs.py"

# Stage 5: MD5 Digital Signatures
Run-Step "step5_md5_checksums.py"

# Stage 6: Creation of Segregated Data Folders
Run-Step "step6_segregate_data_folders.py" $ingestFlag

# Stage 7: Database Ingestion
Run-Step "step7_db_ingestion.py" $ingestFlag

# Stage 8: Quantitative Data & Checksum Verification
if ($ingest -eq "yes") {
    Run-Step "step8_data_verification.py"
} else {
    Write-Host "======================================================================" -ForegroundColor Yellow
    Write-Host " [STAGE 8: SKIPPED]" -ForegroundColor Yellow
    Write-Host " Database verification skipped since DB ingestion was bypassed." -ForegroundColor Yellow
    Write-Host "======================================================================" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " [SUCCESS] PIPELINE RUN SUCCESSFULLY COMPLETE" -ForegroundColor Green
Write-Host " All generated files are in datasets/processed/" -ForegroundColor Green
Write-Host " Check step-by-step logs and outputs for details." -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
