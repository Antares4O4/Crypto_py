# alice.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
from cryptography.hazmat.primitives import serialization
from utils import CryptoUtils, NetworkUtils, MessageHandler
import os
import time
import socket
import threading

class ThreadSafeSignal:
    def __init__(self, window):
        self.window = window

    def emit_log(self, message):
        QMetaObject.invokeMethod(
            self.window,
            "log_message",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, message)
        )

    def emit_clear_input(self):
        QMetaObject.invokeMethod(
            self.window.message_input,
            "clear",
            Qt.ConnectionType.QueuedConnection
        )

    def emit_enable_button(self, button, enabled):
        QMetaObject.invokeMethod(
            button,
            "setEnabled",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(bool, enabled)
        )

class AliceWindow(QMainWindow):
    # Добавляем сигналы для обновления GUI из другого потока
    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal(str)
    key_exchange_successful = pyqtSignal()
    key_exchange_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.title = "Alice"
        self.signals = ThreadSafeSignal(self)  # Добавляем объект для безопасных сигналов
        self.my_port = 5001
        self.bob_port = 5002
        self.trent_port = 5000
        self.session_key = os.urandom(32)
        self.session_established = False
        self.has_bob_key = False

        self.initUI()
        self.init_crypto()
        self.init_network()

        # Инициализация таймера
        self.check_timer = QTimer()
        self.check_timer.setInterval(100)
        self.check_timer.timeout.connect(self.check_messages)

        # Подключение сигналов
        self.connection_successful.connect(self._on_connection_successful)
        self.connection_failed.connect(self._on_connection_failed)
        self.key_exchange_successful.connect(self._on_key_exchange_successful)
        self.key_exchange_failed.connect(self._on_key_exchange_failed)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 400, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Кнопки и элементы управления
        self.connect_button = QPushButton('Подключиться к Тренту')
        self.connect_button.clicked.connect(self.connect_to_trent)
        self.layout.addWidget(self.connect_button)

        self.request_bob_key = QPushButton('Запросить ключ Боба')
        self.request_bob_key.clicked.connect(self.request_public_key)
        self.request_bob_key.setEnabled(False)
        self.layout.addWidget(self.request_bob_key)

        self.send_session_key = QPushButton('Отправить сеансовый ключ')
        self.send_session_key.clicked.connect(self.send_session_key_to_bob)
        self.send_session_key.setEnabled(False)
        self.layout.addWidget(self.send_session_key)

        self.message_input = QLineEdit()
        self.layout.addWidget(self.message_input)

        self.send_message = QPushButton('Отправить сообщение')
        self.send_message.clicked.connect(self.send_encrypted_message)
        self.send_message.setEnabled(False)
        self.layout.addWidget(self.send_message)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        self.status_label = QLabel('Статус: Не подключено')
        self.layout.addWidget(self.status_label)

    def init_crypto(self):
        self.private_key, self.public_key = CryptoUtils.generate_key_pair()
        self.trent_public_key = None

    def init_network(self):
        self.trent_socket = None
        self.bob_socket = None

    def log_message(self, message):
        current_time = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{current_time}] {message}")

    def connect_to_trent(self):
        try:
            self.trent_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.trent_socket.settimeout(5)  # таймаут 5 секунд
            self.trent_socket.connect(('localhost', 5000))

            public_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            registration_data = {
                'type': 'register',
                'name': 'Alice',
                'public_key': public_bytes.decode()
            }

            NetworkUtils.send_message(self.trent_socket, registration_data)
            response = NetworkUtils.receive_message(self.trent_socket)

            if response.get('status') == 'success':
                self.trent_public_key = serialization.load_pem_public_key(
                    response['public_key'].encode()
                )
                self.status_label.setText('Статус: Подключено к Тренту')
                self.log_message("Успешное подключение к Тренту")
                self.connect_button.setEnabled(False)
                self.request_bob_key.setEnabled(True)
            else:
                error_msg = response.get('message', 'Неизвестная ошибка')
                self.log_message(f"Ошибка при регистрации у Трента: {error_msg}")

        except socket.timeout:
            self.log_message("Таймаут при подключении к Тренту")
        except Exception as e:
            self.log_message(f"Ошибка подключения: {str(e)}")
            self.status_label.setText('Статус: Ошибка подключения')

    def request_public_key(self):
        """Запрос открытого ключа Боба"""
        try:
            if not self.trent_socket:
                self.log_message("Нет подключения к Тренту")
                return None

            # Временно переключаем сокет в блокирующий режим
            self.trent_socket.setblocking(True)

            request_data = {
                'type': 'request_key',
                'name': 'Bob'
            }

            self.log_message("Отправка запроса ключа Боба")
            NetworkUtils.send_message(self.trent_socket, request_data)

            self.log_message("Ожидание ответа от Трента")
            response = NetworkUtils.receive_message(self.trent_socket)

            # Возвращаем сокет в неблокирующий режим
            self.trent_socket.setblocking(False)

            if response.get('status') == 'success':
                # Получаем данные из ответа
                public_key_str = response['public_key']
                signature = bytes.fromhex(response['signature'])
                signed_data = response['signed_data']

                # Проверяем подпись
                self.log_message("Проверка подписи Трента...")
                if CryptoUtils.verify_signature(self.trent_public_key, signed_data, signature):
                    self.log_message("Подпись Трента верна")

                    # Преобразуем ключ
                    self.bob_public_key = serialization.load_pem_public_key(
                        public_key_str.encode()
                    )
                    self.has_bob_key = True

                    # Подключаемся к Бобу
                    self.connect_to_bob()

                    return self.bob_public_key
                else:
                    self.log_message("Ошибка проверки подписи")
                    return None
        except Exception as e:
            self.log_message(f"Ошибка запроса ключа: {str(e)}")
            return None

    def handle_connection_loss(self):
        """Добавляем новый метод для обработки потери соединения"""
        if self.bob_socket:
            try:
                self.bob_socket.close()
            except:
                pass
            self.bob_socket = None

        self.check_timer.stop()
        self.session_established = False
        self.send_message.setEnabled(False)
        self.send_session_key.setEnabled(True)
        self.status_label.setText('Статус: Соединение потеряно')

    def connect_to_bob(self):
        """Запуск подключения к Бобу в отдельном потоке"""
        self.send_session_key.setEnabled(False)
        self.status_label.setText('Статус: Подключение к Бобу...')

        # Создаем и запускаем поток подключения
        connection_thread = threading.Thread(target=self._connect_to_bob_thread)
        connection_thread.daemon = True
        connection_thread.start()

    def _connect_to_bob_thread(self):
        """Фоновый процесс подключения к Бобу"""
        try:
            self.bob_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.bob_socket.settimeout(5)
            self.bob_socket.connect(('localhost', self.bob_port))
            self.bob_socket.setblocking(False)

            # Сигнализируем об успешном подключении
            self.connection_successful.emit()

        except Exception as e:
            self.connection_failed.emit(str(e))
            if self.bob_socket:
                try:
                    self.bob_socket.close()
                except:
                    pass
                self.bob_socket = None

    @pyqtSlot()
    def _on_connection_successful(self):
        """Обработчик успешного подключения"""
        self.log_message("Установлено соединение с Бобом")
        self.status_label.setText('Статус: Подключено к Бобу')
        self.send_session_key.setEnabled(True)
        self.check_timer.start()

    @pyqtSlot(str)
    def _on_connection_failed(self, error):
        """Обработчик неудачного подключения"""
        self.log_message(f"Ошибка подключения к Бобу: {error}")
        self.status_label.setText('Статус: Ошибка подключения к Бобу')
        self.send_session_key.setEnabled(False)

    def send_session_key_to_bob(self):
        """Запуск отправки сеансового ключа в отдельном потоке"""
        self.send_session_key.setEnabled(False)
        self.status_label.setText('Статус: Отправка сеансового ключа...')

        # Создаем и запускаем поток отправки ключа
        key_exchange_thread = threading.Thread(target=self._send_session_key_thread)
        key_exchange_thread.daemon = True
        key_exchange_thread.start()

    def _send_session_key_thread(self):
        """Фоновый процесс отправки сеансового ключа"""
        try:
            if not self.has_bob_key or not self.bob_socket:
                raise Exception("Нет подключения к Бобу или отсутствует его ключ")

            temp_private_key, temp_public_key = CryptoUtils.generate_key_pair()
            timestamp = str(int(time.time()))
            lifetime = "3600"

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

            # Временно делаем сокет блокирующим для отправки
            self.bob_socket.setblocking(True)
            NetworkUtils.send_message(self.bob_socket, message)
            self.bob_socket.setblocking(False)

            self.key_exchange_successful.emit()

        except Exception as e:
            self.key_exchange_failed.emit(str(e))

    @pyqtSlot()
    def _on_key_exchange_successful(self):
        """Обработчик успешной отправки ключа"""
        self.session_established = True
        self.send_message.setEnabled(True)
        self.send_session_key.setEnabled(False)
        self.status_label.setText('Статус: Сессия установлена')
        self.log_message("Сеансовый ключ отправлен Бобу")

    @pyqtSlot(str)
    def _on_key_exchange_failed(self, error):
        """Обработчик неудачной отправки ключа"""
        self.log_message(f"Ошибка отправки сеансового ключа: {error}")
        self.handle_connection_loss()

    def check_messages(self):
        """Проверка новых сообщений от Боба"""
        if not self.bob_socket:
            return

        try:
            message = NetworkUtils.receive_message(self.bob_socket)
            if message and isinstance(message, dict):
                if message.get('type') == 'message':
                    try:
                        decrypted_message = CryptoUtils.decrypt_session_key(
                            self.private_key,
                            message['content']
                        ).decode()
                        self.log_message(f"Боб: {decrypted_message}")
                    except Exception as e:
                        self.log_message(f"Ошибка расшифровки сообщения: {str(e)}")
        except BlockingIOError:
            # Нормальная ситуация для неблокирующего сокета
            pass
        except ConnectionError as e:
            self.log_message("Соединение с Бобом потеряно")
            self.handle_connection_loss()
        except Exception as e:
            if "Соединение разорвано" in str(e):
                self.log_message("Соединение с Бобом потеряно")
                self.handle_connection_loss()
            else:
                self.log_message(f"Ошибка приема сообщения: {str(e)}")

    def send_encrypted_message(self):
        """Отправка зашифрованного сообщения"""
        try:
            if not self.session_established or not self.bob_socket:
                self.log_message("Сессия не установлена или отсутствует соединение")
                return

            message = self.message_input.text()
            if not message:
                return

            # Запускаем отправку в отдельном потоке
            send_thread = threading.Thread(
                target=self._send_message_thread,
                args=(message,)
            )
            send_thread.daemon = True
            send_thread.start()

        except Exception as e:
            self.log_message(f"Ошибка отправки сообщения: {str(e)}")

    def _send_message_thread(self, message):
        """Фоновый процесс отправки сообщения"""
        try:
            encrypted_message = CryptoUtils.encrypt_session_key(
                self.bob_public_key,
                message.encode()
            )

            message_data = {
                'type': 'message',
                'content': encrypted_message
            }

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
                temp_socket.connect(('localhost', self.bob_port))
                NetworkUtils.send_message(temp_socket, message_data)

            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, f"Отправлено: {message}")
            )

            QMetaObject.invokeMethod(
                self.message_input,
                "clear",
                Qt.ConnectionType.QueuedConnection
            )

        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, f"Ошибка отправки сообщения: {str(e)}")
            )

    def closeEvent(self, event):
        self.check_timer.stop()
        if self.bob_socket:
            self.bob_socket.close()
        if self.trent_socket:
            self.trent_socket.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AliceWindow()
    window.show()
    sys.exit(app.exec_())
