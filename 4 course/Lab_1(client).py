import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

# Параметры клиента
HOST = '127.0.0.1'  # IP-адрес сервера
PORT = 65432           # Порт, который использует сервер

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Клиент")

        # Создание текстовой области для отображения сообщений
        self.chat_window = scrolledtext.ScrolledText(self.root, state='disabled', width=50, height=20)
        self.chat_window.grid(row=0, column=0, padx=10, pady=10)

        # Настройка тегов для окраски текста
        self.chat_window.tag_configure("server", foreground="red")    # Слово "Сервер" - красное
        self.chat_window.tag_configure("client", foreground="blue")   # Слово "Клиент" - синее
        self.chat_window.tag_configure("info", foreground="green")    # Уведомления - зелёные

        # Поле ввода для сообщений
        self.message_entry = tk.Entry(self.root, width=40)
        self.message_entry.grid(row=1, column=0, padx=10, pady=5)
        self.message_entry.bind("<Return>", self.send_message)

        # Кнопка отправки
        self.send_button = tk.Button(self.root, text="Отправить", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=10, pady=5)

        self.client_socket = None

        # Подключение к серверу в отдельном потоке
        self.connect_to_server()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            self.chat_window.configure(state='normal')
            self.chat_window.insert(tk.END, f"Подключено к серверу {HOST}:{PORT}\n", "info")
            self.chat_window.configure(state='disabled')
            threading.Thread(target=self.receive_message, daemon=True).start()
        except Exception as e:
            self.chat_window.configure(state='normal')
            self.chat_window.insert(tk.END, f"Ошибка подключения: {e}\n", "info")
            self.chat_window.configure(state='disabled')

    def receive_message(self):
        while True:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                message = data.decode()
                self.chat_window.configure(state='normal')
                self.chat_window.insert(tk.END, "Сервер: ", "server")  # Окрашиваем слово "Сервер"
                self.chat_window.insert(tk.END, f"{message}\n")         # Обычное сообщение без цвета
                self.chat_window.configure(state='disabled')
            except Exception as e:
                self.chat_window.configure(state='normal')
                self.chat_window.insert(tk.END, f"Ошибка при получении данных: {e}\n", "info")
                self.chat_window.configure(state='disabled')
                break

    def send_message(self, event=None):
        message = self.message_entry.get()
        self.chat_window.configure(state='normal')
        self.chat_window.insert(tk.END, "Клиент: ", "client")  # Окрашиваем слово "Клиент"
        self.chat_window.insert(tk.END, f"{message}\n")         # Обычное сообщение без цвета
        self.chat_window.configure(state='disabled')
        self.client_socket.sendall(message.encode())
        self.message_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
