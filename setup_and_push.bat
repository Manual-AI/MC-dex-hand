@echo off
setlocal
if /I "%~1"=="--help" goto usage
if /I "%~1"=="/?" goto usage
if /I "%~1"=="--push" goto publish

where python >nul 2>nul || (echo Python 3 is required to import CAD exports. & exit /b 1)
if "%~1"=="" goto default_exports
python "%~dp0tools\place_exports.py" %*
if errorlevel 1 exit /b 1
goto imported

:default_exports
python "%~dp0tools\place_exports.py" "%~dp0..\robot_hand1\export" "%~dp0..\wearable_glove\export"
if errorlevel 1 exit /b 1

:imported
echo Review the changes with git diff and commit the intended files.
exit /b 0

:publish
if not "%~2"=="" goto usage
cd /d "%~dp0" || exit /b 1
git symbolic-ref --quiet HEAD >nul || (echo Check out the branch you want to publish. & exit /b 1)
git lfs version >nul 2>nul || (echo Git LFS is required to publish CAD assets. & exit /b 1)
git lfs install --local || exit /b 1
git push origin HEAD
exit /b %errorlevel%

:usage
echo Import:  setup_and_push.bat [export_directory ...]
echo Publish committed changes on the current branch:  setup_and_push.bat --push
exit /b 0
