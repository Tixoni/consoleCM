import tkinter as tk
from tkinter import scrolledtext
from handlers import CommandHandler
import os
import socket

class ShellEmulator:
    def __init__(self):
        # Создаем главное окно приложения
        self.root = tk.Tk()
        
        # Заголовок окна на основе реальных данных ОС
        username = os.getlogin()
        hostname = socket.gethostname()
        self.root.title(f"Эмулятор - [{username}@{hostname}]")
        
        self.root.geometry("800x600")      
        
        # Инициализируем обработчик команд
        self.command_handler = CommandHandler()
        
        # Создаем текстовое поле с прокруткой 
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
        
        # Добавляем начальное приветственное сообщение и первый промпт
        username = os.getlogin()
        hostname = socket.gethostname()
        self.output_text.insert(tk.END, f"Terminal emulator v1.0\nType 'help' for available commands.\nHOME = USERPROFILE\n\n{username}@{hostname}:~$ ")

        self.output_text.see(tk.END)
        self.input_start = self.output_text.index("end-1c")
        
        # Привязываем обработчики событий клавиш
        self.output_text.bind('<Key>', self.on_key)
        self.output_text.bind('<BackSpace>', self.on_backspace)
        self.output_text.bind('<Return>', self.on_enter)
        self.output_text.bind('<Delete>', self.on_delete)
        
        self.output_text.focus_set()
        self.output_text.mark_set(tk.INSERT, tk.END)

    def on_key(self, event):
        #Обработчик нажатия клавиш с символами
        current_pos = self.output_text.index(tk.INSERT)
        
        if self.output_text.compare(current_pos, "<", self.input_start):
            self.output_text.mark_set(tk.INSERT, tk.END)
            return "break"
        
        if event.char and event.char.isprintable():
            self.output_text.insert(tk.INSERT, event.char)
        
        return "break"

    def on_backspace(self, event):
        #Обработчик клавиши Backspace
        current_pos = self.output_text.index(tk.INSERT)
        
        if self.output_text.compare(current_pos, "<=", self.input_start):
            return "break"
        
        if self.output_text.compare(current_pos, ">", "1.0"):
            self.output_text.delete("insert-1c", tk.INSERT)
        
        return "break"

    def on_delete(self, event):
        #Обработчик клавиши Delete
        current_pos = self.output_text.index(tk.INSERT)
        
        if self.output_text.compare(current_pos, "<", self.input_start):
            return "break"
        
        if self.output_text.compare(tk.INSERT, "<", tk.END):
            self.output_text.delete(tk.INSERT, "insert+1c")
        
        return "break"






    #Обработчик клавиши Enter
    def on_enter(self, event):
        

        #берет команду и убирает лишние пробелы по краям
        command_line = self.output_text.get(self.input_start, tk.END).strip()
        
        #для промпта
        username = os.getlogin()
        hostname = socket.gethostname()
        prompt = f"{username}@{hostname}:~$"
        
        #на всякий 
        if command_line.startswith(prompt):
            command = command_line[len(prompt):].strip()
        else:
            command = command_line
        
        # ---------------------------------------------Передаем ВСЮ обработку в command_handler
        result = self.command_handler.execute(command)
        
        # Обрабатываем специальные сигналы
        if result == "EXIT_TERMINAL":
            self.root.quit()
            return "break"
        
        
        # Добавляем вывод результата
        if result:
            self.output_text.insert(tk.END, f"\n{result}")
        
        # Добавляем новый промпт
        self.output_text.insert(tk.END, f"{prompt} ")
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