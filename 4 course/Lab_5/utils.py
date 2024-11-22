# utils.py
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import socket
import json
import time
import threading
import base64


class CryptoUtils:
    @staticmethod
    def generate_key_pair():
        """Генерация пары ключей RSA"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def sign_message(private_key, message):
        """Подпись сообщения закрытым ключом"""
        signature = private_key.sign(
            message.encode() if isinstance(message, str) else message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    @staticmethod
    def verify_signature(public_key, message, signature):
        """Проверка подписи"""
        try:
            public_key.verify(
                signature,
                message.encode() if isinstance(message, str) else message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    @staticmethod
    def encrypt_session_key(public_key, session_key):
        """Шифрование сеансового ключа открытым ключом"""
        encrypted_key = public_key.encrypt(
            session_key if isinstance(session_key, bytes) else session_key.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_key

    @staticmethod
    def decrypt_session_key(private_key, encrypted_key):
        """Расшифровка сеансового ключа закрытым ключом"""
        session_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return session_key


class NetworkUtils:
    TIMEOUT = 20  # таймаут в секундах

    @staticmethod
    def create_connection(host, port, timeout=TIMEOUT):
        """Создание сокета с таймаутом"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        return sock

    @staticmethod
    def send_message(sock, data):
        """Отправка сообщения через сокет"""
        try:
            # Преобразование сообщения в JSON
            message = json.dumps(data, default=lambda x: base64.b64encode(x).decode() if isinstance(x, bytes) else x)
            message_bytes = message.encode("utf-8")

            # Формируем полное сообщение с длиной
            length_prefix = len(message_bytes).to_bytes(4, "big")
            full_message = length_prefix + message_bytes

            # Отправляем данные
            total_sent = 0
            while total_sent < len(full_message):
                sent = sock.send(full_message[total_sent:])
                if sent == 0:
                    raise RuntimeError("Соединение разорвано")
                total_sent += sent

        except Exception as e:
            print(f"Ошибка отправки: {e}")
            raise

    @staticmethod
    def receive_message(sock):
        """Прием сообщения из сокета"""
        try:
            # Получаем 4 байта длины сообщения
            length_data = NetworkUtils._receive_exactly(sock, 4)
            message_length = int.from_bytes(length_data, "big")

            # Получаем само сообщение
            message_data = NetworkUtils._receive_exactly(sock, message_length)
            message_str = message_data.decode("utf-8")

            # Парсим JSON
            message = json.loads(message_str)

            # Преобразуем base64 обратно в bytes где необходимо
            return {k: base64.b64decode(v) if isinstance(v, str) and NetworkUtils.is_base64(v) else v
                    for k, v in message.items()}

        except Exception as e:
            print(f"Ошибка приема: {e}")
            raise

    @staticmethod
    def _receive_exactly(sock, n):
        """Получение точного количества байт"""
        data = bytearray()
        while len(data) < n:
            chunk = sock.recv(min(n - len(data), 4096))
            if not chunk:
                raise ConnectionError("Соединение разорвано")
            data.extend(chunk)
        return bytes(data)

    @staticmethod
    def is_base64(sb):
        """Проверка строки на base64"""
        try:
            if not isinstance(sb, str):
                return False
            if not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in sb):
                return False
            if len(sb) % 4 != 0:
                return False

            # Пробуем декодировать
            base64.b64decode(sb)
            return True
        except:
            return False

    @staticmethod
    def _recv_all(sock, n):
        """Получение точного количества байт"""
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data


class BaseWindow(QMainWindow):
    """Базовый класс для окон клиентов"""

    # Определяем сигналы
    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal(str)
    log_message_signal = pyqtSignal(str)

    def __init__(self, title, port=None):
        super().__init__()
        self.title = title
        self.port = port

        # Подключаем сигналы к слотам
        self.connection_successful.connect(self._handle_successful_connection)
        self.connection_failed.connect(self._handle_failed_connection)
        self.log_message_signal.connect(self.log_message)

        self.initUI()
        self.init_crypto()
        self.init_network()

    def initUI(self):
        """Базовая инициализация интерфейса"""
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 400, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Лог сообщений
        self.log_label = QLabel("Лог событий:")
        self.layout.addWidget(self.log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        self.status_label = QLabel("Статус: Не подключено")
        self.layout.addWidget(self.status_label)

    def init_crypto(self):
        """Базовая инициализация криптографии"""
        self.private_key, self.public_key = CryptoUtils.generate_key_pair()
        self.trent_public_key = None

    def init_network(self):
        """Базовая инициализация сети"""
        self.trent_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.port:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(("localhost", self.port))
            self.server_socket.listen(1)

    def log_message(self, message):
        """Добавление сообщения в лог"""
        current_time = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{current_time}] {message}")

    @pyqtSlot()
    def _handle_successful_connection(self):
        """Обработчик успешного подключения"""
        self.status_label.setText("Статус: Подключено к Тренту")
        self.log_message("Успешное подключение к Тренту")

        self.connect_button.setEnabled(False)
        self.on_trent_connected()

    @pyqtSlot(str)
    def _handle_failed_connection(self, error_message):
        """Обработчик неудачного подключения"""
        self.status_label.setText("Статус: Ошибка подключения")
        self.log_message(f"Ошибка подключения: {error_message}")
        self.connect_button.setEnabled(True)

    def _connect_to_trent_thread(self):
        """Фоновый процесс подключения к Тренту"""
        try:
            # Создаем соединение с таймаутом
            self.trent_socket = NetworkUtils.create_connection("localhost", 5002)

            # Подготовка данных для регистрации
            public_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            registration_data = {
                "type": "register",
                "name": self.title,
                "public_key": public_bytes.decode()
            }

            # Отправка регистрационных данных
            NetworkUtils.send_message(self.trent_socket, registration_data)

            # Получение ответа
            self.log_message_signal.emit("Ожидание ответа от Трента...")

            response = NetworkUtils.receive_message(self.trent_socket)

            if response and response.get("status") == "success":
                self.trent_public_key = serialization.load_pem_public_key(
                    response["public_key"].encode()
                )
                self.log_message(response) # вывод ответа для Трента для проверки
                self.connection_successful.emit()
            else:
                error_msg = response.get("message", "Неизвестная ошибка") if response else "Нет ответа от сервера"
                raise Exception(f"Ошибка при регистрации у Трента: {error_msg}")

        except Exception as e:
            self.connection_failed.emit(str(e))
            if hasattr(self, "trent_socket"):
                try:
                    self.trent_socket.close()
                except:
                    pass

    def connect_to_trent(self):
        """Подключение к серверу Трента"""
        self.connect_thread = threading.Thread(target=self._connect_to_trent_thread)
        self.connect_thread.daemon = True
        self.connect_thread.start()
        self.connect_button.setEnabled(False)
        self.status_label.setText("Статус: Подключение к Тренту...")
        self.log_message("Попытка подключения к Тренту...")

    def request_public_key(self, name):
        """Запрос открытого ключа другого участника"""
        # Отключаем кнопку на время запроса
        sender = self.sender()
        if sender:
            sender.setEnabled(False)

        self.log_message(f"Запрос ключа {name}...")

        # Запускаем запрос в отдельном потоке
        request_thread = threading.Thread(
            target=self._request_key_thread,
            args=(name, sender)
        )
        request_thread.daemon = True
        request_thread.start()

    def _request_key_thread(self, name, sender_button):
        """Фоновый процесс запроса ключа"""
        try:
            request_data = {
                "type": "request_key",
                "name": name
            }

            NetworkUtils.send_message(self.trent_socket, request_data)
            response = NetworkUtils.receive_message(self.trent_socket)

            if response["status"] == "success":
                public_key = serialization.load_pem_public_key(
                    response["public_key"].encode()
                )
                # Проверка подписи Трента
                signature = bytes.fromhex(response["signature"])
                signature_data = f"{name},{response["public_key"]}"

                if CryptoUtils.verify_signature(self.trent_public_key, signature_data, signature):
                    # Вызываем обработчик через сигнал
                    QMetaObject.invokeMethod(
                        self,
                        "_handle_successful_key_request",
                        Qt.QueuedConnection,
                        Q_ARG(str, name),
                        Q_ARG(object, public_key),
                        Q_ARG(object, sender_button)
                    )
                else:
                    raise Exception("Неверная подпись ключа")
            else:
                raise Exception(response.get("message", "Unknown error"))

        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "_handle_failed_key_request",
                Qt.QueuedConnection,
                Q_ARG(str, str(e)),
                Q_ARG(object, sender_button)
            )

    @pyqtSlot(str, object, object)
    def _handle_successful_key_request(self, name, public_key, sender_button):
        """Обработчик успешного получения ключа"""
        if sender_button:
            sender_button.setEnabled(True)
        self.log_message(f"Получен открытый ключ {name}")
        self.on_key_received(name, public_key)

    @pyqtSlot(str, object)
    def _handle_failed_key_request(self, error_message, sender_button):
        """Обработчик неудачного получения ключа"""
        if sender_button:
            sender_button.setEnabled(True)
        self.log_message(f"Ошибка получения ключа: {error_message}")

    @pyqtSlot(str, object)
    def on_key_received(self, name, public_key):
        """Обработчик получения ключа"""
        self.log_message(f"Получен открытый ключ {name}")

    def on_trent_connected(self):
        """Обработчик успешного подключения к Тренту"""
        pass


class MessageHandler:
    """Класс для обработки сообщений протокола"""

    @staticmethod
    def create_session_key_message(session_key, timestamp, lifetime, name, temp_private_key, temp_public_key,
                                   private_key, recipient_public_key):
        """Создание сообщения с сеансовым ключом"""
        try:
            # Шифрование метки времени
            encrypted_timestamp = CryptoUtils.encrypt_session_key(recipient_public_key, timestamp)

            # Подпись времени жизни, имени и временного открытого ключа
            temp_public_bytes = temp_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            signature_data = f"{lifetime},{name},{temp_public_bytes.decode()}"
            signature = CryptoUtils.sign_message(private_key, signature_data)

            # Шифрование и подпись сеансового ключа
            encrypted_session_key = CryptoUtils.encrypt_session_key(recipient_public_key, session_key)
            session_key_signature = CryptoUtils.sign_message(temp_private_key, str(encrypted_session_key))

            return {
                "encrypted_timestamp": encrypted_timestamp,
                "lifetime_signature": signature.hex(),
                "session_key": encrypted_session_key,
                "session_key_signature": session_key_signature.hex(),
                "temp_public_key": temp_public_bytes.decode()
            }
        except Exception as e:
            raise Exception(f"Ошибка создания сообщения с сеансовым ключом: {str(e)}")

    @staticmethod
    def verify_session_key_message(message, private_key, sender_public_key):
        """Проверка сообщения с сеансовым ключом"""
        try:
            # Расшифровка временной метки
            timestamp = CryptoUtils.decrypt_session_key(private_key, message["encrypted_timestamp"])
            current_time = int(time.time())
            timestamp_value = int(timestamp.decode())

            if abs(timestamp_value - current_time) > 300:  # 5 минут
                raise Exception("Временная метка устарела")

            # Расшифровка сеансового ключа
            session_key = CryptoUtils.decrypt_session_key(private_key, message["session_key"])

            # Проверка подписи сеансового ключа
            temp_public_key = serialization.load_pem_public_key(message["temp_public_key"].encode())
            session_key_signature = bytes.fromhex(message["session_key_signature"])

            if not CryptoUtils.verify_signature(temp_public_key, str(message["session_key"]), session_key_signature):
                raise Exception("Неверная подпись сеансового ключа")

            return session_key

        except Exception as e:
            raise Exception(f"Ошибка проверки сообщения с сеансовым ключом: {str(e)}")
