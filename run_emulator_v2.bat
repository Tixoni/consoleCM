@echo off
chcp 65001 >nul
echo Запуск эмулятора терминала с тестированием команд mkdir и cp...
python main.py --vfs-path vfs_test.xml --startup-script startup_script_v2.txt
pause