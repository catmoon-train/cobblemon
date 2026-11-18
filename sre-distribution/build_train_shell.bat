@echo off
setlocal
if "%COBBLEMON_DIST_WORK%"=="" set "COBBLEMON_DIST_WORK=I:\temp\verify_suite"
if exist "C:\Program Files\Zulu\zulu-21\bin\java.exe" (
    set "JAVA_HOME=C:\Program Files\Zulu\zulu-21"
    set "PATH=%JAVA_HOME%\bin;%PATH%"
)
python -X utf8 "%~dp0build_train_shell.py" --verify %*
endlocal
