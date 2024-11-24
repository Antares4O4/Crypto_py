# bob.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import socket
from cryptography.hazmat.primitives import serialization
from utils import CryptoUtils, NetworkUtils, MessageHandler
import time
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

class BobWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "Bob"
        self.signals = ThreadSafeSignal(self)  # Добавляем объект для безопасных сигналов
        self.initUI()
        self.init_crypto()
        self.init_network()

        # Добавляем блокировку для безопасного доступа к ключам
        self.key_lock = threading.Lock()

        self.has_alice_key = False
        self.session_established = False
        self.alice_public_key = None
        self.alice_socket = None
        self.session_key = None

        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_connections)
        self.check_timer.setInterval(100)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 400, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        self.connect_button = QPushButton('Подключиться к Тренту')
        self.connect_button.clicked.connect(self.connect_to_trent)
        self.layout.addWidget(self.connect_button)

        self.start_server = QPushButton('Запустить сервер')
        self.start_server.clicked.connect(self.start_server_listening)
        self.start_server.setEnabled(False)
        self.layout.addWidget(self.start_server)

        self.request_alice_key = QPushButton('Запросить ключ Алисы')
        self.request_alice_key.clicked.connect(self.request_public_key)
        self.request_alice_key.setEnabled(False)
        self.layout.addWidget(self.request_alice_key)

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
        """Инициализация сетевого взаимодействия"""
        # Создаем серверный сокет
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', 5002))
        self.server_socket.listen(1)
        self.server_socket.setblocking(False)

        # Сокет для подключения к Тренту
        self.trent_socket = None
        self.is_running = False  # Добавляем флаг состояния

    def log_message(self, message):
        current_time = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{current_time}] {message}")

    def connect_to_trent(self):
        """Подключение к серверу Трента"""
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
                'name': 'Bob',
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
                self.start_server.setEnabled(True)
                self.request_alice_key.setEnabled(True)
                # После успешного подключения переводим сокет в неблокирующий режим
                self.trent_socket.setblocking(False)
            else:
                error_msg = response.get('message', 'Неизвестная ошибка')
                self.log_message(f"Ошибка при регистрации у Трента: {error_msg}")

        except socket.timeout:
            self.log_message("Таймаут при подключении к Тренту")
        except Exception as e:
            self.log_message(f"Ошибка подключения: {str(e)}")
            self.status_label.setText('Статус: Ошибка подключения')
            if self.trent_socket:
                self.trent_socket.close()
                self.trent_socket = None

    def start_server_listening(self):
        """Запуск прослушивания входящих подключений"""
        self.is_running = True
        self.check_timer.start()
        self.status_label.setText('Статус: Ожидание подключения Алисы')
        self.log_message("Сервер запущен")
        self.start_server.setEnabled(False)

    # def check_connections(self):
    #     """Проверка новых подключений и сообщений"""
    #     if not self.is_running:
    #         return
    #
    #     try:
    #         # Проверяем новые подключения только если нет активного подключения
    #         if not self.alice_socket:
    #             try:
    #                 # Используем неблокирующий accept()
    #                 self.alice_socket, address = self.server_socket.accept()
    #                 self.alice_socket.setblocking(False)
    #                 self.log_message(f"Алиса подключена: {address}")
    #                 self.status_label.setText('Статус: Алиса подключена')
    #             except BlockingIOError:
    #                 pass  # Нормальная ситуация для неблокирующего сокета
    #             except Exception as e:
    #                 self.log_message(f"Ошибка принятия подключения: {str(e)}")
    #                 return
    #
    #         # Проверяем сообщения только если есть активное подключение
    #         elif self.alice_socket:
    #             try:
    #                 message = NetworkUtils.receive_message(self.alice_socket)
    #                 if message:
    #                     # Запускаем обработку сообщения в отдельном потоке
    #                     processing_thread = threading.Thread(
    #                         target=self._process_message_thread,
    #                         args=(message,)
    #                     )
    #                     processing_thread.daemon = True
    #                     processing_thread.start()
    #
    #             except BlockingIOError:
    #                 pass  # Нормальная ситуация для неблокирующего сокета
    #             except ConnectionError:
    #                 self.log_message("Соединение с Алисой потеряно")
    #                 self.handle_connection_loss()
    #             except Exception as e:
    #                 if "Соединение разорвано" in str(e):
    #                     self.handle_connection_loss()
    #                 else:
    #                     self.log_message(f"Ошибка приема сообщения: {str(e)}")
    #
    #     except Exception as e:
    #         self.log_message(f"Ошибка проверки подключений: {str(e)}")

    def handle_connection_loss(self):
        """Обработка потери соединения"""
        try:
            if self.alice_socket:
                try:
                    self.alice_socket.close()
                except:
                    pass
                finally:
                    self.alice_socket = None

            self.session_established = False
            self.send_message.setEnabled(False)
            self.session_key = None
            self.status_label.setText('Статус: Ожидание подключения Алисы')
            self.log_message("Соединение с Алисой потеряно")
        except Exception as e:
            self.log_message(f"Ошибка в handle_connection_loss: {str(e)}")

    @pyqtSlot()
    def _handle_session_established(self):
        """Обработчик установки сессии"""
        try:
            self.session_established = True
            self.send_message.setEnabled(True)
            self.log_message("Сеансовый ключ успешно установлен")
        except Exception as e:
            self.log_message(f"Ошибка в _handle_session_established: {str(e)}")

    def _process_message_thread(self, message):
        """Обработка сообщения в отдельном потоке"""
        try:
            self.signals.emit_log("Начало обработки сообщения")

            if isinstance(message, dict):
                if 'encrypted_timestamp' in message:
                    try:
                        self.signals.emit_log("Проверка сеансового ключа...")

                        if not self.alice_public_key:
                            self.signals.emit_log("Отсутствует открытый ключ Алисы. Запрашиваем...")
                            if not self.request_alice_key_sync():
                                raise Exception("Не удалось получить ключ Алисы")

                        if not self.alice_public_key:
                            raise Exception("Ключ Алисы не установлен после запроса")

                        with self.key_lock:
                            self.session_key = MessageHandler.verify_session_key_message(
                                message,
                                self.private_key,
                                self.alice_public_key
                            )

                        self.signals.emit_log("Сеансовый ключ успешно проверен")
                        self.session_established = True
                        self.signals.emit_enable_button(self.send_message, True)

                    except Exception as e:
                        self.signals.emit_log(f"Ошибка проверки сеансового ключа: {str(e)}")
                        raise

                elif message.get('type') == 'message' and self.session_established:
                    try:
                        self.signals.emit_log("Расшифровка сообщения...")
                        decrypted_message = CryptoUtils.decrypt_session_key(
                            self.private_key,
                            message['content']
                        ).decode()

                        self.signals.emit_log(f"Алиса: {decrypted_message}")
                    except Exception as e:
                        self.signals.emit_log(f"Ошибка расшифровки сообщения: {str(e)}")

        except Exception as e:
            self.signals.emit_log(f"Ошибка обработки сообщения: {str(e)}")

    def handle_message(self, message):
        """Обработка всех входящих сообщений"""
        try:
            if not isinstance(message, dict):
                return

            message_type = message.get('type')

            # Обработка сообщения с сеансовым ключом
            if 'encrypted_timestamp' in message:
                try:
                    self.log_message("Получено сообщение с сеансовым ключом")

                    if not self.alice_public_key:
                        self.log_message("Отсутствует ключ Алисы. Запрашиваем...")
                        if not self.request_alice_key_sync():
                            raise Exception("Не удалось получить ключ Алисы")

                    if not self.alice_public_key:
                        raise Exception("Ключ Алисы не установлен после запроса")

                    self.log_message("Проверка подписи...")
                    with self.key_lock:
                        if not self.alice_public_key:
                            raise Exception("Ключ Алисы отсутствует при проверке")

                        self.session_key = MessageHandler.verify_session_key_message(
                            message,
                            self.private_key,
                            self.alice_public_key
                        )

                    self.log_message("Сеансовый ключ успешно проверен")
                    self.session_established = True  # Устанавливаем флаг сразу после успешной проверки

                    # Обновляем GUI через сигнал
                    QMetaObject.invokeMethod(
                        self,
                        "_handle_session_established",
                        Qt.ConnectionType.QueuedConnection
                    )
                    return True  # Возвращаем True для индикации успешной установки сессии

                except Exception as e:
                    self.log_message(f"Ошибка проверки сеансового ключа: {str(e)}")
                    self.session_established = False
                    return False

            # Обработка обычного сообщения
            elif message_type == 'message' and self.session_established:
                try:
                    decrypted_content = CryptoUtils.decrypt_session_key(
                        self.private_key,
                        message['content']
                    ).decode()

                    # Безопасно обновляем GUI через сигнал
                    QMetaObject.invokeMethod(
                        self,
                        "log_message",
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, f"Алиса: {decrypted_content}")
                    )
                    return True
                except Exception as e:
                    QMetaObject.invokeMethod(
                        self,
                        "log_message",
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, f"Ошибка расшифровки: {str(e)}")
                    )
                    return False
            else:
                self.log_message(f"Получено неизвестное сообщение типа: {message_type}")
                return False

        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "log_message",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, f"Ошибка обработки сообщения: {str(e)}")
            )
            return False
    def check_connections(self):
        """Проверка новых подключений и сообщений"""
        if not self.is_running:
            return

        try:
            # Проверяем новые подключения
            try:
                client_socket, address = self.server_socket.accept()
                client_socket.setblocking(False)
                self.log_message(f"Новое подключение от {address}")

                # Запускаем обработку клиента в отдельном потоке
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()

            except BlockingIOError:
                pass  # Нормальная ситуация для неблокирующего сокета
            except Exception as e:
                if "Соединение разорвано" not in str(e):
                    self.log_message(f"Ошибка принятия подключения: {str(e)}")

        except Exception as e:
            self.log_message(f"Ошибка в check_connections: {str(e)}")

    def _handle_client(self, client_socket):
        """Обработка подключенного клиента"""
        try:
            # Устанавливаем таймаут для приема данных
            client_socket.settimeout(10)
            self.log_message("Начало обработки клиента")

            # Ждем сообщение
            message = NetworkUtils.receive_message(client_socket)
            if not message:
                self.log_message("Пустое сообщение от клиента")
                client_socket.close()
                return

            self.log_message(f"Получено сообщение: {message.get('type', 'unknown')}")

            # Если это сообщение с сеансовым ключом
            if 'encrypted_timestamp' in message:
                try:
                    # Обрабатываем сообщение
                    session_established = self.handle_message(message)

                    # Если сессия успешно установлена
                    if session_established:
                        self.log_message("Устанавливаем постоянное соединение с Алисой")
                        # Сохраняем сокет и настраиваем его
                        self.alice_socket = client_socket
                        self.alice_socket.setblocking(False)
                        return  # Выходим, сохраняя сокет открытым
                    else:
                        self.log_message("Сессия не была установлена")
                        client_socket.close()
                except Exception as e:
                    self.log_message(f"Ошибка установки сессии: {str(e)}")
                    client_socket.close()

            # Для обычных сообщений
            elif message.get('type') == 'message':
                try:
                    # Обработка сообщения
                    self.handle_message(message)

                    # Если это временный сокет для отдельного сообщения
                    if client_socket != self.alice_socket:
                        client_socket.close()
                except Exception as e:
                    self.log_message(f"Ошибка обработки сообщения: {str(e)}")
                    if client_socket != self.alice_socket:
                        client_socket.close()

            else:
                self.log_message("Получено сообщение неизвестного типа")
                if client_socket != self.alice_socket:
                    client_socket.close()

        except socket.timeout:
            self.log_message("Таймаут при ожидании данных")
            if client_socket != self.alice_socket:
                client_socket.close()
        except Exception as e:
            self.log_message(f"Ошибка обработки клиента: {str(e)}")
            if client_socket != self.alice_socket:
                client_socket.close()
    # def handle_alice_message(self, message):
    #     """Обработка сообщений от Алисы"""
    #     try:
    #         # Отладочный вывод для анализа входящего сообщения
    #         self.log_message(f"Получено сообщение от Алисы: {message}")
    #
    #         if isinstance(message, dict):
    #             if 'encrypted_timestamp' in message:
    #                 try:
    #                     self.session_key = MessageHandler.verify_session_key_message(
    #                         message,
    #                         self.private_key,
    #                         self.alice_public_key
    #                     )
    #                     self.session_established = True
    #                     self.send_message.setEnabled(True)
    #                     self.log_message("Сеансовый ключ успешно установлен")
    #                 except Exception as e:
    #                     self.log_message(f"Ошибка проверки сеансового ключа: {str(e)}")
    #
    #             elif message.get('type') == 'message' and self.session_established:
    #                 try:
    #                     decrypted_message = CryptoUtils.decrypt_session_key(
    #                         self.private_key,
    #                         message['content']
    #                     ).decode()
    #                     self.log_message(f"Алиса: {decrypted_message}")
    #                 except Exception as e:
    #                     self.log_message(f"Ошибка расшифровки сообщения: {str(e)}")
    #             else:
    #                 self.log_message(f"Получено неизвестное сообщение: {message}")
    #         else:
    #             self.log_message(f"Получено некорректное сообщение (не словарь): {message}")
    #
    #     except Exception as e:
    #         self.log_message(f"Ошибка обработки сообщения: {str(e)}")
    #
    # def _process_message_thread(self, message):
    #     """Обработка сообщения в отдельном потоке"""
    #     try:
    #         self.log_message(f"Начало обработки сообщения: {message.get('type', 'unknown')}")
    #
    #         if isinstance(message, dict):
    #             if 'encrypted_timestamp' in message:
    #                 try:
    #                     self.log_message("Получено сообщение с сеансовым ключом")
    #
    #                     # Проверяем/получаем ключ Алисы синхронно
    #                     if not self.alice_public_key:
    #                         self.log_message("Отсутствует ключ Алисы. Запрашиваем...")
    #                         if not self.request_alice_key_sync():
    #                             raise Exception("Не удалось получить ключ Алисы")
    #
    #                     if not self.alice_public_key:
    #                         raise Exception("Ключ Алисы не установлен после запроса")
    #
    #                     self.log_message("Проверка подписи...")
    #                     with self.key_lock:
    #                         if not self.alice_public_key:
    #                             raise Exception("Ключ Алисы отсутствует при проверке")
    #
    #                         self.session_key = MessageHandler.verify_session_key_message(
    #                             message,
    #                             self.private_key,
    #                             self.alice_public_key
    #                         )
    #
    #                     self.log_message("Сеансовый ключ успешно проверен")
    #
    #                     QMetaObject.invokeMethod(
    #                         self,
    #                         "_handle_session_established",
    #                         Qt.QueuedConnection
    #                     )
    #
    #                 except Exception as e:
    #                     self.log_message(f"Ошибка проверки сеансового ключа: {str(e)}")
    #                     raise
    #
    #             elif message.get('type') == 'message' and self.session_established:
    #                 try:
    #                     decrypted_message = CryptoUtils.decrypt_session_key(
    #                         self.private_key,
    #                         message['content']
    #                     ).decode()
    #
    #                     QMetaObject.invokeMethod(
    #                         self,
    #                         "log_message",
    #                         Qt.QueuedConnection,
    #                         Q_ARG(str, f"Алиса: {decrypted_message}")
    #                     )
    #                 except Exception as e:
    #                     self.log_message(f"Ошибка расшифровки сообщения: {str(e)}")
    #
    #     except Exception as e:
    #         self.log_message(f"Ошибка обработки сообщения: {str(e)}")
    #         QMetaObject.invokeMethod(
    #             self,
    #             "handle_connection_loss",
    #             Qt.QueuedConnection
    #         )

    def request_public_key(self):
        """Запрос открытого ключа другого участника"""
        target_name = 'Alice'  # или 'Alice' для Боба
        try:
            if not self.trent_socket:
                self.log_message("Нет подключения к Тренту")
                return None

            request_data = {
                'type': 'request_key',
                'name': target_name
            }

            self.log_message(f"Отправка запроса ключа {target_name}")
            NetworkUtils.send_message(self.trent_socket, request_data)

            self.log_message("Ожидание ответа от Трента")
            response = NetworkUtils.receive_message(self.trent_socket)

            if response.get('status') == 'success':
                # Получаем данные из ответа
                public_key_str = response['public_key']
                signature = bytes.fromhex(response['signature'])
                signed_data = response['signed_data']  # Уже содержит экранированные переносы строк

                # Проверяем подпись используя оригинальные подписанные данные
                self.log_message("Проверка подписи Трента...")
                if CryptoUtils.verify_signature(self.trent_public_key, signed_data, signature):
                    self.log_message("Подпись Трента верна")

                    # Преобразуем ключ
                    target_public_key = serialization.load_pem_public_key(
                        public_key_str.encode()
                    )

                    # Устанавливаем флаги в зависимости от полученного ключа
                    if target_name == 'Bob':
                        self.has_bob_key = True
                        self.bob_public_key = target_public_key
                        self.send_session_key.setEnabled(True)
                        self.connect_to_bob()
                    elif target_name == 'Alice':
                        self.has_alice_key = True
                        self.alice_public_key = target_public_key

                    self.log_message(f"Получен и проверен открытый ключ {target_name}")
                    return target_public_key
                else:
                    self.log_message("Ошибка проверки подписи")
                    return None
        except Exception as e:
            self.log_message(f"Ошибка запроса ключа: {str(e)}")
            return None

    def send_encrypted_message(self):
        """Отправка зашифрованного сообщения"""
        try:
            if not self.session_established or not self.alice_socket:
                return

            message = self.message_input.text()
            if not message:
                return

            encrypted_message = CryptoUtils.encrypt_session_key(
                self.alice_public_key,
                message.encode()
            )

            message_data = {
                'type': 'message',
                'content': encrypted_message
            }

            NetworkUtils.send_message(self.alice_socket, message_data)
            self.signals.emit_log(f"Отправлено: {message}")
            self.signals.emit_clear_input()

        except Exception as e:
            self.signals.emit_log(f"Ошибка отправки сообщения: {str(e)}")

    def request_alice_key_sync(self):
        """Синхронный запрос ключа Алисы"""
        try:
            if not self.trent_socket:
                self.log_message("Нет подключения к Тренту")
                return False

            # Временно делаем сокет блокирующим для запроса
            self.trent_socket.setblocking(True)

            request_data = {
                'type': 'request_key',
                'name': 'Alice'
            }

            self.log_message("Отправка запроса ключа Алисы")
            NetworkUtils.send_message(self.trent_socket, request_data)

            response = NetworkUtils.receive_message(self.trent_socket)

            # Возвращаем сокет в неблокирующий режим
            self.trent_socket.setblocking(False)

            if response and response.get('status') == 'success':
                # Получаем данные из ответа
                public_key_str = response['public_key']
                signature = bytes.fromhex(response['signature'])
                signed_data = response['signed_data']

                self.log_message("Проверка подписи Трента...")
                if not self.trent_public_key:
                    raise Exception("Отсутствует открытый ключ Трента")

                if CryptoUtils.verify_signature(self.trent_public_key, signed_data, signature):
                    self.log_message("Подпись Трента верна")

                    # Сохраняем ключ Алисы
                    with self.key_lock:
                        self.alice_public_key = serialization.load_pem_public_key(
                            public_key_str.encode()
                        )
                        self.has_alice_key = True

                    self.log_message("Получен и сохранен открытый ключ Алисы")
                    return True
                else:
                    self.log_message("Ошибка проверки подписи")
                    return False
            else:
                error_msg = response.get('message', 'Unknown error') if response else "Нет ответа от сервера"
                self.log_message(f"Ошибка получения ключа: {error_msg}")
                return False

        except Exception as e:
            self.log_message(f"Ошибка запроса ключа: {str(e)}")
            return False

    def closeEvent(self, event):
        """Корректное закрытие соединений"""
        self.check_timer.stop()
        if self.alice_socket:
            try:
                self.alice_socket.close()
            except:
                pass
        if self.trent_socket:
            try:
                self.trent_socket.close()
            except:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BobWindow()
    window.show()
    sys.exit(app.exec_())
