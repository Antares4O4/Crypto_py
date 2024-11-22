# trent.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import socket
import time
from utils import CryptoUtils, NetworkUtils
from cryptography.hazmat.primitives import serialization


class TrentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.init_crypto()
        self.init_network()
        self.clients = {}
        self.is_running = False

    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle('Трент')
        self.setGeometry(100, 100, 400, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создание элементов интерфейса
        self.start_button = QPushButton('Запустить сервер')
        self.start_button.clicked.connect(self.toggle_server)
        layout.addWidget(self.start_button)

        # Лог сообщений
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.status_label = QLabel('Статус: Сервер остановлен')
        layout.addWidget(self.status_label)

    def init_crypto(self):
        """Инициализация криптографических ключей"""
        self.private_key, self.public_key = CryptoUtils.generate_key_pair()

    def init_network(self):
        """Инициализация сетевого соединения"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', 5002))
        self.server_socket.listen(5)

    def log_message(self, message):
        """Добавление сообщения в лог"""
        current_time = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{current_time}] {message}")

    def toggle_server(self):
        """Переключение состояния сервера"""
        if not self.is_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        """Запуск сервера"""
        try:
            self.is_running = True
            self.start_button.setText('Остановить сервер')
            self.status_label.setText('Статус: Сервер запущен')
            self.log_message("Сервер запущен")

            # Запуск обработки подключений в отдельном потоке
            self.server_thread = ServerThread(self.server_socket, self)
            self.server_thread.message_received.connect(self.log_message)
            self.server_thread.start()

        except Exception as e:
            self.log_message(f"Ошибка запуска сервера: {str(e)}")
            self.stop_server()

    def stop_server(self):
        """Остановка сервера"""
        self.is_running = False
        self.start_button.setText('Запустить сервер')
        self.status_label.setText('Статус: Сервер остановлен')

        if hasattr(self, 'server_thread'):
            self.server_thread.stop()
            self.server_thread.wait()

        self.log_message("Сервер остановлен")

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.stop_server()
        event.accept()


class ServerThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, server_socket, trent_window):
        super().__init__()
        self.server_socket = server_socket
        self.trent_window = trent_window
        self.running = True

    def stop(self):
        """Остановка потока"""
        self.running = False
        try:
            # Создаем временное подключение для разблокировки accept()
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('localhost', 5002))
        except:
            pass

    def run(self):
        """Основной цикл обработки подключений"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                if not self.running:
                    break

                self.message_received.emit(f"Новое подключение: {address}")
                self.handle_client(client_socket)

            except Exception as e:
                if self.running:
                    self.message_received.emit(f"Ошибка при принятии подключения: {str(e)}")

    def handle_client(self, client_socket):
        """Обработка клиентского подключения"""
        try:
            self.message_received.emit("Начало обработки клиента")

            # Установка таймаута для сокета
            client_socket.settimeout(20)

            # Получение данных
            data = NetworkUtils.receive_message(client_socket)
            self.message_received.emit(f"Получены данные от клиента: {data}")

            if data['type'] == 'register' or 'b\xad\xe8"\xb2\xd7\xab':
                name = data['name']
                self.message_received.emit(f"Обработка регистрации для {name}")

                # Загрузка публичного ключа клиента
                client_public_key = serialization.load_pem_public_key(
                    data['public_key'].encode()
                )
                self.message_received.emit("Ключ клиента загружен успешно")

                # Сохранение данных клиента
                self.trent_window.clients[name] = {
                    'public_key': client_public_key,
                    'socket': client_socket
                }
                self.message_received.emit("Данные клиента сохранены")

                # Подготовка ответа
                public_bytes = self.trent_window.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )

                response = {
                    'status': 'success',
                    'public_key': public_bytes.decode()
                }

                self.message_received.emit(f"Отправка ответа клиенту {name}")
                NetworkUtils.send_message(client_socket, response)
                self.message_received.emit(f"Ответ отправлен клиенту {name}")

            elif data['type'] == 'request_key':
                self.handle_key_request(client_socket, data)

        except Exception as e:
            error_msg = f"Ошибка обработки клиента: {str(e)}"
            self.message_received.emit(error_msg)
            try:
                error_response = {
                    'status': 'error',
                    'message': str(e)
                }
                NetworkUtils.send_message(client_socket, error_response)
            except Exception as send_error:
                self.message_received.emit(f"Ошибка отправки сообщения об ошибке: {str(send_error)}")

    def handle_registration(self, client_socket, data):
        """Обработка регистрации нового клиента"""
        try:
            self.message_received.emit("Начало регистрации клиента")
            name = data['name']

            # Загрузка публичного ключа клиента
            self.message_received.emit(f"Загрузка ключа клиента {name}")
            client_public_key = serialization.load_pem_public_key(
                data['public_key'].encode()
            )

            # Сохранение данных клиента
            self.trent_window.clients[name] = {
                'public_key': client_public_key,
                'socket': client_socket
            }

            # Подготовка ответа с публичным ключом Трента
            self.message_received.emit("Подготовка ответа")
            public_bytes = self.trent_window.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            response = {
                'status': 'success',
                'public_key': public_bytes.decode()
            }

            # Отправка ответа
            self.message_received.emit("Отправка ответа клиенту")
            NetworkUtils.send_message(client_socket, response)
            self.message_received.emit(f"Клиент {name} успешно зарегистрирован")

        except Exception as e:
            error_msg = f"Ошибка регистрации клиента: {str(e)}"
            self.message_received.emit(error_msg)
            try:
                error_response = {
                    'status': 'error',
                    'message': error_msg
                }
                NetworkUtils.send_message(client_socket, error_response)
            except:
                pass

    def handle_key_request(self, client_socket, data):
        """Обработка запроса открытого ключа"""
        try:
            requested_name = data['name']
            self.message_received.emit(f"Запрос ключа для {requested_name}")

            if requested_name not in self.trent_window.clients:
                raise ValueError(f"Клиент {requested_name} не найден")

            requested_public_key = self.trent_window.clients[requested_name]['public_key']
            public_key_bytes = requested_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Создание подписи
            signature_data = f"{requested_name},{public_key_bytes.decode()}"
            signature = CryptoUtils.sign_message(
                self.trent_window.private_key,
                signature_data
            )

            response = {
                'status': 'success',
                'public_key': public_key_bytes.decode(),
                'signature': signature.hex()
            }

            self.message_received.emit(f"Отправка ключа для {requested_name}")
            NetworkUtils.send_message(client_socket, response)
            self.message_received.emit(f"Ключ отправлен для {requested_name}")

        except Exception as e:
            error_msg = f"Ошибка отправки ключа: {str(e)}"
            self.message_received.emit(error_msg)
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            NetworkUtils.send_message(client_socket, error_response)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TrentWindow()
    window.show()
    sys.exit(app.exec_())