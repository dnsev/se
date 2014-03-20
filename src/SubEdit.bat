@echo off
set BASE_DIR=%~dp0



:python_setup
:: Check if python exists
set PYTHON_EXE=python
%PYTHON_EXE% --version > nul 2> nul || goto :python_missing

:: If it does, go to the version test
goto :version_test_native



:python_missing
goto :python_not_found



:version_test_native
:: Test that the version is 2.7.x
%PYTHON_EXE% "%BASE_DIR%apps\Version.py" 2 7 > nul 2> nul || goto :python_missing

:: If it is, start
goto :start



:version_test_custom
:: Test that the version is 2.7.x
%PYTHON_EXE% "%BASE_DIR%apps\Version.py" 2 7 > nul 2> nul || goto :python_not_found

:: If it is, start
goto :start



:python_not_found
:: Python not installed anywhere, or wrong version
echo Python does not appear to be installed on your system,
echo     you have the wrong version, or you installed it improperly.
echo.
echo Download and install Python 2.7.x and add the directory to your
echo     "path" environment variable.
echo.
echo For info on how to setup Python (with or without using the "path",) visit:
echo     http://dnsev.github.io/se/#about/python
echo.

:: Attempt to open install information
start "" "http://dnsev.github.io/se/#about/python" > nul 2> nul

:: Wait
pause

:: Terminate
goto :eof



:start
:: Execute
%PYTHON_EXE% "%BASE_DIR%apps\SubEdit.py" -settings_if_exists "%BASE_DIR%settings.txt" %* && goto :complete

:: Error
pause

:: Terminate
goto :eof


:: Complete
:complete

