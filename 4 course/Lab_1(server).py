import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

# Параметры сервера
HOST = '127.0.0.1'  # Сервер будет слушать на всех доступных интерфейсах
PORT = 65432      # Порт, который использует сервер

clients = []  # Список подключенных клиентов

class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Сервер Чата")

        # Создание текстовой области для отображения сообщений
        self.chat_window = scrolledtext.ScrolledText(self.root, state='disabled', width=50, height=20)
        self.chat_window.grid(row=0, column=0, padx=10, pady=10)

        # Настройка тегов для окраски текста
        self.chat_window.tag_configure("server", foreground="red")    # Слово "Сервер" - красное
        self.chat_window.tag_configure("client", foreground="blue")   # Слово "Клиент" - синее
        self.chat_window.tag_configure("info", foreground="green")    # Уведомления - зелёные

        # Поле ввода для сообщений от сервера
        self.server_message_entry = tk.Entry(self.root, width=40)
        self.server_message_entry.grid(row=1, column=0, padx=10, pady=5)
        self.server_message_entry.bind("<Return>", self.send_message_to_clients)

        # Кнопка отправки сообщения от сервера
        self.send_button = tk.Button(self.root, text="Отправить всем", command=self.send_message_to_clients)
        self.send_button.grid(row=1, column=1, padx=10, pady=5)

        # Запуск сервера в отдельном потоке
        threading.Thread(target=self.start_server, daemon=True).start()

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        self.log_message(f"[ЗАПУСК] Сервер запущен и слушает на {HOST}:{PORT}\n", "info")

        while True:
            client_socket, client_address = server_socket.accept()
            clients.append(client_socket)
            self.log_message(f"[ПОДКЛЮЧЕНО] Новый клиент: {client_address}\n", "info")
            threading.Thread(target=self.handle_client, args=(client_socket, client_address), daemon=True).start()

    def handle_client(self, client_socket, client_address):
        client_socket.sendall("Вы подключены к серверу.\n".encode())

        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                message_decoded = message.decode()
                self.log_message(f"[ОТ {client_address}] Клиент: {message_decoded}\n", "client")

                # Отправка сообщения обратно клиенту
                response = f"Сервер получил: {message_decoded}"
                client_socket.sendall(response.encode())
            except Exception as e:
                self.log_message(f"[ОШИБКА] Произошла ошибка: {e}\n", "info")
                break

        self.log_message(f"[ОТКЛЮЧЕНО] Клиент отключён: {client_address}\n", "info")
        clients.remove(client_socket)
        client_socket.close()

    def send_message_to_clients(self, event=None):
        message = self.server_message_entry.get()
        if message:
            self.log_message(f"[СОБЩЕНИЕ] Сервер: {message}\n", "server")
            for client in clients:
                try:
                    client.sendall(f"Сервер: {message}\n".encode())
                except Exception as e:
                    self.log_message(f"[ОШИБКА] Не удалось отправить сообщение: {e}\n", "info")
            self.server_message_entry.delete(0, tk.END)

    def log_message(self, message, tag):
        self.chat_window.configure(state='normal')
        self.chat_window.insert(tk.END, message, tag)
        self.chat_window.configure(state='disabled')
        self.chat_window.yview(tk.END)  # Прокрутка вниз

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()
