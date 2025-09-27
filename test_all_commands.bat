# Тест всех команд эмулятора
help
vfs-info

# Тест ls в корне
ls

# Тест cd и ls в поддиректориях (если есть)
cd home
ls
cd user
ls
cd projects
ls
cd python
ls
cat main.py          # <-- неизвестная команда → ошибка
cd ..
cd ..
cd ..
cd etc
ls
cd ..

# Тест ошибок
cd non_existent_dir
ls invalid_arg
vfs-info extra_arg
cd
cd /home/user/../etc
ls

# Тест выхода
exit