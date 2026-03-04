#!/usr/bin/env python3
"""
✂  BarberShop Manager – Startup Script
Run this file to start the server.
Workers can connect from phones on the same WiFi.
"""
import subprocess, sys, socket, os

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

def ensure_virtualenv():
    """Create and activate a virtualenv in the project directory.
    Returns the path to the python executable inside the venv."""
    venv_dir = os.path.join(os.getcwd(), 'venv')
    if not os.path.isdir(venv_dir):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True)
    python_bin = os.path.join(venv_dir, 'bin', 'python')
    return python_bin


def install_requirements(python_exe):
    """Install packages from requirements.txt into given python."""
    print("Installing/upgrading requirements...")
    subprocess.run([python_exe, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([python_exe, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)

if __name__ == "__main__":
    # make sure we're in project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # prepare virtualenv and dependencies
    py = ensure_virtualenv()
    install_requirements(py)

    ip = get_local_ip()
    print("""
╔══════════════════════════════════════════════╗
║       ✂  BarberShop Manager v1.0            ║
╠══════════════════════════════════════════════╣
║                                              ║
║  Server is running!                          ║
║                                              ║""")
    print(f"║  PC Access:    http://localhost:5000         ║")
    print(f"║  Mobile/WiFi:  http://{ip}:5000{' '*(20-len(ip))}║")
    print("""║                                              ║
║  Default Admin PIN: 1234                     ║
║  Change it in Settings after first login     ║
║                                              ║
║  Press CTRL+C to stop the server             ║
╚══════════════════════════════════════════════╝
""")

    # if gunicorn is available we use it for a simple production startup
    try:
        import gunicorn
        print('Starting with gunicorn...')
        # use gunicorn from venv bin
        gunicorn_bin = os.path.join(os.path.dirname(py), 'gunicorn')
        os.execv(gunicorn_bin, [gunicorn_bin, '-w', '4', '-b', '0.0.0.0:5000', 'app:app'])
    except ImportError:
        # fallback to builtin server
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
