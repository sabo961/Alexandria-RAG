@echo off
REM Stop Structurizr Lite container

echo.
echo ========================================
echo Alexandria - Stop Structurizr Lite
echo ========================================
echo.

docker ps --format "{{.Names}}" | findstr /C:"alexandria-structurizr" >nul
if %errorlevel% == 0 (
    echo Stopping container...
    docker stop alexandria-structurizr
    echo.
    echo Container stopped successfully!
) else (
    echo Container is not running.
)

echo.
pause
