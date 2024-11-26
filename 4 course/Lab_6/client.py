# client.py
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QGroupBox, QTextEdit, QLineEdit,
                             QApplication, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import socket
import json
import threading
from common import reconstruct_from_shares, binary_to_share


class SignalHandler(QObject):
    secret_reconstructed = pyqtSignal(tuple)
    share_received = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    chat_message_received = pyqtSignal(str)


class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.socket = None
        self.my_share = None
        self.shares = []
        self.shares_count = 0

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle('Blakley Secret Sharing Client')
        self.setGeometry(100, 100, 600, 800)

        # Создаем основной виджет и компоновщик
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Инициализация обработчика сигналов
        self.signals = SignalHandler()
        self.signals.secret_reconstructed.connect(self.update_secret)
        self.signals.share_received.connect(self.update_received_shares)
        self.signals.status_updated.connect(self.update_status)
        self.signals.chat_message_received.connect(self.update_chat)

        # Создаем и добавляем все секции интерфейса
        self.setup_status_section()
        self.setup_share_section()
        self.setup_received_shares_section()
        self.setup_reconstruction_section()
        self.setup_chat_section()

        # Изначально отключаем чат
        self.message_input.setEnabled(False)
        self.send_btn.setEnabled(False)

    def setup_status_section(self):
        """Настройка секции статуса"""
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel('Status: Not connected')
        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.connect_to_server)

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.connect_btn)
        status_group.setLayout(status_layout)
        self.main_layout.addWidget(status_group)

    def setup_share_section(self):
        """Настройка секции для отображения своей доли"""
        share_group = QGroupBox("My Plane Coefficients")
        share_layout = QVBoxLayout()

        self.share_label = QLabel('None')
        self.share_label.setWordWrap(True)
        share_layout.addWidget(self.share_label)
        share_group.setLayout(share_layout)
        self.main_layout.addWidget(share_group)

    def setup_received_shares_section(self):
        """Настройка секции для отображения полученных долей"""
        received_group = QGroupBox("Received Plane Coefficients")
        received_layout = QVBoxLayout()

        self.received_shares = QTextEdit()
        self.received_shares.setReadOnly(True)
        self.received_shares.setMaximumHeight(150)
        received_layout.addWidget(self.received_shares)
        received_group.setLayout(received_layout)
        self.main_layout.addWidget(received_group)

    def setup_reconstruction_section(self):
        """Настройка секции реконструкции секрета"""
        reconstruct_group = QGroupBox("Secret Point Reconstruction")
        reconstruct_layout = QVBoxLayout()

        self.reconstruct_btn = QPushButton('Reconstruct Secret Point')
        self.reconstruct_btn.clicked.connect(self.reconstruct)
        self.result_label = QLabel('Secret Point: Unknown')
        self.result_label.setWordWrap(True)

        reconstruct_layout.addWidget(self.reconstruct_btn)
        reconstruct_layout.addWidget(self.result_label)
        reconstruct_group.setLayout(reconstruct_layout)
        self.main_layout.addWidget(reconstruct_group)

    def setup_chat_section(self):
        """Настройка секции чата"""
        chat_group = QGroupBox("Secure Chat")
        chat_layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter your message...")
        self.message_input.returnPressed.connect(self.send_message)
        self.send_btn = QPushButton('Send')
        self.send_btn.clicked.connect(self.send_message)

        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_btn)
        chat_layout.addLayout(message_layout)

        chat_group.setLayout(chat_layout)
        self.main_layout.addWidget(chat_group)

    def connect_to_server(self):
        """Подключение к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', 5000))
            self.signals.status_updated.emit("Connected")

            data = self.socket.recv(1024).decode()
            msg = json.loads(data)
            if msg['type'] == 'share':
                self.my_share = msg['data']
                plane_coeffs = binary_to_share(self.my_share)
                self.shares = [plane_coeffs]

                # Отображаем коэффициенты плоскости
                coeffs_str = f'a={plane_coeffs[0]}, b={plane_coeffs[1]}, c={plane_coeffs[2]}, d={plane_coeffs[3]}'
                self.share_label.setText(coeffs_str)
                self.signals.status_updated.emit("Got my plane coefficients")

            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.connect_btn.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Connection error: {str(e)}')

    def update_status(self, status):
        """Обновление статуса"""
        self.status_label.setText(f"Status: {status}")

    def update_received_shares(self, binary_share):
        """Обновление списка полученных долей"""
        self.shares_count += 1
        plane_coeffs = binary_to_share(binary_share)
        coeffs_str = f"Plane {self.shares_count}: a={plane_coeffs[0]}, b={plane_coeffs[1]}, c={plane_coeffs[2]}, d={plane_coeffs[3]}\n"
        self.received_shares.append(coeffs_str)

    def update_secret(self, secret):
        """Обновление отображения восстановленного секрета"""
        x, y, z = secret
        self.result_label.setText(f'Reconstructed secret point: ({x}, {y}, {z})')

    def update_chat(self, message):
        """Обновление чата"""
        self.chat_display.append(message)
        # Прокрутка чата вниз
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def receive_messages(self):
        """Получение сообщений от сервера"""
        received_shares = set()  # Множество для отслеживания уже полученных долей

        while True:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break

                msg = json.loads(data)
                if msg['type'] == 'share':
                    share = msg['data']
                    plane_coeffs = binary_to_share(share)

                    # Преобразуем коэффициенты в строку для хранения в множестве
                    share_key = f"{plane_coeffs[0]},{plane_coeffs[1]},{plane_coeffs[2]},{plane_coeffs[3]}"

                    # Проверяем, не получали ли мы уже такую долю
                    if share_key not in received_shares:
                        received_shares.add(share_key)
                        self.signals.share_received.emit(share)

                        if plane_coeffs not in self.shares:
                            self.shares.append(plane_coeffs)
                            self.signals.status_updated.emit(
                                f"Got plane coefficients {len(self.shares)}/3")

                elif msg['type'] == 'chat':
                    self.signals.chat_message_received.emit(
                        f"User: {msg['message']}")

            except Exception as e:
                print(f"Error receiving message: {e}")
                self.signals.status_updated.emit("Connection lost")
                break

    def reconstruct(self):
        """Реконструкция секрета"""
        try:
            # Проверяем, не была ли уже выполнена реконструкция
            if not self.reconstruct_btn.isEnabled():
                return

            # Если у нас меньше 3 долей, запрашиваем дополнительные
            if len(self.shares) < 3:
                self.signals.status_updated.emit("Requesting shares...")
                self.socket.send(json.dumps({
                    'type': 'request_share',
                    'from': self.socket.getsockname()
                }).encode())
                return  # Ждем получения долей через receive_messages

            # Если у нас уже есть 3 или больше долей
            try:
                secret_point = reconstruct_from_shares(self.shares[:3])
                self.signals.secret_reconstructed.emit(secret_point)
                self.signals.status_updated.emit("Secret point reconstructed")
                self.reconstruct_btn.setEnabled(False)
                # Активируем чат
                self.message_input.setEnabled(True)
                self.send_btn.setEnabled(True)
            except ValueError as e:
                QMessageBox.warning(self, 'Reconstruction Error',
                                    f'Failed to reconstruct secret: {str(e)}')

        except Exception as e:
            QMessageBox.critical(self, 'Error',
                                 f'Failed to request shares: {str(e)}')
            self.signals.status_updated.emit("Reconstruction failed")

    def send_message(self):
        """Отправка сообщения в чат"""
        message = self.message_input.text().strip()
        if message:
            try:
                self.socket.send(json.dumps({
                    'type': 'chat',
                    'message': message
                }).encode())
                # Отображаем свое сообщение
                self.chat_display.append(f"Me: {message}")
                self.message_input.clear()
            except Exception as e:
                QMessageBox.critical(self, 'Error',
                                     f'Failed to send message: {str(e)}')

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.socket:
            self.socket.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()