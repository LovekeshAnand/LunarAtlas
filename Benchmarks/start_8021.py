import subprocess, sys

with open("server_8021.log", "w") as log:
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8021"],
        stdout=log, stderr=log,
        cwd=r"d:\LunarAtlas\core\server"
    )
    print(f"PID: {proc.pid}")
    proc.wait()
