import os
import re
from typing import List

class CommandHandler:
    def __init__(self):
        self.history = []
        self.command_handlers = {
            'exit': self._handle_exit,
            'ls': self._ls_stub,
            'cd': self._cd_stub,
            'help': self._help,
        }



    def expand_environment_variables(self, text: str) -> str:
   
        if not text:
            return text

        # Внутренняя функция для замены найденных переменных
        def replace_var(match: re.Match) -> str:
            # Извлекаем имя переменной (из $VAR или ${VAR})
            var_name = match.group(1) or match.group(2)
        
            # получаем через os.environ названия переменных окруждения, если оно сущесвует
            if value := os.environ.get(var_name):
                return value  # Возвращаем значение если найдено
        
            # Если переменная не найдена - бросаем исключение
            raise ValueError(f"Переменная окружения ${var_name} не найдена")

        # Паттерн для поиска: $VAR или ${VAR}
        pattern = r'\$([A-Za-z_]\w*)|\$\{([A-Za-z_]\w*)\}'
    
        # Заменяем все найденные переменные их значениями
        return re.sub(pattern, replace_var, text)
    


    def execute(self, command: str) -> str:
        #Выполняет команду с обработкой переменных окружения
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
            # Для всех команд, кроме exit, передаём аргументы
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
    
    #Заглушка для ls — выводит имя команды и аргументы
    def _ls_stub(self, args: List[str]) -> str:
        
        if len(args) > 1:
            return "Ошибка: команда ls принимает не более одного аргумента\n"
        return f"Вызвана команда: ls с аргументами: {args}\n"
    
    #Заглушка для cd — выводит имя команды и аргументы
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