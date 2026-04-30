@echo off
REM AI電話自動化 — ローカル起動スクリプト（Windows）

where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
)

cd /d "%~dp0.."
echo Starting AI電話自動化...
uv run phone-automation
pause
