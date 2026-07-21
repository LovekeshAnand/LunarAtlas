import os, subprocess, sys

env = os.environ.copy()
env["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/LunarAtlas"

with open("server_8020.log", "w") as log:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8020"],
        env=env,
        stdout=log, stderr=log,
        cwd=r"d:\LunarAtlas\core\server"
    )
    print(f"PID: {proc.pid}")
    proc.wait()
