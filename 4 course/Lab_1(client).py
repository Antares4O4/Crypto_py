import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# Настройки
HOST = '127.0.0.1'
PORT = 12345

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Client")
        self.client_socket = None

        # Интерфейс
        self.create_widgets()

    def create_widgets(self):
        # Окно чата
        self.chat_box = scrolledtext.ScrolledText(self.root, state='disabled', width=50, height=20)
        self.chat_box.pack(padx=10, pady=10)

        # Поле для ввода сообщений
        self.entry_field = tk.Entry(self.root, width=40)
        self.entry_field.pack(side=tk.LEFT, padx=10, pady=10)
        self.entry_field.bind('<Return>', self.send_message)

        # Кнопка для отправки сообщений
        self.send_button = tk.Button(self.root, text="Отправить", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Подключение к серверу
        threading.Thread(target=self.start_client, daemon=True).start()

    def start_client(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
            self.append_message(f"Подключен к серверу {HOST}:{PORT}")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except ConnectionRefusedError:
            messagebox.showerror("Ошибка", "Не удалось подключиться к серверу.")

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                self.append_message(f"Сервер: {message}")
            except ConnectionResetError:
                self.append_message("Соединение разорвано.")
                break

    def send_message(self, event=None):
        message = self.entry_field.get()
        if not message:
            return
        self.client_socket.send(message.encode())
        self.append_message(f"Вы: {message}")
        self.entry_field.delete(0, tk.END)

        if message.lower() == 'exit':
            self.root.quit()

    def append_message(self, message):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, message + '\n')
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
