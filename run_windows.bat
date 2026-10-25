@echo off
title DiskScope - Disk Space Analyzer
cd /d "%~dp0"
python diskscope.py
if errorlevel 1 (
  echo.
  echo Could not start DiskScope. Check that Python 3 is installed and added to PATH.
  pause
)
