@echo off
REM miWork Launcher — auto-detects Anaconda and opens browser
setlocal

REM Try to find conda
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
    REM Try common Anaconda locations
    if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\anaconda3\Scripts\activate.bat"
    ) else if exist "%USERPROFILE%\Anaconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\Anaconda3\Scripts\activate.bat"
    ) else if exist "C:\ProgramData\Anaconda3\Scripts\activate.bat" (
        call "C:\ProgramData\Anaconda3\Scripts\activate.bat"
    ) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
    ) else (
        echo Warning: Anaconda not found. Using system Python.
    )
)

REM Optional: backup the database
if exist "data\tracker.db" (
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set "datestamp=%%c%%a%%b"
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "timestamp=%%a%%b"
    copy "data\tracker.db" "data\tracker-%datestamp%-%timestamp%.db.bak" >nul 2>&1
)

REM Start browser after a short delay
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

REM Run the Flask app
set FLASK_APP=app
set FLASK_ENV=development
python -m flask run --host=127.0.0.1 --port=5000

endlocal
