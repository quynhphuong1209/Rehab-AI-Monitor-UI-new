@echo off
cd /d "%~dp0.."
echo Dang chuan bi day code len GitHub UI-new...
git add .
git commit -m "Update Rehab AI Monitor UI"
git push gh-new main
echo.
echo Hoan tat! Nhan phim bat ky de thoat.
pause
