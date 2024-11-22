# bob.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import threading
from utils import BaseWindow, CryptoUtils, NetworkUtils, MessageHandler


class BobWindow(BaseWindow):
    def __init__(self):
        # Вызываем конструктор базового класса с именем и портом для сервера
        super().__init__("Bob", port=5005)

        # Дополнительные флаги состояния
        self.has_alice_key = False
        self.session_established = False
        self.alice_public_key = None
        self.alice_socket = None
        self.session_key = None

        # Инициализация специфичного для Боба интерфейса
        self.setup_bob_ui()

    def setup_bob_ui(self):
        """Настройка специфичного для Боба интерфейса"""
        # Размещаем элементы над логом (который уже создан в BaseWindow)

        # Кнопка подключения к Тренту
        self.connect_button = QPushButton('Подключиться к Тренту')
        self.connect_button.clicked.connect(self.connect_to_trent)
        self.layout.insertWidget(0, self.connect_button)

        # Кнопка запуска сервера
        self.start_server_button = QPushButton('Запустить сервер')
        self.start_server_button.clicked.connect(self.start_server)
        self.start_server_button.setEnabled(False)
        self.layout.insertWidget(1, self.start_server_button)

        # Кнопка запроса ключа Алисы
        self.request_alice_key = QPushButton('Запросить ключ Алисы')
        self.request_alice_key.clicked.connect(lambda: self.request_public_key("Alice"))
        self.request_alice_key.setEnabled(False)
        self.layout.insertWidget(2, self.request_alice_key)

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
        self.start_server_button.setEnabled(True)
        self.request_alice_key.setEnabled(True)
        self.connect_button.setEnabled(False)

    @pyqtSlot(str, object)
    def on_key_received(self, name, public_key):
        """Обработчик получения ключа"""
        if name == "Alice":
            self.alice_public_key = public_key
            self.has_alice_key = True
        super().on_key_received(name, public_key)

    def start_server(self):
        """Запуск сервера для приема подключений от Алисы"""
        self.start_server_button.setEnabled(False)
        self.status_label.setText('Статус: Ожидание подключения Алисы')

        # Запуск прослушивания в отдельном потоке
        self.server_thread = threading.Thread(target=self.accept_connections)
        self.server_thread.daemon = True
        self.server_thread.start()

        self.log_message("Сервер запущен")

    def accept_connections(self):
        """Обработка входящих подключений"""
        try:
            while True:
                client_socket, _ = self.server_socket.accept()
                self.alice_socket = client_socket

                # Уведомление о подключении
                QMetaObject.invokeMethod(
                    self,
                    "handle_alice_connected",
                    Qt.QueuedConnection
                )

                # Запуск обработки сообщений
                self.handle_alice_messages()

        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.QueuedConnection,
                Q_ARG(str, f"Ошибка принятия подключения: {str(e)}")
            )

    @pyqtSlot()
    def handle_alice_connected(self):
        """Обработчик подключения Алисы"""
        self.log_message("Алиса подключилась")
        self.status_label.setText('Статус: Алиса подключена')

    def handle_alice_messages(self):
        """Обработка сообщений от Алисы"""
        try:
            while True:
                data = NetworkUtils.receive_message(self.alice_socket)

                if 'encrypted_timestamp' in data:
                    # Обработка установки сеансового ключа
                    self.process_session_key_message(data)
                elif 'type' in data and data['type'] == 'message':
                    # Обработка зашифрованного сообщения
                    self.process_encrypted_message(data)

        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.QueuedConnection,
                Q_ARG(str, f"Ошибка обработки сообщения: {str(e)}")
            )

    def process_session_key_message(self, message):
        """Обработка сообщения с сеансовым ключом"""
        try:
            # Проверка и извлечение сеансового ключа
            self.session_key = MessageHandler.verify_session_key_message(
                message,
                self.private_key,
                self.alice_public_key
            )

            self.session_established = True

            # Обновление GUI
            QMetaObject.invokeMethod(
                self,
                "on_session_established",
                Qt.QueuedConnection
            )

        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.QueuedConnection,
                Q_ARG(str, f"Ошибка обработки сеансового ключа: {str(e)}")
            )

    @pyqtSlot()
    def on_session_established(self):
        """Обработчик установки сессии"""
        self.send_message.setEnabled(True)
        self.log_message("Сеансовый ключ успешно установлен")
        self.status_label.setText('Статус: Сессия установлена')

    def process_encrypted_message(self, data):
        """Обработка зашифрованного сообщения от Алисы"""
        try:
            if not self.session_established:
                raise Exception("Сессия не установлена")

            encrypted_message = data['content']
            message = CryptoUtils.decrypt_session_key(
                self.private_key,
                encrypted_message
            ).decode()

            QMetaObject.invokeMethod(
                self,
                "display_message",
                Qt.QueuedConnection,
                Q_ARG(str, f"Алиса: {message}")
            )

        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.QueuedConnection,
                Q_ARG(str, f"Ошибка расшифровки сообщения: {str(e)}")
            )

    @pyqtSlot(str)
    def display_message(self, message):
        """Отображение полученного сообщения"""
        self.log_message(message)

    def send_encrypted_message(self):
        """Отправка зашифрованного сообщения Алисе"""
        try:
            if not self.session_established:
                self.log_message("Сессия не установлена")
                return

            message = self.message_input.text()
            if not message:
                return

            # Шифрование сообщения сеансовым ключом
            encrypted_message = CryptoUtils.encrypt_session_key(
                self.alice_public_key,
                message.encode()
            )

            message_data = {
                'type': 'message',
                'content': encrypted_message
            }

            NetworkUtils.send_message(self.alice_socket, message_data)
            self.log_message(f"Отправлено: {message}")
            self.message_input.clear()

        except Exception as e:
            self.log_message(f"Ошибка отправки сообщения: {str(e)}")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            if self.alice_socket:
                self.alice_socket.close()
            if self.server_socket:
                self.server_socket.close()
            if self.trent_socket:
                self.trent_socket.close()
        except:
            pass
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BobWindow()
    window.show()
    sys.exit(app.exec_())