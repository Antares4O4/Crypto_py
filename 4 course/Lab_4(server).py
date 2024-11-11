import socket  # Импортируем модуль socket для создания сетевых соединений
import rsa  # Импортируем модуль rsa для работы с криптографией RSA
import random  # Импортируем модуль random для генерации случайных чисел
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit  # Импортируем модули для создания GUI с PyQt5
from PyQt5.QtCore import pyqtSignal, QObject  # Импортируем необходимые элементы PyQt5 для сигналов и слотов


# Функция для генерации случайного числа в пределах от 1 до 1 000 000
def generate_random_number():
    return random.randint(1, 1000000)


# Загрузка приватного ключа сервера из файла для последующего подписания сообщений
with open("private_key.pem", "rb") as f:
    private_key = rsa.PrivateKey.load_pkcs1(f.read())

# Загрузка публичного ключа клиента из файла для последующей проверки подписей клиента
with open("public_key.pem", "rb") as f:
    client_public_key = rsa.PublicKey.load_pkcs1(f.read())


# Определяем класс Server для серверного приложения
class Server(QObject):
    update_message = pyqtSignal(str)  # Сигнал для обновления сообщений на интерфейсе GUI
    next_step_signal = pyqtSignal()  # Сигнал для перехода к следующему шагу в интерфейсе GUI

    def __init__(self):
        super().__init__()
        # Создаем серверный сокет и настраиваем его для прослушивания входящих соединений
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 9999))  # Привязываем сокет к локальному IP и порту 9999
        self.server_socket.listen(1)  # Сокет ожидает одно входящее соединение
        self.client_socket, self.address = None, None  # Переменные для хранения сокета клиента и его адреса
        self.r_a = None  # Переменная для хранения числа R_A, полученного от клиента
        self.r_b = None  # Переменная для хранения случайного числа R_B, сгенерированного сервером
        self.step_number = 1  # Счетчик для отслеживания текущего шага

    # Функция для запуска сервера и ожидания подключения клиента
    def start_server(self):
        self.update_message.emit(f"Шаг {self.step_number}: Сервер ожидает подключения...")
        # Ожидаем подключения клиента и сохраняем его сокет и адрес
        self.client_socket, self.address = self.server_socket.accept()
        self.update_message.emit(f"Шаг {self.step_number}: Подключение установлено с {self.address}")
        self.step_number += 1  # Переходим к следующему шагу
        self.next_step_signal.emit()  # Отправляем сигнал для обновления шага в интерфейсе

    # Функция для получения R_A от клиента
    def receive_ra(self):
        self.r_a = int(self.client_socket.recv(1024).decode())  # Получаем и декодируем R_A
        self.update_message.emit(f"Шаг {self.step_number}: Получено R_A от клиента: {self.r_a}")
        self.step_number += 1  # Переходим к следующему шагу
        self.next_step_signal.emit()

    # Функция для генерации R_B, создания и отправки сообщения с подписью клиенту
    def generate_and_send_rb(self):
        self.r_b = generate_random_number()  # Генерируем случайное число R_B
        self.update_message.emit(f"Шаг {self.step_number}: Сгенерировано R_B: {self.r_b}")
        # Создаем сообщение, включающее имя сервера, R_A и R_B
        message = f"Bob:{self.r_a}:{self.r_b}".encode()
        # Подписываем сообщение с помощью приватного ключа сервера и SHA-256
        signature = rsa.sign(message, private_key, 'SHA-256')
        self.update_message.emit(f"Шаг {self.step_number}: Сообщение для подписи: {message.decode()}")
        self.update_message.emit(f"Шаг {self.step_number}: Подпись: {signature.hex()}")

        # Отправляем клиенту подпись и число R_B
        self.client_socket.send(signature + b'::' + str(self.r_b).encode())
        self.update_message.emit(f"Шаг {self.step_number}: Отправлено R_B и подпись клиенту.")
        self.step_number += 1
        self.next_step_signal.emit()

    # Функция для получения R_B и подписи от клиента и проверки подлинности клиента
    def receive_and_verify_client_signature(self):
        response = self.client_socket.recv(1024)  # Получаем ответ от клиента
        signature, r_b = response.split(b'::')  # Разделяем сообщение на подпись и число R_B
        r_b = int(r_b.decode())  # Преобразуем R_B в целое число
        self.update_message.emit(f"Шаг {self.step_number}: Получено R_B от клиента: {r_b}")
        self.update_message.emit(f"Шаг {self.step_number}: Подпись клиента: {signature.hex()}")

        # Создаем сообщение для проверки, включающее имя клиента и R_B
        message_to_check = f"Alice:{r_b}".encode()
        self.update_message.emit(f"Шаг {self.step_number}: Сообщение для проверки: [{message_to_check.decode()}]")

        # Проверяем подпись клиента, используя его публичный ключ
        try:
            rsa.verify(message_to_check, signature, client_public_key)
            self.update_message.emit(f"Шаг {self.step_number}: Подпись клиента проверена. Клиент подлинный.")
        except rsa.VerificationError:
            self.update_message.emit(f"Шаг {self.step_number}: Ошибка: неверная подпись клиента.")
        self.client_socket.close()  # Закрываем соединение с клиентом
        self.step_number += 1
        self.next_step_signal.emit()


# GUI-класс ServerGUI, использующий PyQt5 для визуализации серверной стороны
class ServerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сервер - Протокол SKID3")  # Устанавливаем заголовок окна
        self.setGeometry(100, 100, 500, 400)  # Устанавливаем размер окна
        self.server = Server()  # Создаем объект сервера
        self.initUI()  # Инициализация элементов интерфейса
        self.connect_signals()  # Подключение сигналов к функциям

    # Функция для инициализации интерфейса
    def initUI(self):
        layout = QVBoxLayout()  # Создаем вертикальный компоновщик
        self.label = QLabel("Серверная сторона протокола SKID3", self)  # Заголовок интерфейса
        layout.addWidget(self.label)

        self.info_text = QTextEdit(self)  # Текстовое поле для отображения сообщений
        self.info_text.setReadOnly(True)  # Делаем поле только для чтения
        layout.addWidget(self.info_text)

        self.next_button = QPushButton("Запустить сервер", self)  # Кнопка для перехода к следующему шагу
        layout.addWidget(self.next_button)

        self.setLayout(layout)  # Устанавливаем компоновщик на виджет
        self.current_step = 0  # Счетчик для отслеживания текущего шага

    # Функция для подключения сигналов к функциям
    def connect_signals(self):
        self.server.update_message.connect(self.update_message)  # Подключение обновления сообщений
        self.server.next_step_signal.connect(self.next_step)  # Подключение сигнала перехода к следующему шагу
        self.next_button.clicked.connect(self.execute_step)  # Подключение кнопки к выполнению шага

    # Функция для выполнения шагов протокола
    def execute_step(self):
        if self.current_step == 0:
            self.server.start_server()
            self.next_button.setText("Получить R_A от клиента")
        elif self.current_step == 1:
            self.server.receive_ra()
            self.next_button.setText("Отправить R_B и подпись клиенту")
        elif self.current_step == 2:
            self.server.generate_and_send_rb()
            self.next_button.setText("Получить подпись клиента и R_B")
        elif self.current_step == 3:
            self.server.receive_and_verify_client_signature()
            self.next_button.setEnabled(False)  # Отключаем кнопку после завершения всех шагов

    # Функция для перехода к следующему шагу
    def next_step(self):
        self.current_step += 1

    # Функция для обновления сообщений в интерфейсе
    def update_message(self, message):
        self.info_text.append(message)  # Добавляем новое сообщение в текстовое поле


# Создаем приложение и запускаем интерфейс сервера
app = QApplication([])
server_gui = ServerGUI()
server_gui.show()
app.exec_()
