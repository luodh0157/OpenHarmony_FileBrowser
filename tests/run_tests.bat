@echo off
REM =============================================================================
REM OpenHarmony File Browser - Test Runner (Windows)
REM =============================================================================
REM Usage:
REM   run_tests.bat              REM Run all tests
REM   run_tests.bat unit         REM Run unit tests only
REM   run_tests.bat integration  REM Run integration tests only
REM   run_tests.bat test_file_utils.py  REM Run specific test file
REM   run_tests.bat --coverage   REM Run with coverage report
REM =============================================================================

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo ============================================
echo  OpenHarmony File Browser - Test Runner
echo ============================================
echo.

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: python not found
    exit /b 1
)

echo Python: python
echo.

set PYTHON=python

for /f "tokens=*" %%i in ('%PYTHON% --version') do set PYVER=%%i
echo Version: %PYVER%
echo.

REM Parse arguments
set COVERAGE=0
set TEST_TYPE=all
set SPECIFIC_FILE=

for %%a in (%*) do (
    if "%%a"=="--coverage" (
        set COVERAGE=1
    ) else if "%%a"=="unit" (
        set TEST_TYPE=unit
    ) else if "%%a"=="integration" (
        set TEST_TYPE=integration
    ) else (
        set SPECIFIC_FILE=%%a
    )
)

REM Install pytest if needed
%PYTHON% -c "import pytest" 2>nul
if %errorlevel% neq 0 (
    echo Installing pytest...
    %PYTHON% -m pip install -q pytest
)

REM Install coverage if needed
if %COVERAGE%==1 (
    %PYTHON% -c "import coverage" 2>nul
    if %errorlevel% neq 0 (
        echo Installing coverage...
        %PYTHON% -m pip install -q coverage pytest-cov
    )
)

REM Run tests
echo Running tests...
echo.

if not "%SPECIFIC_FILE%"=="" (
    if %COVERAGE%==1 (
        %PYTHON% -m pytest "tests\%SPECIFIC_FILE%" -v --tb=short --cov=src --cov-report=term-missing --cov-report=html:htmlcov
    ) else (
        %PYTHON% -m pytest "tests\%SPECIFIC_FILE%" -v --tb=short
    )
) else if "%TEST_TYPE%"=="unit" (
    if %COVERAGE%==1 (
        %PYTHON% -m pytest tests\unit\ -v --tb=short --cov=src --cov-report=term-missing --cov-report=html:htmlcov
    ) else (
        %PYTHON% -m pytest tests\unit\ -v --tb=short
    )
) else if "%TEST_TYPE%"=="integration" (
    if %COVERAGE%==1 (
        %PYTHON% -m pytest tests\integration\ -v --tb=short --cov=src --cov-report=term-missing --cov-report=html:htmlcov
    ) else (
        %PYTHON% -m pytest tests\integration\ -v --tb=short
    )
) else (
    if %COVERAGE%==1 (
        %PYTHON% -m pytest tests\ -v --tb=short --cov=src --cov-report=term-missing --cov-report=html:htmlcov
    ) else (
        %PYTHON% -m pytest tests\ -v --tb=short
    )
)

set EXIT_CODE=%errorlevel%

echo.
echo ============================================

if %EXIT_CODE% equ 0 (
    echo All tests passed!
) else (
    echo Some tests failed (exit code: %EXIT_CODE%)
)

if %COVERAGE%==1 (
    echo Coverage report: htmlcov\index.html
)

echo ============================================

REM Cleanup temporary files
echo.
echo Cleaning up temporary files...
if exist ".pytest_cache" rmdir /s /q ".pytest_cache"

if exist "htmlcov" rmdir /s /q "htmlcov"
if exist ".coverage" del /q ".coverage"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul
echo Cleanup completed.

exit /b %EXIT_CODE%
