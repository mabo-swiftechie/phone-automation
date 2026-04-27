@echo off
cd /d "%~dp0"

REM uv がなければインストール
where uv >nul 2>&1 || (
    echo uv をインストールしています...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
)

REM uvx で起動
uvx --from . phone-automation
pause
