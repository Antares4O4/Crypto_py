# trent.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import socket
import time
from utils import CryptoUtils, NetworkUtils
from cryptography.hazmat.primitives import serialization
import select


class TrentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.init_crypto()
        self.init_network()
        self.clients = {}
        self.is_running = False
        self.sockets_list = []  # Список всех активных сокетов

        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_connections)
        self.check_timer.setInterval(100)

    def initUI(self):
        self.setWindowTitle('Трент')
        self.setGeometry(100, 100, 400, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.start_button = QPushButton('Запустить сервер')
        self.start_button.clicked.connect(self.toggle_server)
        layout.addWidget(self.start_button)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.status_label = QLabel('Статус: Сервер остановлен')
        layout.addWidget(self.status_label)

    def init_crypto(self):
        self.private_key, self.public_key = CryptoUtils.generate_key_pair()

    def init_network(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Устанавливаем неблокирующий режим
        self.server_socket.setblocking(False)
        try:
            self.server_socket.bind(('localhost', 5000))
            self.server_socket.listen(20)
            self.log_message("Сервер успешно инициализирован на порту 5000")
        except Exception as e:
            self.log_message(f"Ошибка при инициализации сервера: {str(e)}")
        self.sockets_list = [self.server_socket]

    def log_message(self, message):
        current_time = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{current_time}] {message}")

    def toggle_server(self):
        if not self.is_running:
            self.start_server()
        else:
            self.stop_server()

    # Исправленная версия start_server
    def start_server(self):
        try:
            self.is_running = True
            self.start_button.setText('Остановить сервер')
            self.status_label.setText('Статус: Сервер запущен')
            self.log_message("Сервер запущен")
            # Запускаем таймер проверки подключений
            self.check_timer.start()
        except Exception as e:
            self.log_message(f"Ошибка запуска сервера: {str(e)}")
            self.stop_server()

    def stop_server(self):
        self.is_running = False
        self.check_timer.stop()
        self.start_button.setText('Запустить сервер')
        self.status_label.setText('Статус: Сервер остановлен')
        self.log_message("Сервер остановлен")

    def check_connections(self):
        if not self.is_running:
            return

        try:
            # Фильтруем только действительные сокеты
            valid_sockets = [sock for sock in self.sockets_list if sock and sock.fileno() != -1]

            if not valid_sockets:
                self.sockets_list = [self.server_socket]
                return

            try:
                # Используем select с небольшим таймаутом
                readable, _, exceptional = select.select(valid_sockets, [], valid_sockets, 0.1)

                # Обработка исключительных ситуаций
                for sock in exceptional:
                    self.log_message(f"Исключительная ситуация для сокета")
                    if sock in self.sockets_list:
                        self.sockets_list.remove(sock)
                    sock.close()

                for sock in readable:
                    if sock == self.server_socket:
                        # Новое подключение
                        try:
                            client_socket, address = self.server_socket.accept()
                            client_socket.setblocking(False)
                            self.sockets_list.append(client_socket)
                            self.log_message(f"Новое подключение: {address}")
                        except Exception as e:
                            self.log_message(f"Ошибка при принятии подключения: {str(e)}")
                    else:
                        # Обработка данных от существующего клиента
                        try:
                            data = NetworkUtils.receive_message(sock)
                            if data:
                                self.log_message(f"Получены данные: {data}")
                                if data.get('type') == 'register':
                                    self.handle_registration(sock, data)
                                elif data.get('type') == 'request_key':
                                    self.handle_key_request(sock, data)
                                    self.log_message("Запрос ключа обработан")
                        except (ConnectionError, ConnectionResetError):
                            self.log_message("Клиент отключился")
                            if sock in self.sockets_list:
                                self.sockets_list.remove(sock)
                            sock.close()
                            # Удаляем клиента из словаря clients если он там есть
                            to_remove = []
                            for name, client in self.clients.items():
                                if client['socket'] == sock:
                                    to_remove.append(name)
                            for name in to_remove:
                                del self.clients[name]

            except select.error as e:
                self.log_message(f"Ошибка select: {str(e)}")
                # Очищаем недействительные сокеты
                self.sockets_list = [sock for sock in self.sockets_list if sock and sock.fileno() != -1]

        except Exception as e:
            self.log_message(f"Ошибка в check_connections: {str(e)}")
            # В случае серьезной ошибки, очищаем список сокетов
            self.sockets_list = [self.server_socket]

    def handle_registration(self, client_socket, data):
        try:
            name = data.get('name')
            if not name:
                raise ValueError("Имя клиента не указано")

            public_key_data = data.get('public_key')
            if not public_key_data:
                raise ValueError("Открытый ключ не предоставлен")

            client_public_key = serialization.load_pem_public_key(
                public_key_data.encode()
            )

            self.clients[name] = {
                'public_key': client_public_key,
                'socket': client_socket
            }

            response = {
                'status': 'success',
                'public_key': self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()
            }

            NetworkUtils.send_message(client_socket, response)
            self.log_message(f"Клиент {name} зарегистрирован")

        except Exception as e:
            self.log_message(f"Ошибка регистрации: {str(e)}")
            try:
                error_response = {
                    'status': 'error',
                    'message': str(e)
                }
                NetworkUtils.send_message(client_socket, error_response)
            except:
                pass

    def show_connected_clients(self):
        """Отображает список подключенных клиентов"""
        self.log_message("Подключенные клиенты:")
        for name in self.clients:
            self.log_message(f"- {name}")

    def handle_key_request(self, client_socket, data):
        """Обработка запроса на получение открытого ключа"""
        try:
            self.log_message(f"Начало обработки запроса ключа: {data}")

            # Получаем имя из запроса
            requested_name = data.get('name')
            if not requested_name:
                raise ValueError("Не указано имя запрашиваемого клиента")

            self.log_message(f"Ищем ключ для: {requested_name}")

            # Проверяем наличие клиента
            if requested_name not in self.clients:
                raise ValueError(f"Клиент {requested_name} не найден")

            # Получаем и конвертируем ключ
            requested_public_key = self.clients[requested_name]['public_key']
            public_key_bytes = requested_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

            # Заменяем символы новой строки на \n для согласованности
            public_key_str = public_key_bytes.replace('\n', '\\n')

            # Создаем строку для подписи
            message_to_sign = f"{requested_name},{public_key_str}"
            self.log_message(f"Подписываем сообщение: {message_to_sign}")

            # Создаем подпись
            signature = CryptoUtils.sign_message(self.private_key, message_to_sign)

            # Формируем ответ
            response = {
                'status': 'success',
                'public_key': public_key_bytes,  # Оригинальный ключ с реальными переносами строк
                'signature': signature.hex(),
                'signed_data': message_to_sign  # Подписанные данные с экранированными переносами
            }

            self.log_message(f"Отправляем ответ с ключом")
            NetworkUtils.send_message(client_socket, response)
            self.log_message("Ответ отправлен")

        except Exception as e:
            error_msg = f"status=error|message={str(e)}"
            NetworkUtils.send_message(client_socket, {'status': 'error', 'message': str(e)})
            self.log_message(f"Ошибка обработки запроса ключа: {str(e)}")

    def closeEvent(self, event):
        """Корректное закрытие всех соединений"""
        self.is_running = False
        self.check_timer.stop()
        for sock in self.sockets_list:
            try:
                sock.close()
            except:
                pass
        self.sockets_list.clear()
        self.clients.clear()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TrentWindow()
    window.show()
    sys.exit(app.exec_())
