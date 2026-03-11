#!/usr/bin/env python3
"""
BarberShop Manager - Professional Launcher
This script detects your network IP and starts the management server.
Workers can connect by visiting the IP shown below on their phones.
"""

import subprocess
import sys
import socket
import os
import platform
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def print_header():
    ip = get_local_ip()
    port = "5000"
    
    print("\033[91m") # Red
    print(r"""
    ---------------------------------------------------------
    |   BARBERSHOP MANAGER PRO - SERVER CONSOLE             |
    ---------------------------------------------------------
    """)
    print("\033[0m") # Reset
    print(f"    {'='*56}")
    print(f"    SYSTEM STATUS: \033[92mONLINE\033[0m")
    print(f"    PLATFORM:      {platform.system()} {platform.release()}")
    print(f"    LOCAL IP:      \033[93m{ip}\033[0m")
    print(f"    DASHBOARD:     \033[94mhttp://{ip}:{port}\033[0m")
    print(f"    ADMIN PANEL:   \033[94mhttp://localhost:{port}/admin\033[0m")
    print(f"    {'='*56}")
    print("\n    \033[90mPress Ctrl+C to stop the server\033[0m\n")

def run_app():
    # Detect the correct python executable
    if os.path.exists('venv/bin/python'):
        py_path = 'venv/bin/python'
    elif os.path.exists('venv/Scripts/python.exe'):
        py_path = 'venv/Scripts/python.exe'
    else:
        py_path = sys.executable # Fallback to current python
        
    try:
        # Check if requirements are installed (simple check)
        subprocess.run([py_path, "-c", "import flask"], check=True, capture_output=True)
    except:
        print("    \033[91m[!] Dependencies not found. Installing...\033[0m")
        subprocess.run([py_path, "-m", "pip", "install", "-r", "requirements.txt"])

    clear_screen()
    print_header()
    
    try:
        # Start the Flask app (assuming app.py or start.py is the entry)
        # If start.py is used, we just run that, but better to run the app directly
        # if start.py starts the app.
        env = os.environ.copy()
        env["FLASK_APP"] = "app.py" # Assuming app.py is the main file
        subprocess.run([py_path, "app.py"], env=env)
    except KeyboardInterrupt:
        print("\n    \033[93m[!] Server stopped by user.\033[0m")
    except Exception as e:
        print(f"\n    \033[91m[!] Error: {e}\033[0m")

if __name__ == "__main__":
    run_app()
