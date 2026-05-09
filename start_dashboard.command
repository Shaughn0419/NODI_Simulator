#!/bin/bash
# ============================================================
# NODI Interferometric Simulator — Dashboard Launcher (macOS)
# ============================================================
# Double-click this file to start the dashboard.
# Browser will auto-open at the first available port (starting from 8501)
# Press Ctrl+C in terminal to stop.
# ============================================================

# Navigate to project root (where this script lives)
cd "$(dirname "$0")"

echo "============================================"
echo "  NODI Interferometric Simulator Dashboard"
echo "============================================"
echo ""

# --- Find Python with streamlit installed ---
# Priority: homebrew python@3.13 > python3 > python
PYTHON=""

# Try homebrew python first (most likely to have packages)
if [ -x "/opt/homebrew/opt/python@3.13/libexec/bin/python" ]; then
    CANDIDATE="/opt/homebrew/opt/python@3.13/libexec/bin/python"
    if $CANDIDATE -c "import streamlit" 2>/dev/null; then
        PYTHON="$CANDIDATE"
    fi
fi

# Try python3 on PATH
if [ -z "$PYTHON" ] && command -v python3 &>/dev/null; then
    CANDIDATE="python3"
    if $CANDIDATE -c "import streamlit" 2>/dev/null; then
        PYTHON="$CANDIDATE"
    fi
fi

# Try python on PATH
if [ -z "$PYTHON" ] && command -v python &>/dev/null; then
    CANDIDATE="python"
    if $CANDIDATE -c "import streamlit" 2>/dev/null; then
        PYTHON="$CANDIDATE"
    fi
fi

# No python with streamlit found — try to install
if [ -z "$PYTHON" ]; then
    # Pick the best available python
    if [ -x "/opt/homebrew/opt/python@3.13/libexec/bin/python" ]; then
        PYTHON="/opt/homebrew/opt/python@3.13/libexec/bin/python"
    elif command -v python3 &>/dev/null; then
        PYTHON="python3"
    elif command -v python &>/dev/null; then
        PYTHON="python"
    else
        echo "[ERROR] Python not found."
        echo "Please install Python 3.10+ from https://www.python.org"
        echo ""
        read -p "Press Enter to exit..."
        exit 1
    fi

    echo "[INFO] Streamlit not found. Installing dependencies..."
    echo "  Using: $($PYTHON --version 2>&1)"
    echo ""
    $PYTHON -m pip install streamlit plotly numpy scipy pandas
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] Failed to install dependencies."
        echo "Please run:  $PYTHON -m pip install streamlit plotly numpy scipy pandas"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "Using Python: $($PYTHON --version 2>&1)"
echo "  Path: $(which $PYTHON 2>/dev/null || echo $PYTHON)"

# --- Set PYTHONPATH so nodi_simulator is importable from this project root ---
export PYTHONPATH="$(pwd):$PYTHONPATH"

# --- Report current dataset status without auto-running legacy precompute ---
CURRENT_STANDARD_DATASET="results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
CURRENT_STANDARD_PRECOMPUTE_CMD="$PYTHON -m nodi_simulator.dashboard.precompute --grid ev_design --particle-profile full_range_biomimetic_exosome_with_anchors --tag full_range_biomimetic_exosome_with_anchors_10000e --workers 8 --freeze-probe-report --artifact-profile standard --progress-interval 2 --resume --checkpoint --checkpoint-batch-size 100 --checkpoint-flush-interval 5 --output results/"

echo ""
if [ -f "$CURRENT_STANDARD_DATASET" ]; then
    echo "[OK] Current standard dataset found:"
    echo "     $CURRENT_STANDARD_DATASET"
elif find results -maxdepth 1 -type f -name '*_summary.csv' | grep -q . 2>/dev/null; then
    echo "[INFO] Current standard dataset not found."
    echo "       Dashboard will auto-fallback to another available dataset."
    echo "       To rebuild the current standard dataset, run:"
    echo "       $CURRENT_STANDARD_PRECOMPUTE_CMD"
else
    echo "[INFO] No precomputed dataset found yet."
    echo "       Dashboard can still start, but main story pages may stay limited."
    echo "       To build the current standard dataset, run:"
    echo "       $CURRENT_STANDARD_PRECOMPUTE_CMD"
fi

echo ""
# --- Pick an available Streamlit port ---
PORT="$($PYTHON - <<'PY'
import os
import socket

start = int(os.environ.get("STREAMLIT_PORT", "8501"))
max_tries = 50

for port in range(start, start + max_tries):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            continue
        print(port)
        break
else:
    raise SystemExit(
        f"[ERROR] No available port found in range {start}-{start + max_tries - 1}."
    )
PY
)"

if [ -z "$PORT" ]; then
    echo ""
    echo "[ERROR] Failed to determine an available Streamlit port."
    read -p "Press Enter to exit..."
    exit 1
fi

if [ "$PORT" != "8501" ]; then
    echo ""
    echo "[WARNING] Port 8501 is in use. Falling back to port $PORT."
fi

echo ""
echo "Starting dashboard..."
echo "  URL: http://localhost:$PORT"
echo "  Press Ctrl+C to stop."
echo ""

# --- Launch Streamlit ---
$PYTHON -m streamlit run dashboard/app.py \
    --server.port "$PORT" \
    --server.headless false \
    --browser.gatherUsageStats false
