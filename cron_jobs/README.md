# LunarAtlas Cron Jobs Deployment Guide

These automation scripts are designed to run on a separate server (like your EC2 instance) to keep your free cloud resources alive and manage daily database backups.

---

## 1. Directory Structure

Copy the `cron_jobs` folder to your EC2 instance:
```
cron_jobs/
├── .env.example
├── README.md
├── backup.sh
├── keep_alive.py
└── requirements.txt
```

---

## 2. Server Prerequisites

On your EC2 instance (Ubuntu/Debian), install PostgreSQL client utilities and Python dependencies:

```bash
# Update package list and install postgres-client for backups
sudo apt update
sudo apt install -y postgresql-client python3-pip python3-venv

# Setup a dedicated virtual environment
cd /path/to/cron_jobs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Configuration

1. Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your Supabase connection string, Render Redis URL, and Render Backend URL:
   ```env
   DATABASE_URL=postgresql://postgres.ljlgxaigoiqedgmkaukw:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
   REDIS_URL=redis://red-xxxxxxxxxxxx.oregon-redis.render.com:6379
   HEALTH_CHECK_URL=https://lunaratlas-backend.onrender.com/api/v1/health
   ```

---

## 4. Setting Up Crontab

Open the system cron table editor:
```bash
crontab -e
```

Add the following lines at the bottom (make sure to update `/path/to/cron_jobs` with the absolute path of the directory on your EC2 instance):

```cron
# 1. Keep Alive (Runs every 10 minutes)
# Keeps the Render free Web Service awake and prevents Supabase/Redis from spinning down.
*/10 * * * * cd /path/to/cron_jobs && ./venv/bin/python keep_alive.py >> keep_alive.log 2>&1

# 2. Daily Database Backup (Runs every day at 2:00 AM)
0 2 * * * cd /path/to/cron_jobs && export $(cat .env | xargs) && bash backup.sh >> backup.log 2>&1
```

---

## 5. Script Details

### Keep Alive (`keep_alive.py`)
Pings:
* **Database**: Runs `SELECT 1` on Supabase to keep the database active.
* **Redis**: Runs a PING command on Render Redis to prevent connection timeout.
* **Health Check**: Hits your Render web app health endpoint. This keeps the free Render backend instance awake 24/7 (preventing the 30-second cold-start delay).

### Daily Backup (`backup.sh`)
* Uses `pg_dump` to extract the full database schema and data.
* Compresses the backup into a `.sql.gz` file.
* If `S3_BUCKET_NAME` is set in the environment, it automatically uploads the compressed backup to AWS S3.
