import os
import re
from typing import List, Tuple
from vfs import VFSManager


class CommandHandler:
    def __init__(self, vfs_xml_path: str):
        
        # инициализация обработчика команд с поддержкой VFS.
        
        try:
            self.vfs = VFSManager(vfs_xml_path)
        except (FileNotFoundError, ValueError) as e:
            raise RuntimeError(f"Ошибка загрузки VFS: {e}")

        self.history = []
        self.command_handlers = {
            'exit': self._handle_exit,
            'ls': self._handle_ls,
            'cd': self._handle_cd,
            'help': self._handle_help,
            'vfs-info': self._handle_vfs_info,
            'pwd': self._handle_pwd,
            'cat': self._handle_cat,
            'tac': self._handle_tac,      # новая команда 4
            'rev': self._handle_rev,      # новая команда 4
            'mkdir': self._handle_mkdir,  # Новая команда 5 
            'cp': self._handle_cp,       # Новая команда 5
            'echo': self._handle_echo,    # Новая команда 5
        }

    def execute_script(self, script_path: str) -> Tuple[List[str], List[str]]:
        executed_commands = []
        errors = []
        
        if not script_path:
            errors.append("Путь к скрипту не указан")
            return executed_commands, errors
            
        if not os.path.exists(script_path):
            errors.append(f"Скрипт '{script_path}' не найден")
            return executed_commands, errors
        
        if not os.path.isfile(script_path):
            errors.append(f"'{script_path}' не является файлом")
            return executed_commands, errors
            
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                command = line.strip()
                
                # пропускаем пустые строки и комментарии
                if not command or command.startswith('#'):
                    continue
                
                try:
                    # используем тот же execute(), что и в интерактивном режиме
                    result = self.execute(command)
                    executed_commands.append(command)
                    
                    # если команда завершает работу — прерываем скрипт
                    if result == "EXIT_TERMINAL":
                        break
                        
                except Exception as e:
                    error_msg = f"Строка {line_num}: {str(e)}"
                    errors.append(error_msg)
                    
        except UnicodeDecodeError:
            errors.append(f"Ошибка кодировки файла '{script_path}'. Используйте UTF-8")
        except Exception as e:
            errors.append(f"Ошибка чтения скрипта: {str(e)}")
            
        return executed_commands, errors

    def expand_environment_variables(self, text: str) -> str:
        if not text:
            return text

        def replace_var(match: re.Match) -> str:
            var_name = match.group(1) or match.group(2)
            if value := os.environ.get(var_name):
                return value
            raise ValueError(f"Переменная окружения ${var_name} не найдена")

        pattern = r'\$([A-Za-z_]\w*)|\$\{([A-Za-z_]\w*)\}'
        return re.sub(pattern, replace_var, text)

    def execute(self, command: str) -> str:
        if not (clean_cmd := command.strip()):
            return ""

        try:
            expanded_cmd = self.expand_environment_variables(clean_cmd).strip()
            if not expanded_cmd:
                return ""
        except ValueError as e:
            return f"Ошибка: {e}\n"

        parts = expanded_cmd.split()
        if not parts:
            return ""

        cmd = parts[0]
        args = parts[1:]

        if handler := self.command_handlers.get(cmd):
            if cmd == 'exit':
                if args:
                    return "Ошибка: команда exit не принимает аргументов\n"
                return handler()
            else:
                return handler(args)
        else:
            return f"Ошибка: неизвестная команда '{cmd}'\n"

    def _handle_exit(self) -> str:
        return "EXIT_TERMINAL"
    
    def _handle_ls(self, args: List[str]) -> str:
        if len(args) > 1:
            return "Ошибка: команда ls принимает не более одного аргумента (путь)\n"
        
        try:
            if args:
                # сохраняет текущий путь
                original_path = self.vfs._current_path.copy()
                
                # пробует перейти по указанному пути
                result = self.vfs.cd(args[0])
                if result:  # Если ошибка - возвращаем её
                    return result
                
                # получаетм список файлов
                ls_result = self.vfs.ls()
                
                # возвращается обратно
                self.vfs._current_path = original_path
                return ls_result
            else:
                # ls без аргументов = текущая директория
                return self.vfs.ls()
        except Exception as e:
            return f"Ошибка при выполнении ls: {e}\n"

    def _handle_cd(self, args: List[str]) -> str:
        if len(args) == 0:
            # cd без аргументов -> корень VFS
            return self.vfs.cd("/")
        if len(args) > 1:
            return "Ошибка: команда cd принимает не более одного аргумента\n"
        return self.vfs.cd(args[0])

    def _handle_help(self, args: List[str] = None) -> str:
        return """Доступные команды:
ls                - список файлов и директорий в текущей папке
cd <путь>         - перейти в директорию (поддерживает .. и /)
pwd               - показать текущую директорию
cat <файл>        - вывести содержимое файла
tac <файл>        - вывести содержимое файла в обратном порядке строк
rev <файл>        - перевернуть каждую строку файла задом наперёд
mkdir <путь>      - создать новую директорию
cp <src> <dest>   - скопировать файл
vfs-info          - информация о загруженной VFS
help              - показать эту справку
exit              - выйти из терминала
"""

    def _handle_vfs_info(self, args: List[str] = None) -> str:
        if args:
            return "Ошибка: команда vfs-info не принимает аргументов\n"
        try:
            return self.vfs.get_vfs_info()
        except Exception as e:
            return f"Ошибка получения информации о VFS: {e}\n"
        
    def _handle_pwd(self, args: List[str] = None) -> str:
        if args:
            return "Ошибка: команда pwd не принимает аргументов\n"
        return self.vfs.get_current_path_str() + "\n"

    def _handle_cat(self, args: List[str]) -> str:
        if len(args) != 1:
            return "Ошибка: команда cat требует ровно один аргумент (имя файла)\n"
        
        try:
            content = self.vfs.read_file(args[0])
            return content + ("\n" if not content.endswith('\n') else "")
        except Exception as e:
            return f"Ошибка: {e}\n"
        
    #-----------------------------------------------------4444444-------------------------------------

    def _handle_tac(self, args: List[str]) -> str:
        # выводит содержимое файла в обратном порядке строк
        if len(args) != 1:
            return "Ошибка: команда tac требует ровно один аргумент (имя файла)\n"
        
        try:
            content = self.vfs.read_file(args[0])
            lines = content.split('\n')
            reversed_lines = lines[::-1]  # обратный порядок строк
            return '\n'.join(reversed_lines) + ("\n" if content else "")
        except Exception as e:
            return f"Ошибка: {e}\n"

    def _handle_rev(self, args: List[str]) -> str:
        # переворачивает каждую строку файла задом наперёд
        if len(args) != 1:
            return "Ошибка: команда rev требует ровно один аргумент (имя файла)\n"
        
        try:
            content = self.vfs.read_file(args[0])
            lines = content.split('\n')
            reversed_lines = [line[::-1] for line in lines]  # каждая строка перевёрнута
            return '\n'.join(reversed_lines) + ("\n" if content else "")
        except Exception as e:
            return f"Ошибка: {e}\n"
        
    #--------------------------------------------5555555--------------------------
    def _handle_mkdir(self, args: List[str]) -> str:
        # оздает новую директорию
        if len(args) != 1:
            return "Ошибка: команда mkdir требует ровно один аргумент (путь)\n"
        
        try:
            result = self.vfs.mkdir(args[0])
            return result if result else "Директория создана успешно\n"
        except Exception as e:
            return f"Ошибка при выполнении mkdir: {e}\n"

    def _handle_cp(self, args: List[str]) -> str:
        # копирует файл
        if len(args) != 2:
            return "Ошибка: команда cp требует два аргумента (источник и назначение)\n"
        
        try:
            result = self.vfs.cp(args[0], args[1])
            return result if result else "Файл скопирован успешно\n"
        except Exception as e:
            return f"Ошибка при выполнении cp: {e}\n"
        

    def _handle_echo(self, args: List[str]) -> str:
        # выводит текст в консоль, поддерживает переменные окружения и специальные символы"""
        if not args:
            return "\n"  # echo без аргументов - просто пустая строка
        
        # объединяет все аргументы в одну строку
        text = ' '.join(args)
        
        # обрабатывает специальные символы
        processed_text = self._process_echo_special_chars(text)
        
        # подставляет переменные окружения
        try:
            processed_text = self.expand_environment_variables(processed_text)
        except ValueError as e:
            return f"Ошибка: {e}\n"
        
        return processed_text + "\n"
    
    def _process_echo_special_chars(self, text: str) -> str:
        #Обрабатывает специальные символы в команде echo
        # заменяет escape-последовательности
        replacements = {
            '\\n': '\n',
            '\\t': '\t',
            '\\\\': '\\',
            '\\$': '$'
        }
        
        result = text
        for esc, char in replacements.items():
            result = result.replace(esc, char)
        
        return result