import os
import re
from typing import List, Tuple

class CommandHandler:
    def __init__(self):
        self.history = []
        self.command_handlers = {
            'exit': self._handle_exit,
            'ls': self._ls_stub,
            'cd': self._cd_stub,
            'help': self._help,
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
                commands = f.readlines()
            
            for line_num, command in enumerate(commands, 1):
                command = command.strip()
                
                if not command or command.startswith('#'):
                    continue
                    
                print(f"DEBUG: Выполнение строки {line_num}: {command}")
                
                try:
                    result = self.execute(command)
                    executed_commands.append(command)
                    
                    if result == "EXIT_TERMINAL":
                        errors.append(f"Строка {line_num}: команда exit прервала выполнение скрипта")
                        break
                        
                except Exception as e:
                    error_msg = f"Строка {line_num}: {str(e)}"
                    errors.append(error_msg)
                    print(f"ERROR: {error_msg}")
                    
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
    
    def _ls_stub(self, args: List[str]) -> str:
        if len(args) > 1:
            return "Ошибка: команда ls принимает не более одного аргумента\n"
        return f"Вызвана команда: ls с аргументами: {args}\n"
    
    def _cd_stub(self, args: List[str]) -> str:
        if len(args) > 1:
            return "Ошибка: команда cd принимает не более одного аргумента\n"
        return f"Вызвана команда: cd с аргументами: {args}\n"

    def _help(self, args: List[str] = None) -> str:
        return """Доступные команды:
ls [директория] - список файлов (заглушка)
cd [директория] - сменить директорию (заглушка)
help - показать справку
exit - выйти из терминала
"""