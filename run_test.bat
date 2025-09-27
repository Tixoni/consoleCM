@echo off
setlocal

cd /d "%~dp0"

echo Создание тестовых VFS-файлов...

:: Минимальный VFS
(
echo ^<?xml version="1.0" encoding="UTF-8"?^>
echo ^<vfs name="minimal_vfs"^>
echo ^</vfs^>
) > vfs_minimal.xml

:: Средний VFS (несколько файлов)
(
echo ^<?xml version="1.0" encoding="UTF-8"?^>
echo ^<vfs name="medium_vfs"^>
echo   ^<dir name="docs"^>
echo     ^<file name="readme.txt"^>SGVsbG8gZnJvbSBkb2NzIQ==^</file^>
echo   ^</dir^>
echo   ^<file name="config.ini"^>W2RlZmF1bHRdCmRlYnVnID0gdHJ1ZQ==^</file^>
echo ^</vfs^>
) > vfs_medium.xml

:: Глубокий VFS (3+ уровня)
(
echo ^<?xml version="1.0" encoding="UTF-8"?^>
echo ^<vfs name="deep_vfs"^>
echo   ^<dir name="home"^>
echo     ^<dir name="user"^>
echo       ^<dir name="projects"^>
echo         ^<dir name="python"^>
echo           ^<file name="main.py"^>cHJpbnQoIkhlbGxvIik=^</file^>
echo         ^</dir^>
echo         ^<file name="notes.txt"^>VGVzdA==^</file^>
echo       ^</dir^>
echo     ^</dir^>
echo   ^</dir^>
echo   ^<dir name="etc"^>
echo     ^<file name="hosts"^>^</file^>
echo   ^</dir^>
echo ^</vfs^>
) > vfs_deep.xml

echo.
echo Запуск эмулятора с минимальным VFS...
python main.py --vfs-path vfs_minimal.xml --startup-script test_all_commands.bat
pause

echo.
echo Запуск эмулятора со средним VFS...
python main.py --vfs-path vfs_medium.xml --startup-script test_all_commands.bat
pause

echo.
echo Запуск эмулятора с глубоким VFS...
python main.py --vfs-path vfs_deep.xml --startup-script test_all_commands.bat
pause

echo Все тесты завершены.