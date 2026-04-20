# LunarAtlas Backend Development Guide
## For Windows Local Development

**Version:** 1.0  
**Target OS:** Windows 10/11  
**Goal:** Build and test the complete backend locally before VM deployment

---

## 1. Prerequisites & Installation

### 1.1 Install PostgreSQL 16 on Windows
1. Download from: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
2. Port: `5432`
3. Add `C:\Program Files\PostgreSQL\16\bin` to PATH.
4. Create the database: `CREATE DATABASE LunarAtlas;`

### 1.2 Install Redis on Windows
**Option A: WSL2 + Redis (Recommended)**
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Redis Configuration (`/etc/redis/redis.conf`):**
```ini
# Memory
maxmemory 4gb
maxmemory-policy allkeys-lru

# Network
bind 127.0.0.1
port 6379

# Performance
tcp-backlog 511
timeout 0

# Disable persistence for cache-only mode (faster)
save ""
appendonly no
```
*Restart redis: `sudo service redis-server restart`*

**Option B: Memurai**
1. Download from: https://www.memurai.com/get-memurai
2. Apply similar config in `memurai.conf`.

### 1.3 Install Python 3.11
1. Download from: https://www.python.org/downloads/
2. Ensure "Add Python to PATH" is checked.

---

## 2. Environment Setup

### 2.1 Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2 Database Configuration
The backend uses `.env` for database credentials. Ensure `DATABASE_URL` matches your local setup:
```env
DATABASE_URL=postgresql://lunaratlas_user:summertimesadness101@localhost:5432/LunarAtlas
REDIS_URL=redis://localhost:6379/0
```

---

## 3. Automated Setup (New Environment)

If you are setting up on a fresh Ubuntu VM, you can use the automated setup script.

1. **Navigate to the server directory**:
   ```bash
   cd server
   ```
2. **Run the setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
This will recreate the entire project structure and write all code files automatically.

---

## 4. Database Initialization

### 3.1 Create Schema
```powershell
psql -U postgres -d LunarAtlas -f configs/schema.sql
```

### 3.2 Insert Test Data
```powershell
python scripts/insert_test_data.py
```

---

## 5. Running the API

From the `core/server` directory:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*Note: Ensure you are in the directory containing the `app` folder.*

Access Interactive Documentation at: http://localhost:8000/docs

---

## 6. Verification
Run the following tests to verify implementation:
```powershell
# Downsampling algorithm test
python tests/test_downsampling.py

# API performance test (requires running server)
python tests/performance_test.py
```
