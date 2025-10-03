@echo off
chcp 65001 >nul
echo Запуск эмулятора терминала с тестовым скриптом...
python main.py --vfs-path vfs_test.xml --startup-script startup_script.txt
pause