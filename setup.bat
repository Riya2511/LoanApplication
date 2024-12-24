@echo off
setlocal enabledelayedexpansion

:: Download Miniconda
echo Downloading Miniconda...
curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe -o miniconda.exe

:: Install Miniconda silently
echo Installing Miniconda...
start /wait "" .\miniconda.exe /S

:: Remove installer
echo Removing Miniconda installer...
del miniconda.exe

:: Install requirements
echo Installing Python requirements...
pip install -r requirements.txt

:: Run main Python script
echo Running main application...
python main.py

:: Cleanup script
echo Performing comprehensive cleanup...

:: Remove specific directories
if exist "__pycache__" (
    echo Removing __pycache__ directory...
    rmdir /s /q "__pycache__"
)

if exist "logs" (
    echo Removing logs directory...
    rmdir /s /q "logs"
)

if exist "build" (
    echo Removing build directory...
    rmdir /s /q "build"
)

:: Remove all files except specific ones
for %%F in (*) do (
    set "keep=0"
    if "%%~nxF"=="LoanApplication.exe" set "keep=1"
    if "%%~nxF"=="loanApp.db" set "keep=1"
    
    if !keep!==0 del "%%F"
)

echo Cleanup complete.