@echo off
setlocal enabledelayedexpansion

REM ========================================================================
REM Alexandria Library Census - Book Inventory Generator
REM ========================================================================
REM Purpose: Scan all books in Alexandria library and generate inventory report
REM Location: Temenos/Akademija/Alexandria/scripts/
REM Usage: Double-click to run, or execute from command line
REM ========================================================================

echo.
echo ========================================================================
echo Alexandria Library Census - Book Inventory
echo ========================================================================
echo.

REM Set timestamp for output filename
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTPUT=alexandria-census-%TIMESTAMP%.txt

REM Configure library path (Google Drive Desktop sync)
REM Common paths: C:\Users\goran\Google Drive\Alexandria or G:\My Drive\Alexandria
set LIBRARY_PATH=G:\My Drive\Alexandria

echo Scanning library at: %LIBRARY_PATH%
echo Output file: %OUTPUT%
echo.

REM Check if library path exists
if not exist "%LIBRARY_PATH%" (
    echo ERROR: Library path does not exist: %LIBRARY_PATH%
    echo Please edit this batch file and set LIBRARY_PATH to your Alexandria library folder.
    pause
    exit /b 1
)

REM Create output file header
echo ======================================================================== > %OUTPUT%
echo Alexandria Library - Full Inventory Census >> %OUTPUT%
echo ======================================================================== >> %OUTPUT%
echo Generated: %date% %time% >> %OUTPUT%
echo Library Path: %LIBRARY_PATH% >> %OUTPUT%
echo. >> %OUTPUT%

REM Count books by format
echo Counting books by format...
echo Format Distribution: >> %OUTPUT%
echo ---------------------------------------- >> %OUTPUT%

for %%e in (pdf epub mobi djvu chm azw azw3 fb2 txt doc docx rtf odt md) do (
    for /f %%a in ('dir "%LIBRARY_PATH%\*.%%e" /s /b 2^>nul ^| find /c /v ""') do (
        echo %%e: %%a books >> %OUTPUT%
        echo   %%e: %%a books
    )
)

echo. >> %OUTPUT%
echo ======================================================================== >> %OUTPUT%
echo Full File Listing (All Books in Library): >> %OUTPUT%
echo ======================================================================== >> %OUTPUT%
echo. >> %OUTPUT%

REM List all book files
echo Generating full file listing...
dir "%LIBRARY_PATH%\*.pdf" "%LIBRARY_PATH%\*.epub" "%LIBRARY_PATH%\*.mobi" "%LIBRARY_PATH%\*.djvu" "%LIBRARY_PATH%\*.chm" "%LIBRARY_PATH%\*.azw" "%LIBRARY_PATH%\*.azw3" "%LIBRARY_PATH%\*.fb2" "%LIBRARY_PATH%\*.txt" "%LIBRARY_PATH%\*.doc" "%LIBRARY_PATH%\*.docx" "%LIBRARY_PATH%\*.rtf" "%LIBRARY_PATH%\*.odt" "%LIBRARY_PATH%\*.md" /s /b >> %OUTPUT% 2>nul

echo. >> %OUTPUT%
echo ======================================================================== >> %OUTPUT%
echo Census Complete! >> %OUTPUT%
echo Total lines in output: >> %OUTPUT%
find /c /v "" %OUTPUT% >> %OUTPUT%
echo ======================================================================== >> %OUTPUT%

echo.
echo ========================================================================
echo Census completed successfully!
echo ========================================================================
echo Output file: %OUTPUT%
echo.
echo Next steps:
echo 1. Review the census file to see all books in your library
echo 2. Use this file for Qdrant ingestion planning
echo 3. Estimate total tokens needed for embeddings
echo.
pause
