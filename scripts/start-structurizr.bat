@echo off
REM Start Structurizr Lite for Alexandria Architecture
REM Port 8081 (8080 is used by WBF2)

echo.
echo ========================================
echo Alexandria - Structurizr Lite
echo ========================================
echo.

REM Check if container already exists
docker ps -a --format "{{.Names}}" | findstr /C:"alexandria-structurizr" >nul
if %errorlevel% == 0 (
    echo Container exists. Checking if running...
    docker ps --format "{{.Names}}" | findstr /C:"alexandria-structurizr" >nul
    if %errorlevel% == 0 (
        echo Container already running!
    ) else (
        echo Starting existing container...
        docker start alexandria-structurizr
    )
) else (
    echo Creating new container...
    cd /d "%~dp0.."
    docker run -d --name alexandria-structurizr -p 8081:8080 -v "%cd%\docs\architecture:/usr/local/structurizr" structurizr/lite
)

echo.
echo ========================================
echo Structurizr Lite is running!
echo.
echo   URL: http://localhost:8081
echo   Container: alexandria-structurizr
echo.
echo To stop:  docker stop alexandria-structurizr
echo To remove: docker rm alexandria-structurizr
echo ========================================
echo.

pause
