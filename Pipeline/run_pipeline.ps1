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

# Prompt for raw data input path
$rawDir = Read-Host "Enter raw ISRO files directory path [default: D:\ch3_libs\lib-v2\data\calibrated]"
if ([string]::IsNullOrWhiteSpace($rawDir)) {
    $rawDir = "D:\ch3_libs\lib-v2\data\calibrated"
}

# Prompt for processed output path
$processedDir = Read-Host "Enter processed datasets output path [default: ..\datasets\processed]"
if ([string]::IsNullOrWhiteSpace($processedDir)) {
    $processedDir = "..\datasets\processed"
}

# Prompt for uploads directory (for Stage 6)
$uploadsDir = Read-Host "Enter raw uploads isolation path [default: ..\datasets\uploads]"
if ([string]::IsNullOrWhiteSpace($uploadsDir)) {
    $uploadsDir = "..\datasets\uploads"
}

# Prompt for database ingestion option
$ingestInput = Read-Host "Ingest processed datasets into the PostgreSQL database? (y/n) [default: y]"
if ([string]::IsNullOrWhiteSpace($ingestInput)) {
    $ingestInput = "y"
}

if ($ingestInput.ToLower() -eq "y" -or $ingestInput.ToLower() -eq "yes") {
    $ingest = "yes"
    $ingestFlag = "y"

    # Collect database credentials directly (no .env dependency)
    Write-Host ""
    Write-Host "[INPUT REQUIRED] Enter PostgreSQL connection details:" -ForegroundColor Cyan
    
    $dbHost = Read-Host "  DB Host [default: localhost]"
    if ([string]::IsNullOrWhiteSpace($dbHost)) { $dbHost = "localhost" }
    
    $dbPort = Read-Host "  DB Port [default: 5432]"
    if ([string]::IsNullOrWhiteSpace($dbPort)) { $dbPort = "5432" }
    
    $dbName = Read-Host "  DB Name [default: LunarAtlas]"
    if ([string]::IsNullOrWhiteSpace($dbName)) { $dbName = "LunarAtlas" }
    
    $dbUser = Read-Host "  DB User [default: postgres]"
    if ([string]::IsNullOrWhiteSpace($dbUser)) { $dbUser = "postgres" }
    
    $dbPass = Read-Host "  DB Password" -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPass)
    $dbPassPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    
    $dbUrl = "postgresql://${dbUser}:${dbPassPlain}@${dbHost}:${dbPort}/${dbName}"
} else {
    $ingest = "no"
    $ingestFlag = "n"
    $dbUrl = ""
}

Write-Host ""
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " CONFIG SUMMARY" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " Raw Data Input Path   : $rawDir"
Write-Host " Processed Output Path : $processedDir"
Write-Host " Uploads Isolation Path: $uploadsDir"
Write-Host " Ingest into Database  : $ingest"
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# Helper to run python script and check status
function Run-Step {
    param([string]$script, [string[]]$argsList)
    Write-Host "[RUNNING] python $script $($argsList -join ' ')" -ForegroundColor Yellow
    if ($argsList.Count -gt 0) {
        python $script @argsList
    } else {
        python $script
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Script $script failed with exit code $LASTEXITCODE" -ForegroundColor Red
        Exit $LASTEXITCODE
    }
}

try {
    # Initialize JSON log
    python -c "import sys, pipeline_logger; pipeline_logger.init_log(sys.argv[1], sys.argv[2])" "$rawDir" "$processedDir"

    # Stage 1: Folder Structure Study
    Run-Step "step1_structure_study.py" -argsList @($rawDir)

    # Stage 2: Process L1 Data
    Run-Step "step2_process_l1_data.py" -argsList @($rawDir, $processedDir)

    # Stage 3: Graph Plotting
    Run-Step "step3_graph_plotting.py" -argsList @($processedDir)

    # Stage 4: NIST Verification Logs
    Run-Step "step4_nist_verification_logs.py" -argsList @($processedDir)

    # Stage 5: MD5 Digital Signatures
    Run-Step "step5_md5_checksums.py" -argsList @($processedDir)

    # Stage 6: Creation of Segregated Data Folders
    Run-Step "step6_segregate_data_folders.py" -argsList @($ingestFlag, $rawDir, $processedDir, $uploadsDir)

    # Stage 7: Database Ingestion
    Run-Step "step7_db_ingestion.py" -argsList @($ingestFlag, $dbUrl, $processedDir)

    # Stage 8: Quantitative Data & Checksum Verification
    if ($ingest -eq "yes") {
        Run-Step "step8_data_verification.py" -argsList @($processedDir, $dbUrl)
    } else {
        Write-Host "======================================================================" -ForegroundColor Yellow
        Write-Host " [STAGE 8: SKIPPED]" -ForegroundColor Yellow
        Write-Host " Database verification skipped since DB ingestion was bypassed." -ForegroundColor Yellow
        Write-Host "======================================================================" -ForegroundColor Yellow
    }

    # Finalize JSON log
    python -c "import pipeline_logger; pipeline_logger.finalize_log()"

    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host " [SUCCESS] PIPELINE RUN SUCCESSFULLY COMPLETE" -ForegroundColor Green
    Write-Host " All generated files are in datasets/processed/" -ForegroundColor Green
    Write-Host " Check step-by-step logs and outputs for details." -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Green
} finally {
    if (Test-Path "pipeline_log.json") {
        if (!(Test-Path $processedDir)) {
            New-Item -ItemType Directory -Force -Path $processedDir -ErrorAction SilentlyContinue | Out-Null
        }
        Copy-Item -Path "pipeline_log.json" -Destination $processedDir -Force -ErrorAction SilentlyContinue
    }
}
