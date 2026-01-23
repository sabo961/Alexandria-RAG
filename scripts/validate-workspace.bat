@echo off
REM Validate Structurizr workspace.dsl syntax

echo.
echo ========================================
echo Alexandria - Validate Workspace DSL
echo ========================================
echo.

cd /d "%~dp0.."

echo Validating workspace.dsl...
echo.

docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/cli validate -workspace workspace.dsl

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo ✅ Workspace is valid!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ❌ Validation failed - check errors above
    echo ========================================
)

echo.
pause
