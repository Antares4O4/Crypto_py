import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import rsa
import base64


# Функции шифрования и расшифровки
def encrypt_message(public_key, message):
    encrypted_message = rsa.encrypt(message.encode(), public_key)
    return base64.b64encode(encrypted_message).decode()


def decrypt_message(private_key, encrypted_message):
    decoded_message = base64.b64decode(encrypted_message)
    return rsa.decrypt(decoded_message, private_key).decode()


# Серверное приложение
class ServerApp:
    def __init__(self, root, host='127.0.0.1', port=65432):
        self.root = root
        self.root.title("Сервер")
        self.host, self.port = host, port

        # Генерация пары ключей
        self.public_key, self.private_key = rsa.newkeys(512)

        # GUI элементы
        self.chat_window = scrolledtext.ScrolledText(self.root, state='disabled', width=50, height=20)
        self.chat_window.grid(row=0, column=0, padx=10, pady=10)
        self.chat_window.tag_configure("server_tag", foreground="blue")
        self.chat_window.tag_configure("client_tag", foreground="green")
        self.chat_window.tag_configure("self_tag", foreground="purple")
        self.chat_window.tag_configure("encrypted_tag", foreground="gray")  # Серый цвет для зашифрованного текста

        self.message_entry = tk.Entry(self.root, width=40)
        self.message_entry.grid(row=1, column=0, padx=10, pady=5)
        self.message_entry.bind("<Return>", self.send_message_to_client)
        self.send_button = tk.Button(self.root, text="Отправить", command=self.send_message_to_client)
        self.send_button.grid(row=1, column=1, padx=10, pady=5)

        # Настройка сервера
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.display_message("Сервер", "Ожидание подключения...", "server_tag")

        threading.Thread(target=self.accept_client, daemon=True).start()

    def accept_client(self):
        self.client_socket, addr = self.server_socket.accept()
        self.display_message("Сервер", f"Клиент подключился: {addr}", "server_tag")

        # Получение открытого ключа клиента
        client_key_data = self.client_socket.recv(4096)
        self.client_public_key = rsa.PublicKey.load_pkcs1(client_key_data)

        # Отправка открытого ключа сервера
        self.client_socket.send(self.public_key.save_pkcs1())

        threading.Thread(target=self.receive_message, daemon=True).start()

    def receive_message(self):
        while True:
            try:
                encrypted_message = self.client_socket.recv(4096).decode()
                if encrypted_message:
                    self.display_message("Зашифрованное сообщение", encrypted_message, "encrypted_tag")
                    decrypted_message = decrypt_message(self.private_key, encrypted_message)
                    self.display_message("Клиент", decrypted_message, "client_tag")
            except Exception as e:
                self.display_message("Сервер", f"Ошибка: {e}", "server_tag")
                break

    def send_message_to_client(self, event=None):
        message = self.message_entry.get()
        if self.client_public_key:
            try:
                encrypted_message = encrypt_message(self.client_public_key, message)
                self.display_message("Зашифрованное сообщение", encrypted_message, "encrypted_tag")
                self.client_socket.send(encrypted_message.encode())
                self.display_message("Вы", message, "self_tag")
            except Exception as e:
                self.display_message("Сервер", f"Ошибка при отправке: {e}", "server_tag")
        self.message_entry.delete(0, tk.END)

    def display_message(self, label, message, tag):
        self.chat_window.configure(state='normal')
        self.chat_window.insert(tk.END, f"{label}: ", tag)
        self.chat_window.insert(tk.END, f"{message}\n", "normal")
        self.chat_window.configure(state='disabled')
        self.chat_window.yview(tk.END)


# Запуск сервера
if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()
