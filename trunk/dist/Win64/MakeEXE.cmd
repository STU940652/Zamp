@echo off
pushd ..\..\src
pyinstaller Zamp.spec --distpath=../dist/Win64 --clean -y
if ERRORLEVEL 1 goto END_FAIL
popd

rem Make Installer
pushd ..\Win64_Inno
"%ProgramFiles(x86)%\Inno Setup 5\Compil32.exe" /cc Zamp.iss
if ERRORLEVEL 1 goto END_FAIL
popd

goto END

:END_FAIL
popd
pause

:END
