@echo off
REM Manual-Dex: import CAD exports and push the CURRENT branch.
REM Requires Python 3, Git and Git LFS. For a new checkout, pass a remote URL.
setlocal
cd /d "%~dp0"
set "MANUAL_DEX_SOURCE=%~dp0.."

where git >nul 2>nul || (echo Git is required. & exit /b 1)
where python >nul 2>nul || (echo Python 3 is required. & exit /b 1)
git lfs version >nul 2>nul || (echo Git LFS is required. & exit /b 1)
if not exist .git git init -b main
git lfs install --local || exit /b 1

REM Includes the current three-part Quest mount and Manual-Dex STEP names.
python tools\place_exports.py "%MANUAL_DEX_SOURCE%\robot_hand1\export" --assembly hand
if errorlevel 1 exit /b 1
python tools\place_exports.py "%MANUAL_DEX_SOURCE%\wearable_glove\export" --assembly glove
if errorlevel 1 exit /b 1

REM Preserve the configured origin and branch; use the user's Git identity.
git remote get-url origin >nul 2>nul
if errorlevel 1 (
    if "%~1"=="" (
        echo No origin configured. Pass the intended Git remote URL.
        exit /b 1
    )
    git remote add origin "%~1" || exit /b 1
)
git add hardware || exit /b 1
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Update Manual-Dex CAD release assets" || exit /b 1
)
git push -u origin HEAD || exit /b 1
echo Manual-Dex CAD assets pushed on the current branch.
