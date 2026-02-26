@echo off
echo === SteamDeckSoft Build ===

tasklist /FI "IMAGENAME eq SteamDeckSoft.exe" 2>NUL | find /I "SteamDeckSoft.exe" >NUL
if %ERRORLEVEL% EQU 0 (
    echo SteamDeckSoft.exe is running. Closing...
    taskkill /IM SteamDeckSoft.exe /F >NUL 2>&1
    timeout /t 2 /nobreak >NUL
)

pyinstaller --noconfirm --clean --onefile --windowed ^
    --name SteamDeckSoft ^
    --add-data "config;config" ^
    --add-binary "src\native\numpad_hook.dll;." ^
    --hidden-import comtypes.stream ^
    --hidden-import pycaw.utils ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build complete: dist\SteamDeckSoft.exe
) else (
    echo.
    echo Build failed!
)
pause
