# utils.py
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import socket
import time
import threading
import json
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
        try:
            if isinstance(message, str):
                message = message.encode()
            elif not isinstance(message, bytes):
                raise ValueError("Message must be string or bytes")

            signature = private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return signature
        except Exception as e:
            print(f"Error signing message: {str(e)}")
            raise

    @staticmethod
    def verify_signature(public_key, message, signature):
        """Проверка подписи"""
        try:
            if isinstance(message, str):
                message = message.encode()
            elif not isinstance(message, bytes):
                raise ValueError("Message must be string or bytes")

            if not isinstance(signature, bytes):
                raise ValueError("Signature must be bytes")

            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {str(e)}")
            return False

    @staticmethod
    def encrypt_session_key(public_key, data):
        """Шифрование данных открытым ключом"""
        data_bytes = data if isinstance(data, bytes) else data.encode()
        encrypted_data = public_key.encrypt(
            data_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_data

    @staticmethod
    def decrypt_session_key(private_key, encrypted_data):
        """Расшифровка данных закрытым ключом"""
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_data


class NetworkUtils:
    TIMEOUT = 20  # таймаут в секундах
    WOULD_BLOCK_ERRORS = (10035, 11)  # Windows и Unix коды ошибок для неблокирующих операций

    @staticmethod
    def create_connection(host, port, timeout=TIMEOUT):
        """Создание сокета с таймаутом"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        return sock

    @staticmethod
    def send_message(sock, data):
        """Отправка сообщения с корректной обработкой бинарных данных"""
        try:
            if isinstance(data, dict):
                processed_data = {}
                for k, v in data.items():
                    if isinstance(v, bytes):
                        processed_data[k] = base64.b64encode(v).decode('utf-8')
                    else:
                        processed_data[k] = v
                message = json.dumps(processed_data)
            else:
                message = json.dumps(data)

            message_bytes = message.encode('utf-8')
            length_bytes = len(message_bytes).to_bytes(4, 'big')

            # Отправка длины сообщения
            total_sent = 0
            while total_sent < 4:
                try:
                    sent = sock.send(length_bytes[total_sent:])
                    if sent == 0:
                        raise ConnectionError("Соединение разорвано")
                    total_sent += sent
                except socket.error as e:
                    if e.errno in NetworkUtils.WOULD_BLOCK_ERRORS:
                        time.sleep(0.1)
                        continue
                    raise

            # Отправка самого сообщения
            total_sent = 0
            while total_sent < len(message_bytes):
                try:
                    sent = sock.send(message_bytes[total_sent:])
                    if sent == 0:
                        raise ConnectionError("Соединение разорвано")
                    total_sent += sent
                except socket.error as e:
                    if e.errno in NetworkUtils.WOULD_BLOCK_ERRORS:
                        time.sleep(0.1)
                        continue
                    raise

        except Exception as e:
            print(f"Ошибка отправки: {e}")
            raise

    @staticmethod
    def parse_message(message):
        """Безопасный парсинг сообщения в словарь"""
        try:
            if not isinstance(message, str):
                return message

            if "|" in message:
                result = {}
                pairs = message.split("|")
                for pair in pairs:
                    if "=" in pair:
                        key, value = pair.split("=", 1)  # Разделяем только по первому '='
                        result[key.strip()] = value.strip()
                    else:
                        print(f"Пропущена некорректная пара: {pair}")
                return result
            return message
        except Exception as e:
            print(f"Ошибка парсинга сообщения: {e}")
            return message

    @staticmethod
    def receive_message(sock):
        """Получение сообщения с таймаутом и обработкой неблокирующего режима"""
        try:
            # Получение длины сообщения
            length_bytes = bytearray()
            attempts = 0
            max_attempts = 10

            while len(length_bytes) < 4 and attempts < max_attempts:
                try:
                    chunk = sock.recv(4 - len(length_bytes))
                    if not chunk:
                        raise ConnectionError("Соединение разорвано")
                    length_bytes.extend(chunk)
                except socket.error as e:
                    if e.errno in NetworkUtils.WOULD_BLOCK_ERRORS:
                        attempts += 1
                        time.sleep(0.1)
                        continue
                    raise

            if len(length_bytes) < 4:
                raise BlockingIOError("Нет данных для чтения")

            message_length = int.from_bytes(length_bytes, 'big')
            message_bytes = bytearray()
            attempts = 0

            while len(message_bytes) < message_length and attempts < max_attempts:
                try:
                    chunk = sock.recv(min(4096, message_length - len(message_bytes)))
                    if not chunk:
                        raise ConnectionError("Соединение разорвано")
                    message_bytes.extend(chunk)
                except socket.error as e:
                    if e.errno in NetworkUtils.WOULD_BLOCK_ERRORS:
                        attempts += 1
                        time.sleep(0.1)
                        continue
                    raise

            if len(message_bytes) < message_length:
                raise BlockingIOError("Нет данных для чтения")

            # Декодирование и парсинг JSON
            message = message_bytes.decode('utf-8')
            data = json.loads(message)

            # Преобразование base64 обратно в bytes
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, str) and k in [
                        'encrypted_timestamp',
                        'session_key',
                        'session_key_signature',
                        'lifetime_signature',  # Добавлен lifetime_signature
                        'content'
                    ]:
                        try:
                            data[k] = base64.b64decode(v)
                        except Exception as e:
                            print(f"Error decoding {k}: {str(e)}")
                            raise

            return data

        except BlockingIOError:
            raise
        except Exception as e:
            print(f"Ошибка приема: {e}")
            raise


class BaseWindow(QMainWindow):
    """Базовый класс для окон клиентов"""

    connection_successful = pyqtSignal()
    connection_failed = pyqtSignal(str)
    log_message_signal = pyqtSignal(str)

    def __init__(self, title, port=None):
        super().__init__()
        self.title = title
        self.port = port

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
            self.trent_socket = NetworkUtils.create_connection("localhost", 5000)

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
                self.log_message(response)  # вывод ответа для Трента
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

    # def request_public_key(self, name):
    #     """Запрос открытого ключа другого участника"""
    #     # Отключаем кнопку на время запроса
    #     sender = self.sender()
    #     if sender:
    #         sender.setEnabled(False)
    #
    #     self.log_message(f"Запрос ключа {name}...")
    #
    #     # Запускаем запрос в отдельном потоке
    #     request_thread = threading.Thread(
    #         target=self._request_key_thread,
    #         args=(name, sender)
    #     )
    #     request_thread.daemon = True
    #     request_thread.start()

    # def _request_key_thread(self, name, sender_button):
    #     """Фоновый процесс запроса ключа"""
    #     try:
    #         request_data = {
    #             "type": "request_key",
    #             "name": name
    #         }
    #
    #         NetworkUtils.send_message(self.trent_socket, request_data)
    #         response = NetworkUtils.receive_message(self.trent_socket)
    #
    #         if response["status"] == "success":
    #             public_key = serialization.load_pem_public_key(
    #                 response["public_key"].encode()
    #             )
    #             # Проверка подписи Трента
    #             signature = bytes.fromhex(response["signature"])
    #             signature_data = f"{name},{response["public_key"]}"
    #
    #             if CryptoUtils.verify_signature(self.trent_public_key, signature_data, signature):
    #                 # Вызываем обработчик через сигнал
    #                 QMetaObject.invokeMethod(
    #                     self,
    #                     "_handle_successful_key_request",
    #                     Qt.QueuedConnection,
    #                     Q_ARG(str, name),
    #                     Q_ARG(object, public_key),
    #                     Q_ARG(object, sender_button)
    #                 )
    #             else:
    #                 raise Exception("Неверная подпись ключа")
    #         else:
    #             raise Exception(response.get("message", "Unknown error"))
    #
    #         return request_data
    #
    #     except Exception as e:
    #         QMetaObject.invokeMethod(
    #             self,
    #             "_handle_failed_key_request",
    #             Qt.QueuedConnection,
    #             Q_ARG(str, str(e)),
    #             Q_ARG(object, sender_button)
    #         )

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
    def normalize_key_string(key_str):
        """Нормализация строки ключа для подписи"""
        normalized = key_str.strip()
        normalized = normalized.replace('\r\n', '\n')
        normalized = normalized.replace('\n', '\\n')
        return normalized

    def create_session_key_message(session_key, timestamp, lifetime, name, temp_private_key, temp_public_key,
                                   private_key, recipient_public_key):
        """Создание сообщения с сеансовым ключом"""
        try:
            # Шифрование метки времени
            encrypted_timestamp = CryptoUtils.encrypt_session_key(recipient_public_key, timestamp.encode())

            # Получаем временный открытый ключ в формате PEM
            temp_public_bytes = temp_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

            # Нормализуем ключ для подписи
            normalized_key = MessageHandler.normalize_key_string(temp_public_bytes)

            # Создаем данные для подписи как строку
            signature_data_str = f"{lifetime},{name},{normalized_key}"
            # Преобразуем в bytes для подписи
            signature_data = signature_data_str.encode()

            # Создаем подпись
            lifetime_signature = CryptoUtils.sign_message(private_key, signature_data)

            # Шифруем сеансовый ключ
            encrypted_session_key = CryptoUtils.encrypt_session_key(recipient_public_key, session_key)

            # Подписываем зашифрованный сеансовый ключ
            session_key_signature = CryptoUtils.sign_message(temp_private_key, encrypted_session_key)

            message1 = MessageHandler.create_session_key_message(
                lifetime,
                "Alice",
                temp_public_key,
                signature=CryptoUtils.sign_message(lifetime,"Alice",temp_public_key)
            )
            NetworkUtils.send_message(self.bob_socket, message)

            message2 = MessageHandler.create_session_key_message(
                encrypted_session_key,
                signature=CryptoUtils.sign_message(encrypted_session_key)
            )
            NetworkUtils.send_message(self.bob_socket, message2)

            message3 = MessageHandler.create_session_key_message(
                encrypted_timestamp,
            )
            NetworkUtils.send_message(self.bob_socket, message1)
            return message1,message2,message3

        except Exception as e:
            print(f"Error in create_session_key_message: {str(e)}")
            raise Exception(f"Ошибка создания сообщения с сеансовым ключом: {str(e)}")

    @staticmethod
    def verify_session_key_message(message, private_key, sender_public_key):
        """Проверка сообщения с сеансовым ключом"""
        try:
            # Debug logging
            print("Message keys:", message.keys())
            print("Signature type:", type(message.get("lifetime_signature")))

            # Проверка наличия всех необходимых полей
            required_fields = [
                "encrypted_timestamp",
                "lifetime_signature",
                "session_key",
                "session_key_signature",
                "temp_public_key",
                "lifetime",
                "name"
            ]

            for field in required_fields:
                if field not in message:
                    raise Exception(f"Missing required field: {field}")
                if message[field] is None:
                    raise Exception(f"Field is None: {field}")

            # Проверка формата подписи
            if not isinstance(message["lifetime_signature"], bytes):
                print(f"Invalid signature format. Got {type(message['lifetime_signature'])}")
                raise Exception(f"Invalid signature format: {type(message['lifetime_signature'])}")

            # Проверка временной метки
            timestamp = CryptoUtils.decrypt_session_key(private_key, message["encrypted_timestamp"])
            current_time = int(time.time())
            timestamp_value = int(timestamp.decode())

            if abs(timestamp_value - current_time) > 3:
                raise Exception(f"Timestamp expired: {abs(timestamp_value - current_time)} seconds")

            # Нормализация ключа
            temp_public_key_str = MessageHandler.normalize_key_string(message['temp_public_key'])

            # Создание данных для проверки подписи
            verification_data = f"{message['lifetime']},{message['name']},{temp_public_key_str}"

            print(f"Verification data: {verification_data}")
            print(f"Signature length: {len(message['lifetime_signature'])}")

            # Проверка подписи lifetime
            if not CryptoUtils.verify_signature(
                    sender_public_key,
                    verification_data.encode(),
                    message["lifetime_signature"]
            ):
                raise Exception("Invalid lifetime signature")

            # Загрузка временного ключа
            temp_public_key = serialization.load_pem_public_key(
                message["temp_public_key"].encode()
            )

            # Проверка и расшифровка сеансового ключа
            session_key = CryptoUtils.decrypt_session_key(
                private_key,
                message["session_key"]
            )

            # Проверка подписи сеансового ключа
            if not CryptoUtils.verify_signature(
                    temp_public_key,
                    message["session_key"],
                    message["session_key_signature"]
            ):
                raise Exception("Invalid session key signature")

            return session_key

        except Exception as e:
            print(f"Error in verify_session_key_message: {str(e)}")
            raise