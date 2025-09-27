# main.py
import tkinter as tk
from tkinter import scrolledtext
from handlers import CommandHandler
from vfs import VFSManager
import os
import socket
import argparse
import sys


def parse_arguments():
    parser = argparse.ArgumentParser(description='Эмулятор терминала')
    parser.add_argument('--vfs-path', type=str, required=True,
                      help='Путь к XML-файлу с виртуальной файловой системой')
    parser.add_argument('--startup-script', type=str, default=None,
                      help='Путь к стартовому скрипту')
    
    args = parser.parse_args()
    
    # Проверка существования XML-файла
    if not os.path.isfile(args.vfs_path):
        raise FileNotFoundError(f"VFS XML-файл не найден: {args.vfs_path}")
    
    if args.startup_script and not os.path.exists(args.startup_script):
        raise FileNotFoundError(f"Стартовый скрипт не найден: {args.startup_script}")
    
    return args


class ShellEmulator:
    def __init__(self):
        try:
            args = parse_arguments()
            self._debug_output(args)
            
            self.vfs_path = args.vfs_path
            self.startup_script = args.startup_script
            
            # Инициализация GUI
            self.root = tk.Tk()
            username = os.getlogin()
            hostname = socket.gethostname()
            self.root.title(f"Эмулятор - [{username}@{hostname}] - VFS: {self.vfs_path}")
            self.root.geometry("800x600")
            
            self.command_handler = CommandHandler(self.vfs_path)
            self.setup_gui()
            
            # Выполнение стартового скрипта
            if self.startup_script:
                self.execute_startup_script()
                
        except Exception as e:
            print(f"Критическая ошибка инициализации: {e}")
            sys.exit(1)

    def _debug_output(self, args):
        """Детальный отладочный вывод"""
        print("=" * 60)
        print("DEBUG: Параметры эмулятора терминала")
        print("=" * 60)
        print(f"VFS Path: {os.path.abspath(args.vfs_path)}")
        print(f"VFS Exists: {os.path.exists(args.vfs_path)}")
        print(f"Startup Script: {args.startup_script}")
        if args.startup_script:
            print(f"Script Exists: {os.path.exists(args.startup_script)}")
            print(f"Script is file: {os.path.isfile(args.startup_script)}")
        print("=" * 60)

    def setup_gui(self):
        """Настройка графического интерфейса"""
        self.output_text = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            width=100,
            height=30,
            bg='black',
            fg='#00FF00',
            font=('Courier New', 12),
            insertbackground='#00FF00'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Получаем текущий путь из VFS для промпта
        username = os.getlogin()
        hostname = socket.gethostname()
        current_dir = self.command_handler.vfs.get_current_path_str()
        self.display_output(f"Terminal emulator v1.0\nType 'help' for available commands.\n\n{username}@{hostname}:{current_dir}$ ")

        self.output_text.see(tk.END)
        self.input_start = self.output_text.index("end-1c")
        
        # Привязываем обработчики событий клавиш
        self.output_text.bind('<Key>', self.on_key)
        self.output_text.bind('<BackSpace>', self.on_backspace)
        self.output_text.bind('<Return>', self.on_enter)
        self.output_text.bind('<Delete>', self.on_delete)
        
        self.output_text.focus_set()
        self.output_text.mark_set(tk.INSERT, tk.END)

    def display_output(self, text):
        """Универсальный метод для вывода текста"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    def execute_startup_script(self):
        """Выполнение стартового скрипта"""
        executed_commands, errors = self.command_handler.execute_script(self.startup_script)
        
        # Обрабатываем ошибки выполнения скрипта
        if errors:
            for error in errors:
                self.display_output(f"\nОшибка скрипта: {error}")
        
        # Имитируем выполнение команд для отображения в интерфейсе
        for command in executed_commands:
            username = os.getlogin()
            hostname = socket.gethostname()
            current_dir = self.command_handler.vfs.get_current_path_str()
            prompt = f"{username}@{hostname}:{current_dir}$"
            self.display_output(f"\n{prompt} {command}")
            
            result = self.command_handler.execute(command)
            if result and result != "EXIT_TERMINAL":
                self.display_output(f"\n{result}")
            
            self.output_text.update()

    def on_key(self, event):
        """Обработчик нажатия клавиш с символами"""
        current_pos = self.output_text.index(tk.INSERT)
        
        if self.output_text.compare(current_pos, "<", self.input_start):
            self.output_text.mark_set(tk.INSERT, tk.END)
            return "break"
        
        if event.char and event.char.isprintable():
            self.output_text.insert(tk.INSERT, event.char)
        
        return "break"

    def on_backspace(self, event):
        """Обработчик клавиши Backspace"""
        current_pos = self.output_text.index(tk.INSERT)
        
        if self.output_text.compare(current_pos, "<=", self.input_start):
            return "break"
        
        if self.output_text.compare(current_pos, ">", "1.0"):
            self.output_text.delete("insert-1c", tk.INSERT)
        
        return "break"

    def on_delete(self, event):
        """Обработчик клавиши Delete"""
        current_pos = self.output_text.index(tk.INSERT)
        
        if self.output_text.compare(current_pos, "<", self.input_start):
            return "break"
        
        if self.output_text.compare(tk.INSERT, "<", tk.END):
            self.output_text.delete(tk.INSERT, "insert+1c")
        
        return "break"

    def on_enter(self, event):
        """Обработчик клавиши Enter"""
        command_line = self.output_text.get(self.input_start, tk.END).strip()
        
        username = os.getlogin()
        hostname = socket.gethostname()
        current_dir = self.command_handler.vfs.get_current_path_str()
        prompt = f"{username}@{hostname}:{current_dir}$"
        
        if command_line.startswith(prompt):
            command = command_line[len(prompt):].strip()
        else:
            command = command_line
        
        result = self.command_handler.execute(command)
        
        if result == "EXIT_TERMINAL":
            self.root.quit()
            return "break"
        
        if result:
            self.output_text.insert(tk.END, f"\n{result}")
        
        # Обновляем промпт с учётом возможного изменения директории (например, после cd)
        new_current_dir = self.command_handler.vfs.get_current_path_str()
        new_prompt = f"{username}@{hostname}:{new_current_dir}$"
        self.output_text.insert(tk.END, f"\n{new_prompt} ")
        self.input_start = self.output_text.index("end-1c")
        self.output_text.mark_set(tk.INSERT, tk.END)
        self.output_text.see(tk.END)
        return "break"
    
    def run(self):
        """Запуск главного цикла обработки событий"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ShellEmulator()
    app.run()