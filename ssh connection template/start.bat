@echo off

REM Check if paramiko is installed
python -c "import paramiko" 2>NUL
if %errorlevel% neq 0 (
    echo paramiko is not installed. Installing now...
    pip install paramiko
) else (
    echo paramiko is already installed.
)


set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%main.py"
pause