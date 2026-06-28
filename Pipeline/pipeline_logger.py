import os
import re
import time
import json
from datetime import datetime

LOG_FILE = "pipeline_log.json"
DEFAULT_RAW = r"D:\ch3_libs\lib-v2\data\calibrated"
DEFAULT_PROCESSED = "../datasets/processed"

def _read_log():
    if not os.path.exists(LOG_FILE):
        return None
        
    for attempt in range(5):
        try:
            with open(LOG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < 4:
                time.sleep(0.05)
                continue
            # Attempt regex recovery of directories if JSON parsing completely fails after retries
            print(f"[WARNING] Log file {LOG_FILE} is malformed ({e}). Recovering paths...")
            raw_dir = DEFAULT_RAW
            processed_dir = DEFAULT_PROCESSED
            timestamp = datetime.now().isoformat()
            try:
                with open(LOG_FILE, "r") as rf:
                    content = rf.read()
                raw_match = re.search(r'"raw_dir"\s*:\s*"([^"]+)"', content)
                if raw_match: raw_dir = raw_match.group(1)
                proc_match = re.search(r'"processed_dir"\s*:\s*"([^"]+)"', content)
                if proc_match: processed_dir = proc_match.group(1)
                ts_match = re.search(r'"timestamp"\s*:\s*"([^"]+)"', content)
                if ts_match: timestamp = ts_match.group(1)
            except Exception:
                pass
            return {
                "timestamp": timestamp,
                "overall_status": "in_progress",
                "raw_dir": raw_dir,
                "processed_dir": processed_dir,
                "stages": {}
            }
        except IOError as e:
            if attempt < 4:
                time.sleep(0.05)
                continue
            print(f"[WARNING] Log file {LOG_FILE} is locked ({e}). Re-initializing fallback structure.")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "in_progress",
                "raw_dir": DEFAULT_RAW,
                "processed_dir": DEFAULT_PROCESSED,
                "stages": {}
            }

def _write_log(log_data):
    temp_file = LOG_FILE + ".tmp"
    try:
        with open(temp_file, "w") as f:
            json.dump(log_data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # os.replace handles atomic overwrite on both Windows and POSIX systems
        os.replace(temp_file, LOG_FILE)
    except Exception as e:
        print(f"[WARNING] Atomic write failed for {LOG_FILE}: {e}")
        try:
            with open(LOG_FILE, "w") as f:
                json.dump(log_data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
        except Exception as fe:
            print(f"[ERROR] Direct write fallback failed: {fe}")

def init_log(raw_dir, processed_dir):
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "in_progress",
        "raw_dir": raw_dir or DEFAULT_RAW,
        "processed_dir": processed_dir or DEFAULT_PROCESSED,
        "stages": {}
    }
    _write_log(log_data)

def log_stage_success(stage_key, stage_name, metrics=None):
    try:
        log_data = _read_log()
        if log_data is None:
            # Initialize on the fly if not initialized
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "in_progress",
                "raw_dir": DEFAULT_RAW,
                "processed_dir": DEFAULT_PROCESSED,
                "stages": {}
            }
        
        log_data["stages"][stage_key] = {
            "name": stage_name,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics or {}
        }
        _write_log(log_data)
    except Exception as e:
        print(f"[WARNING] Logger failed to record success for {stage_name}: {e}")

def log_stage_failure(stage_key, stage_name, error_msg, metrics=None):
    try:
        log_data = _read_log()
        if log_data is None:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "in_progress",
                "raw_dir": DEFAULT_RAW,
                "processed_dir": DEFAULT_PROCESSED,
                "stages": {}
            }
        
        log_data["stages"][stage_key] = {
            "name": stage_name,
            "status": "failed",
            "timestamp": datetime.now().isoformat(),
            "error": error_msg,
            "metrics": metrics or {}
        }
        log_data["overall_status"] = "failed"
        log_data["finished_at"] = datetime.now().isoformat()
        _write_log(log_data)
    except Exception as e:
        print(f"[WARNING] Logger failed to record failure for {stage_name}: {e}")

def finalize_log(status="success"):
    try:
        log_data = _read_log()
        if log_data is None:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "in_progress",
                "raw_dir": DEFAULT_RAW,
                "processed_dir": DEFAULT_PROCESSED,
                "stages": {}
            }
        
        any_failed = any(stage.get("status") == "failed" for stage in log_data["stages"].values())
        log_data["overall_status"] = "failed" if any_failed else status
        log_data["finished_at"] = datetime.now().isoformat()
        _write_log(log_data)
    except Exception as e:
        print(f"[WARNING] Logger failed to finalize log: {e}")

