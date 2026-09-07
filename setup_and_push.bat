@echo off
REM MC-dex-hand: one-click repo setup + push.
REM Run from inside the MC-dex-hand folder (double-click). Requires git + git-lfs installed
REM and a GitHub login on this machine (Git Credential Manager will prompt in the browser if needed).
setlocal
cd /d "%~dp0"
set SRC=%~dp0..

echo == copying exported CAD files into the repo layout
copy /y "%SRC%\robot_hand1\export\stl\rh_*.STL"         hardware\robot_hand\stl\  >nul
copy /y "%SRC%\wearable_glove\export\stl\gl_*.STL"      hardware\glove\stl\       >nul
copy /y "%SRC%\robot_hand1\export\stl\cm_camera_*.STL"       hardware\common\stl\ >nul
copy /y "%SRC%\robot_hand1\export\stl\cm_electronics_*.STL"  hardware\common\stl\ >nul
copy /y "%SRC%\robot_hand1\export\stl\cm_quest_adapter_*.STL" third_party\udcap\stl\ >nul
copy /y "%SRC%\robot_hand1\export\step\manu_dex_hand_robot_hand.step" hardware\step\mc_dex_hand_robot_hand.step >nul
copy /y "%SRC%\wearable_glove\export\step\manu_dex_hand_glove.step"   hardware\step\mc_dex_hand_glove.step >nul
REM lower-case the .STL extensions so names match the BOM/README
for /r hardware %%f in (*.STL) do ren "%%f" "%%~nf.stl" 2>nul
for /r third_party %%f in (*.STL) do ren "%%f" "%%~nf.stl" 2>nul
del /q hardware\*\stl\.gitkeep hardware\step\.gitkeep third_party\udcap\stl\.gitkeep 2>nul

echo == git init + LFS
where git >nul 2>nul || (echo git not found - install Git for Windows first & pause & exit /b 1)
git lfs version >nul 2>nul || (echo git-lfs not found - install from https://git-lfs.com & pause & exit /b 1)
if not exist .git git init -b main
git lfs install --local
git add -A
git -c user.name="Roman" -c user.email="roman@manualcognition.ai" commit -m "Initial release: BOM, tooling, 48 printed-part STLs, assembly STEPs (LFS)"
git remote remove origin 2>nul
git remote add origin https://github.com/Manual-AI/MC-dex-hand.git
echo == pushing (LFS objects ~150 MB, may take a few minutes)
git push -u origin main
echo.
echo Done. Check https://github.com/Manual-AI/MC-dex-hand
pause
