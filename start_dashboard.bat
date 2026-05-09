@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM NODI Interferometric Simulator — Dashboard Launcher (Windows)
REM ============================================================
REM Double-click this file to start the dashboard.
REM Browser will auto-open at the first available port (starting from 8501).
REM Press Ctrl+C in the terminal window to stop.
REM ============================================================

REM --- Navigate to the directory containing this bat file ---
cd /d "%~dp0"

echo ============================================
echo   NODI Interferometric Simulator Dashboard
echo ============================================
echo.

REM ============================================================
REM 1. Find a Python interpreter that has streamlit installed
REM    (mirrors .command priority order)
REM ============================================================
set "PYTHON="

REM Try "python" on PATH
where python >nul 2>&1
IF NOT ERRORLEVEL 1 (
    python -c "import streamlit" >nul 2>&1
    IF NOT ERRORLEVEL 1 set "PYTHON=python"
)

REM Try "py" launcher (Windows Python Launcher)
if not defined PYTHON (
    where py >nul 2>&1
    IF NOT ERRORLEVEL 1 (
        py -3 -c "import streamlit" >nul 2>&1
        IF NOT ERRORLEVEL 1 set "PYTHON=py -3"
    )
)

REM No Python with streamlit — try to install
if not defined PYTHON (
    set "_BASEPY="

    where python >nul 2>&1
    IF NOT ERRORLEVEL 1 set "_BASEPY=python"

    if not defined _BASEPY (
        where py >nul 2>&1
        IF NOT ERRORLEVEL 1 set "_BASEPY=py -3"
    )

    if not defined _BASEPY (
        echo [ERROR] Python not found on PATH.
        echo Please install Python 3.10+ from https://www.python.org
        echo Make sure to tick "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )

    echo [INFO] streamlit not found. Installing required packages...
    echo.
    !_BASEPY! -m pip install streamlit plotly numpy scipy pandas
    IF ERRORLEVEL 1 (
        echo.
        echo [ERROR] pip install failed. Try running manually:
        echo   !_BASEPY! -m pip install streamlit plotly numpy scipy pandas
        echo.
        pause
        exit /b 1
    )
    set "PYTHON=!_BASEPY!"
)

for /f "tokens=*" %%v in ('%PYTHON% --version 2^>^&1') do echo Using %%v
echo.

REM ============================================================
REM 2. Set PYTHONPATH so "import nodi_simulator" works from this project root.
REM ============================================================
for %%i in ("%~dp0.") do set "PROJ_ROOT=%%~fi"
set "PYTHONPATH=%PROJ_ROOT%;%PYTHONPATH%"
set "PYTHONUTF8=1"
echo [INFO] PYTHONPATH set to: %PROJ_ROOT%
echo [INFO] PYTHONUTF8=1 (force UTF-8 I/O, avoids cp932 decode errors)
echo.

REM ============================================================
REM 3. Quick self-test: confirm nodi_simulator is importable
REM ============================================================
%PYTHON% -c "import nodi_simulator" >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Could not import nodi_simulator.
    echo         PYTHONPATH = %PYTHONPATH%
    echo         Make sure this bat file is inside the nodi_simulator project folder.
    echo.
    pause
    exit /b 1
)
echo [OK] nodi_simulator importable.
echo.

REM ============================================================
REM 4. Check for precomputed result data
REM ============================================================
set "CURRENT_STANDARD_DATASET=results\ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
set "CURRENT_STANDARD_PRECOMPUTE=%PYTHON% -m nodi_simulator.dashboard.precompute --grid ev_design --particle-profile full_range_biomimetic_exosome_with_anchors --tag full_range_biomimetic_exosome_with_anchors_10000e --workers 8 --freeze-probe-report --artifact-profile standard --progress-interval 2 --resume --checkpoint --checkpoint-batch-size 100 --checkpoint-flush-interval 5 --output results/"

if exist "%CURRENT_STANDARD_DATASET%" (
    echo [OK] Current standard dataset found: %CURRENT_STANDARD_DATASET%
    goto :data_ready
)

dir /b "results\*_summary.csv" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Current standard dataset not found.
    echo        Dashboard will auto-fallback to another available dataset.
    echo        To rebuild the current standard dataset, run:
    echo        %CURRENT_STANDARD_PRECOMPUTE%
    goto :data_ready
)

echo [INFO] No precomputed dataset found yet.
echo        Dashboard can still start, but main story pages may stay limited.
echo        To build the current standard dataset, run:
echo        %CURRENT_STANDARD_PRECOMPUTE%

:data_ready
echo.

REM ============================================================
REM 5. Find an available port (equivalent to .command heredoc)
REM    Write the port-finder to a temp .py file, run it, read output.
REM ============================================================
set "PORT_PY=%TEMP%\nodi_find_port_%RANDOM%.py"

(
    echo import socket, os
    echo start = int^(os.environ.get^("STREAMLIT_PORT", "8501"^)^)
    echo for p in range^(start, start + 50^):
    echo     s = socket.socket^(socket.AF_INET, socket.SOCK_STREAM^)
    echo     if s.connect_ex^(^("127.0.0.1", p^)^) != 0:
    echo         s.close^(^)
    echo         print^(p^)
    echo         break
    echo     s.close^(^)
) > "%PORT_PY%"

set "PORT="
for /f "tokens=*" %%p in ('%PYTHON% "%PORT_PY%"') do set "PORT=%%p"
del "%PORT_PY%" >nul 2>&1

if not defined PORT (
    echo [WARNING] Port detection failed. Defaulting to 8501.
    set "PORT=8501"
)
if not "%PORT%"=="8501" (
    echo [WARNING] Port 8501 is in use. Using port %PORT% instead.
)

REM ============================================================
REM 6. Launch Streamlit
REM ============================================================
echo Starting dashboard...
echo   URL : http://localhost:%PORT%
echo   Press Ctrl+C to stop.
echo.

%PYTHON% -m streamlit run dashboard/app.py --server.port %PORT% --server.headless false --browser.gatherUsageStats false

echo.
echo Dashboard stopped.
pause
endlocal
