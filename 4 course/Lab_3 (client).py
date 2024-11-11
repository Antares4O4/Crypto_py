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


# Клиентское приложение
class ClientApp:
    def __init__(self, root, host='192.168.1.34', port=65432):
        self.root = root
        self.root.title("Клиент")
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
        self.message_entry.bind("<Return>", self.send_message)
        self.send_button = tk.Button(self.root, text="Отправить", command=self.send_message)
        self.send_button.grid(row=1, column=1, padx=10, pady=5)

        # Подключение к серверу
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

        # Обмен открытыми ключами
        self.client_socket.send(self.public_key.save_pkcs1())
        server_key_data = self.client_socket.recv(4096)
        self.server_public_key = rsa.PublicKey.load_pkcs1(server_key_data)

        threading.Thread(target=self.receive_message, daemon=True).start()

    def receive_message(self):
        while True:
            try:
                encrypted_message = self.client_socket.recv(4096).decode()
                if encrypted_message:
                    self.display_message("Зашифрованное сообщение", encrypted_message, "encrypted_tag")
                    decrypted_message = decrypt_message(self.private_key, encrypted_message)
                    self.display_message("Сервер", decrypted_message, "server_tag")
            except Exception as e:
                self.display_message("Клиент", f"Ошибка: {e}", "client_tag")
                break

    def send_message(self, event=None):
        message = self.message_entry.get()
        if self.server_public_key:
            try:
                encrypted_message = encrypt_message(self.server_public_key, message)
                self.display_message("Зашифрованное сообщение", encrypted_message, "encrypted_tag")
                self.client_socket.send(encrypted_message.encode())
                self.display_message("Вы", message, "self_tag")
            except Exception as e:
                self.display_message("Клиент", f"Ошибка при отправке: {e}", "client_tag")
        self.message_entry.delete(0, tk.END)

    def display_message(self, label, message, tag):
        self.chat_window.configure(state='normal')
        self.chat_window.insert(tk.END, f"{label}: ", tag)
        self.chat_window.insert(tk.END, f"{message}\n", "normal")
        self.chat_window.configure(state='disabled')
        self.chat_window.yview(tk.END)


# Запуск клиента
if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
