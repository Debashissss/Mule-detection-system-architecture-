"""
PS-01: MuleGuard Platform Master Controller & Service Launcher
Coordinates:
1. Python Data Science & ML Engine (Port 8000)
2. C# .NET 8 Bank Gateway Service (Port 5000)
"""

import os
import sys
import time
import subprocess
import urllib.request
import json

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
DOTNET_EXE = os.path.expandvars(r"%USERPROFILE%\.dotnet\dotnet.exe")

def check_service_health(url, timeout=2):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MuleGuard-Monitor"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode())
    except Exception:
        return None
    return None

def main():
    print("=" * 80)
    print("      MULEGUARD: INTELLIGENT MULE ACCOUNT DETECTION & INVESTIGATION PLATFORM")
    print("      Technology Stack: Python Data Science Engine + C# .NET 8 Bank Gateway")
    print("=" * 80)

    # 1. Run C# Integration Tests
    print("\n>>> STEP 1: Running C# .NET 8 Integration & Security Suite...")
    res = subprocess.run([DOTNET_EXE, "run", "--project", os.path.join(ROOT_DIR, "csharp_gateway", "BankGateway.csproj"), "--no-build", "--", "--run-tests"], cwd=ROOT_DIR)
    if res.returncode != 0:
        print("[!] Rebuilding C# project...")
        subprocess.run([DOTNET_EXE, "build", os.path.join(ROOT_DIR, "csharp_gateway", "BankGateway.csproj")], cwd=ROOT_DIR)

    # 2. Launch Python Engine
    print("\n>>> STEP 2: Launching Python Data Science & ML Engine (Port 8000)...")
    python_proc = subprocess.Popen(
        [PYTHON_EXE, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.path.join(ROOT_DIR, "python_engine"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 3. Launch C# Bank Gateway
    print(">>> STEP 3: Launching C# ASP.NET Core 8 Bank Gateway (Port 5000)...")
    csharp_proc = subprocess.Popen(
        [DOTNET_EXE, "run", "--project", os.path.join(ROOT_DIR, "csharp_gateway", "BankGateway.csproj"), "--no-build"],
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for services to initialize
    print("\nWaiting for microservices to initialize...")
    for _ in range(15):
        time.sleep(1)
        py_health = check_service_health("http://127.0.0.1:8000/health")
        cs_health = check_service_health("http://127.0.0.1:5000/api/bank/health")
        if py_health and cs_health:
            print("\n[SUCCESS] Both Microservices are ONLINE and Communicating!")
            print(f"  • Python ML Engine : http://127.0.0.1:8000 (FastAPI Docs: http://127.0.0.1:8000/docs)")
            print(f"  • C# Bank Gateway  : http://127.0.0.1:5000 (Swagger: http://127.0.0.1:5000/swagger)")
            break
    else:
        print("[*] Services launched in background.")

    print("\nPress Ctrl+C to stop both backend services.")
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping services...")
        python_proc.terminate()
        csharp_proc.terminate()
        print("MuleGuard services safely stopped.")

if __name__ == "__main__":
    main()
