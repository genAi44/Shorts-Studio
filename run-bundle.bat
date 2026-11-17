@echo off
cd /d C:\Users\mhama\Desktop\shorts-studio\remotion
echo.
echo === BUNDLE START ===
npx remotion bundle > C:\Users\mhama\Desktop\shorts-studio\bundle-out.log 2>&1
echo.
echo === BUNDLE EXIT: %ERRORLEVEL% ===
echo.
echo === LOG TAIL ===
tail -n 60 C:\Users\mhama\Desktop\shorts-studio\bundle-out.log
