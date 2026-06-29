@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8

echo ================================================================
echo    EVIDENCIA DE EJECUCION - Agente "Banco Digital Chile"
echo    ISY0101 - Roger Rosas, Rodrigo Santis, Edgardo Gutierrez
echo ================================================================
echo.

REM --- Seleccionar un interprete de Python con el stack instalado ---
set "PY="
if exist "C:\Python314\python.exe" set "PY=C:\Python314\python.exe"
if not defined PY set "PY=python"
echo Interprete: %PY%
"%PY%" --version
echo.

REM --- Asegurar dependencias (instala solo si faltan; no requiere internet si ya estan) ---
"%PY%" -c "import numpy,pandas,matplotlib,openpyxl,pytest" 1>nul 2>nul
if errorlevel 1 (
    echo [AVISO] Faltan dependencias. Instalando con pip...
    "%PY%" -m pip install -q --user pandas numpy matplotlib openpyxl pytest
    echo.
)

echo [1/4] Pipeline de observabilidad (telemetria, metricas, dashboard)...
echo ----------------------------------------------------------------
"%PY%" run_observability.py
echo.
echo [2/4] Suite de pruebas automatizadas (pytest)...
echo ----------------------------------------------------------------
"%PY%" -m pytest tests/ -v
echo.
echo [3/4] Demostracion de seguridad (guardrails: PII + injection)...
echo ----------------------------------------------------------------
"%PY%" -m security.guardrails
echo.
echo [4/4] Demostracion del pipeline RAG (fuentes internas + externas)...
echo ----------------------------------------------------------------
"%PY%" -m rag.rag_pipeline
echo.
echo ================================================================
echo    EVIDENCIA COMPLETA - Todos los componentes ejecutados
echo ================================================================
echo.
pause
