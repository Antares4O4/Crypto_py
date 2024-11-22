# alice.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
from utils import BaseWindow, CryptoUtils, NetworkUtils, MessageHandler
import os
import time
import threading
import socket


class AliceWindow(BaseWindow):
    def __init__(self):
        super().__init__("Alice")

        # Дополнительные флаги состояния
        self.has_bob_key = False
        self.session_established = False
        self.bob_public_key = None
        self.bob_socket = None

        # Инициализация сеансового ключа
        self.session_key = os.urandom(32)

        # Добавление специфичных для Алисы элементов интерфейса
        self.setup_alice_ui()

    def setup_alice_ui(self):
        """Настройка специфичного для Алисы интерфейса"""
        # Размещаем элементы над логом (который уже создан в BaseWindow)

        # Кнопка подключения к Тренту
        self.connect_button = QPushButton('Подключиться к Тренту')
        self.connect_button.clicked.connect(self.connect_to_trent)
        self.layout.insertWidget(0, self.connect_button)

        # Кнопка запроса ключа Боба
        self.request_bob_key = QPushButton('Запросить ключ Боба')
        self.request_bob_key.clicked.connect(lambda: self.request_public_key("Bob"))
        self.request_bob_key.setEnabled(False)
        self.layout.insertWidget(1, self.request_bob_key)

        # Кнопка отправки сеансового ключа
        self.send_session_key = QPushButton('Отправить сеансовый ключ')
        self.send_session_key.clicked.connect(self.send_session_key_to_bob)
        self.send_session_key.setEnabled(False)
        self.layout.insertWidget(2, self.send_session_key)

        # Группа для отправки сообщений
        message_group = QGroupBox("Отправка сообщений")
        message_layout = QVBoxLayout()

        self.message_input = QLineEdit()
        message_layout.addWidget(self.message_input)

        self.send_message = QPushButton('Отправить сообщение')
        self.send_message.clicked.connect(self.send_encrypted_message)
        self.send_message.setEnabled(False)
        message_layout.addWidget(self.send_message)

        message_group.setLayout(message_layout)
        self.layout.insertWidget(3, message_group)

    def on_trent_connected(self):
        """Обработчик успешного подключения к Тренту"""
        self.request_bob_key.setEnabled(True)
        self.connect_button.setEnabled(False)

    @pyqtSlot(str, object)
    def on_key_received(self, name, public_key):
        """Обработчик получения ключа"""
        if name == "Bob":
            self.bob_public_key = public_key
            self.has_bob_key = True
            self.send_session_key.setEnabled(True)
            self.connect_to_bob()
        super().on_key_received(name, public_key)

    def connect_to_bob(self):
        """Подключение к Бобу"""
        try:
            self.bob_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.bob_socket.connect(('localhost', 5005))
            self.log_message("Установлено соединение с Бобом")
        except Exception as e:
            self.log_message(f"Ошибка подключения к Бобу: {str(e)}")

    def send_session_key_to_bob(self):
        """Отправка сеансового ключа Бобу"""
        try:
            if not self.has_bob_key or not self.bob_socket:
                self.log_message("Нет подключения к Бобу или его открытого ключа")
                return

            # Создание временной пары ключей
            temp_private_key, temp_public_key = CryptoUtils.generate_key_pair()

            # Подготовка данных для сообщения
            timestamp = str(int(time.time()))
            lifetime = "3600"  # время жизни сессии в секундах

            # Создание сообщения с сеансовым ключом
            message = MessageHandler.create_session_key_message(
                self.session_key,
                timestamp,
                lifetime,
                "Alice",
                temp_private_key,
                temp_public_key,
                self.private_key,
                self.bob_public_key
            )

            NetworkUtils.send_message(self.bob_socket, message)
            self.session_established = True
            self.send_message.setEnabled(True)
            self.send_session_key.setEnabled(False)
            self.log_message("Сеансовый ключ отправлен Бобу")

            # Запуск прослушивания ответов от Боба
            self.start_listening()

        except Exception as e:
            self.log_message(f"Ошибка отправки сеансового ключа: {str(e)}")

    def start_listening(self):
        """Запуск прослушивания сообщений от Боба"""
        self.listener_thread = threading.Thread(target=self.listen_for_messages)
        self.listener_thread.daemon = True
        self.listener_thread.start()

    def listen_for_messages(self):
        """Прослушивание сообщений от Боба"""
        try:
            while True:
                message = NetworkUtils.receive_message(self.bob_socket)
                if message.get('type') == 'message':
                    decrypted_message = CryptoUtils.decrypt_session_key(
                        self.private_key,
                        message['content']
                    ).decode()

                    QMetaObject.invokeMethod(
                        self,
                        "display_message",
                        Qt.QueuedConnection,
                        Q_ARG(str, f"Боб: {decrypted_message}")
                    )
        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.QueuedConnection,
                Q_ARG(str, f"Ошибка приема сообщений: {str(e)}")
            )

    @pyqtSlot(str)
    def display_message(self, message):
        """Отображение полученного сообщения"""
        self.log_message(message)

    def send_encrypted_message(self):
        """Отправка зашифрованного сообщения Бобу"""
        try:
            if not self.session_established:
                self.log_message("Сессия не установлена")
                return

            message = self.message_input.text()
            if not message:
                return

            # Шифрование сообщения сеансовым ключом
            encrypted_message = CryptoUtils.encrypt_session_key(
                self.bob_public_key,
                message.encode()
            )

            message_data = {
                'type': 'message',
                'content': encrypted_message
            }

            NetworkUtils.send_message(self.bob_socket, message_data)
            self.log_message(f"Отправлено: {message}")
            self.message_input.clear()

        except Exception as e:
            self.log_message(f"Ошибка отправки сообщения: {str(e)}")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            if self.bob_socket:
                self.bob_socket.close()
            if self.trent_socket:
                self.trent_socket.close()
        except:
            pass
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AliceWindow()
    window.show()
    sys.exit(app.exec_())