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

@REM :: Remove specific directories
@REM if exist "__pycache__" (
@REM     echo Removing __pycache__ directory...
@REM     rmdir /s /q "__pycache__"
@REM )

@REM if exist "logs" (
@REM     echo Removing logs directory...
@REM     rmdir /s /q "logs"
@REM )

@REM if exist "build" (
@REM     echo Removing build directory...
@REM     rmdir /s /q "build"
@REM )

@REM :: Remove all files except specific ones
@REM for %%F in (*) do (
@REM     set "keep=0"
@REM     if "%%~nxF"=="LoanApplication.exe" set "keep=1"
@REM     if "%%~nxF"=="loanApp.db" set "keep=1"
    
@REM     if !keep!==0 del "%%F"
@REM )

@REM echo Cleanup complete.