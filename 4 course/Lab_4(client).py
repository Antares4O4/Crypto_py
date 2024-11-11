import socket  # Импортируем модуль socket для работы с сетевыми соединениями
import rsa  # Импортируем модуль rsa для работы с криптографией RSA
import random  # Импортируем модуль random для генерации случайных чисел
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit  # Импортируем модули для создания GUI с PyQt5
from PyQt5.QtCore import pyqtSignal, QObject  # Импортируем элементы для сигналов и слотов в PyQt5


# Функция для генерации случайного числа R_A в пределах от 1 до 1 000 000
def generate_random_number():
    return random.randint(1, 1000000)


# Загрузка публичного ключа сервера из файла для проверки подписи сервера
with open("public_key.pem", "rb") as f:
    server_public_key = rsa.PublicKey.load_pkcs1(f.read())

# Загрузка приватного ключа клиента из файла для подписи сообщения клиентом
with open("private_key.pem", "rb") as f:
    client_private_key = rsa.PrivateKey.load_pkcs1(f.read())


# Определяем класс Client, который реализует клиентскую часть протокола SKID3
class Client(QObject):
    update_message = pyqtSignal(str)  # Сигнал для обновления сообщений в интерфейсе
    next_step_signal = pyqtSignal()  # Сигнал для перехода к следующему шагу в интерфейсе

    def __init__(self):
        super().__init__()
        # Создаем клиентский сокет
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.r_a = None  # Переменная для хранения случайного числа R_A
        self.r_b = None  # Переменная для хранения R_B, полученного от сервера
        self.step_number = 1  # Счетчик для отслеживания текущего шага

    # Функция для генерации случайного числа R_A и отправки его серверу
    def generate_and_send_ra(self):
        self.r_a = generate_random_number()  # Генерируем случайное число R_A
        self.update_message.emit(f"Шаг {self.step_number}: Сгенерировано R_A: {self.r_a}")
        # Устанавливаем соединение с сервером
        self.socket.connect(('localhost', 9999))
        # Отправляем R_A серверу в виде строки
        self.socket.send(str(self.r_a).encode())
        self.step_number += 1  # Переходим к следующему шагу
        self.next_step_signal.emit()

    # Функция для получения R_B и подписи от сервера и проверки подлинности сервера
    def receive_and_verify_signature(self):
        # Получаем ответ от сервера
        response = self.socket.recv(1024)
        # Разделяем полученные данные на подпись и R_B
        signature, r_b = response.split(b'::')
        self.r_b = int(r_b.decode())  # Декодируем и сохраняем R_B
        self.update_message.emit(f"Шаг {self.step_number}: Получено R_B от сервера: {self.r_b}")
        self.update_message.emit(f"Шаг {self.step_number}: Подпись от сервера: {signature.hex()}")

        # Создаем сообщение для проверки подписи
        message_to_check = f"Bob:{self.r_a}:{self.r_b}".encode()
        self.update_message.emit(f"Шаг {self.step_number}: Сообщение для проверки: [{message_to_check.decode()}]")

        # Проверяем подпись, используя публичный ключ сервера
        try:
            rsa.verify(message_to_check, signature, server_public_key)
            self.update_message.emit(f"Шаг {self.step_number}: Подпись проверена. Сервер подлинный.")
        except rsa.VerificationError:
            self.update_message.emit(f"Шаг {self.step_number}: Ошибка: неверная подпись сервера.")

        # Создаем и подписываем сообщение для подтверждения подлинности клиента
        signature_client = rsa.sign(f"Alice:{self.r_b}".encode(), client_private_key, 'SHA-256')
        # Отправляем подпись и R_B обратно серверу
        self.socket.send(signature_client + b'::' + str(self.r_b).encode())
        self.socket.close()  # Закрываем соединение
        self.step_number += 1
        self.next_step_signal.emit()


# GUI-класс ClientGUI, использующий PyQt5 для визуализации клиентской стороны
class ClientGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Клиент - Протокол SKID3")  # Устанавливаем заголовок окна
        self.setGeometry(100, 100, 500, 400)  # Устанавливаем размер окна
        self.client = Client()  # Создаем объект клиента
        self.initUI()  # Инициализация элементов интерфейса
        self.connect_signals()  # Подключение сигналов к функциям

    # Функция для инициализации интерфейса
    def initUI(self):
        layout = QVBoxLayout()  # Создаем вертикальный компоновщик
        self.label = QLabel("Клиентская сторона протокола SKID3", self)  # Заголовок интерфейса
        layout.addWidget(self.label)

        self.info_text = QTextEdit(self)  # Текстовое поле для отображения сообщений
        self.info_text.setReadOnly(True)  # Делаем поле только для чтения
        layout.addWidget(self.info_text)

        self.next_button = QPushButton("Запустить клиент", self)  # Кнопка для перехода к следующему шагу
        layout.addWidget(self.next_button)

        self.setLayout(layout)  # Устанавливаем компоновщик на виджет
        self.current_step = 0  # Счетчик для отслеживания текущего шага

    # Функция для подключения сигналов к функциям
    def connect_signals(self):
        self.client.update_message.connect(self.update_message)  # Подключение обновления сообщений
        self.client.next_step_signal.connect(self.next_step)  # Подключение сигнала перехода к следующему шагу
        self.next_button.clicked.connect(self.execute_step)  # Подключение кнопки к выполнению шага

    # Функция для выполнения шагов протокола
    def execute_step(self):
        if self.current_step == 0:
            # Первый шаг: генерируем и отправляем R_A серверу
            self.client.generate_and_send_ra()
            self.next_button.setText("Получить R_B и подпись сервера")
        elif self.current_step == 1:
            # Второй шаг: получаем и проверяем R_B и подпись от сервера
            self.client.receive_and_verify_signature()
            self.next_button.setEnabled(False)  # Отключаем кнопку после завершения всех шагов

    # Функция для перехода к следующему шагу
    def next_step(self):
        self.current_step += 1

    # Функция для обновления сообщений в интерфейсе
    def update_message(self, message):
        self.info_text.append(message)  # Добавляем новое сообщение в текстовое поле


# Создаем приложение и запускаем интерфейс клиента
app = QApplication([])
client_gui = ClientGUI()
client_gui.show()
app.exec_()
