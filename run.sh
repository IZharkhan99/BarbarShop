#!/usr/bin/env bash
# ✂ BarberShop Manager helper script
# Bootstraps environment and runs the application in either development or production mode.
# Usage:
#   ./run.sh            # production (gunicorn)
#   ./run.sh dev        # development (flask builtin, debug enabled)
#   ./run.sh help       # show this message

set -e

usage() {
    grep '^#' "$0" | sed 's/^#//'
    exit 1
}

if [[ "$1" == "help" ]]; then
    usage
fi

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$PROJECT_ROOT"

# prepare venv
if [[ ! -d venv ]]; then
    echo "Creating virtualenv..."
    python3 -m venv venv
fi
source venv/bin/activate

# install requirements
pip install --upgrade pip
pip install -r requirements.txt

export FLASK_APP=app.py

if [[ "$1" == "dev" ]]; then
    export FLASK_ENV=development
    echo "Starting in development mode (debug)..."
    flask run --host=0.0.0.0 --port=5000
else
    export FLASK_ENV=production
    if command -v gunicorn >/dev/null 2>&1; then
        echo "Starting in production mode with gunicorn..."
        gunicorn -w 4 -b 0.0.0.0:5000 app:app
    else
        echo "Gunicorn not found, using Flask builtin server (not for production)."
        flask run --host=0.0.0.0 --port=5000
    fi
fi
