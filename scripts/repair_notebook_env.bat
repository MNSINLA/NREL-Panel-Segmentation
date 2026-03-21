@echo off
setlocal

REM Run from the repository root with the project's virtual environment active.
python -m pip install -e . --no-deps
if errorlevel 1 exit /b 1

REM IPython/ipykernel need a newer typing_extensions than tensorflow 2.13 pins.
python -m pip install --no-deps --force-reinstall typing_extensions==4.15.0
if errorlevel 1 exit /b 1

python -c "import panel_segmentation.panel_detection as pd; print(pd.__file__)"
if errorlevel 1 exit /b 1

python -c "import inspect, panel_segmentation.panel_detection as pd; print('verify=False' in inspect.getsource(pd.PanelDetection.generateSatelliteImage))"
if errorlevel 1 exit /b 1

python -c "from typing_extensions import TypeAliasType; print('typing ok')"
if errorlevel 1 exit /b 1

echo.
echo Notebook environment repaired.
echo Expected results:
echo   - panel_detection.py path points into this repo
echo   - verify=False check prints False
echo   - typing ok
