@echo off
REM Export Structurizr diagrams to various formats
REM Uses structurizr/cli Docker image

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Alexandria - Export Architecture Diagrams
echo ========================================
echo.

REM Change to project root
cd /d "%~dp0.."

REM Check if output directory exists
if not exist "docs\architecture\diagrams" (
    echo Creating diagrams directory...
    mkdir "docs\architecture\diagrams"
)

REM Get format from argument or prompt user
set FORMAT=%1
if "%FORMAT%"=="" (
    echo.
    echo Available formats:
    echo   1. PNG  - Raster images
    echo   2. SVG  - Vector graphics
    echo   3. PlantUML - Text-based UML
    echo   4. Mermaid - Markdown diagrams
    echo   5. DOT - Graphviz
    echo   6. All - Export all formats
    echo.
    set /p CHOICE="Choose format (1-6): "

    if "!CHOICE!"=="1" set FORMAT=png
    if "!CHOICE!"=="2" set FORMAT=svg
    if "!CHOICE!"=="3" set FORMAT=plantuml
    if "!CHOICE!"=="4" set FORMAT=mermaid
    if "!CHOICE!"=="5" set FORMAT=dot
    if "!CHOICE!"=="6" set FORMAT=all
)

if "%FORMAT%"=="all" (
    echo.
    echo Exporting all formats...
    echo.

    echo [1/5] Exporting PNG...
    docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/cli export -workspace workspace.dsl -format png -output diagrams

    echo [2/5] Exporting SVG...
    docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/cli export -workspace workspace.dsl -format svg -output diagrams

    echo [3/5] Exporting PlantUML...
    docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/cli export -workspace workspace.dsl -format plantuml -output diagrams

    echo [4/5] Exporting Mermaid...
    docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/cli export -workspace workspace.dsl -format mermaid -output diagrams

    echo [5/5] Exporting DOT...
    docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/cli export -workspace workspace.dsl -format dot -output diagrams

) else (
    echo.
    echo Exporting %FORMAT%...
    docker run --rm -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/cli export -workspace workspace.dsl -format %FORMAT% -output diagrams
)

echo.
echo ========================================
echo Export complete!
echo.
echo Output: docs\architecture\diagrams\
echo.
dir /b "docs\architecture\diagrams" 2>nul
echo ========================================
echo.

pause
