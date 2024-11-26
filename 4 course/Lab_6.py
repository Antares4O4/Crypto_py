import sys
import numpy as np
from typing import List, Tuple
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QSpinBox, QGroupBox, QGridLayout)
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter
from PyQt5.QtCore import Qt


class LogHighlighter(QSyntaxHighlighter):
    """Подсветка синтаксиса для лога операций"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlights = {
            "Генерация долей:": self.format_header(),
            "Секретная точка:": self.format_secret(),
            "Плоскость": self.format_plane(),
            "Проверка:": self.format_check(),
            "Восстановление секрета:": self.format_header(),
            "Определитель": self.format_math(),
            "Система уравнений:": self.format_header(),
            "Матрица": self.format_matrix(),
            "Найденное решение:": self.format_result(),
            "Тест успешно пройден": self.format_success(),
            "Ошибка:": self.format_error()
        }

    def format_header(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QColor("#2E86C1"))
        return fmt

    def format_secret(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QColor("#27AE60"))
        return fmt

    def format_plane(self):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#8E44AD"))
        return fmt

    def format_check(self):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#D35400"))
        return fmt

    def format_math(self):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#2980B9"))
        return fmt

    def format_matrix(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QColor("#16A085"))
        return fmt

    def format_result(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QColor("#27AE60"))
        return fmt

    def format_success(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QColor("#27AE60"))
        return fmt

    def format_error(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QColor("#C0392B"))
        return fmt

    def highlightBlock(self, text):
        for pattern, fmt in self.highlights.items():
            if pattern in text:
                start = text.index(pattern)
                self.setFormat(start, len(pattern), fmt)


class BlackleyScheme:
    def __init__(self, prime: int):
        """
        Инициализация схемы Блэкли с заданным простым модулем.
        """
        self.prime = prime
        self._validate_prime()
        self.log = []

    def _validate_prime(self):
        """Проверка, является ли заданный модуль простым числом"""
        if self.prime < 2:
            raise ValueError("Модуль должен быть больше 1")
        for i in range(2, int(np.sqrt(self.prime)) + 1):
            if self.prime % i == 0:
                raise ValueError(f"{self.prime} не является простым числом")

    def add_log(self, message: str):
        """Добавление сообщения в лог"""
        self.log.append(message)

    def generate_shares(self, secret: Tuple[int, int, int], n: int) -> List[List[int]]:
        """Генерация n долей для секрета"""
        if n < 3:
            raise ValueError("Количество долей должно быть не менее 3")

        shares = []
        x, y, z = [val % self.prime for val in secret]

        self.add_log("\nГенерация долей:")
        self.add_log(f"Секретная точка: ({x}, {y}, {z})")
        self.add_log("\nСгенерированные уравнения плоскостей:")

        np.random.seed(42)  # Для воспроизводимости результатов

        for i in range(n):
            a = np.random.randint(1, self.prime)
            b = np.random.randint(1, self.prime)
            c = (a * x + b * y + z) % self.prime

            shares.append([a, b, 1, c])

            self.add_log(f"Плоскость {i + 1}: {a}x + {b}y + z = {c} (mod {self.prime})")
            check = (a * x + b * y + z) % self.prime
            self.add_log(f"Проверка: {a}*{x} + {b}*{y} + {z} ≡ {check} ≡ {c} (mod {self.prime})")

        return shares

    def _mod_inverse(self, a: int, m: int) -> int:
        """Вычисление мультипликативного обратного"""

        def egcd(a: int, b: int) -> Tuple[int, int, int]:
            if a == 0:
                return b, 0, 1
            g, x, y = egcd(b % a, a)
            return g, y - (b // a) * x, x

        g, x, _ = egcd(a % m, m)
        if g != 1:
            raise ValueError("Мультипликативное обратное не существует")
        return x % m

    def _solve_linear_system_mod_p(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Решение системы линейных уравнений по модулю p"""
        n = len(b)
        det = int(round(np.linalg.det(A))) % self.prime
        if det == 0:
            raise ValueError("Система уравнений вырождена")

        self.add_log(f"\nОпределитель системы: {det}")
        det_inv = self._mod_inverse(det, self.prime)
        self.add_log(f"Обратный элемент определителя по модулю {self.prime}: {det_inv}")

        result = np.zeros(n, dtype=int)

        for i in range(n):
            A_i = A.copy()
            A_i[:, i] = b
            det_i = int(round(np.linalg.det(A_i))) % self.prime
            result[i] = (det_i * det_inv) % self.prime
            self.add_log(f"Определитель для x_{i + 1}: {det_i}")
            self.add_log(f"x_{i + 1} = ({det_i} * {det_inv}) mod {self.prime} = {result[i]}")

        return result

    def reconstruct_secret(self, shares: List[List[int]]) -> Tuple[int, int, int]:
        """Восстановление секрета из трех долей"""
        if len(shares) < 3:
            raise ValueError("Для восстановления секрета требуется не менее 3 долей")

        shares = shares[:3]

        self.add_log("\nВосстановление секрета:")
        self.add_log("Система уравнений:")
        for i, share in enumerate(shares):
            a, b, c, d = share
            self.add_log(f"{a}x + {b}y + {c}z ≡ {d} (mod {self.prime})")

        A = np.array([[share[0], share[1], share[2]] for share in shares])
        b = np.array([share[3] for share in shares])

        self.add_log("\nМатрица коэффициентов A:")
        self.add_log(str(A))
        self.add_log("\nВектор свободных членов b:")
        self.add_log(str(b))

        try:
            solution = self._solve_linear_system_mod_p(A, b)
            result = tuple(int(x) % self.prime for x in solution)
            self.add_log(f"\nНайденное решение: {result}")
            return result
        except ValueError as e:
            raise ValueError(f"Не удалось восстановить секрет: {str(e)}")


class BlackleyGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Схема разделения секрета Блэкли")
        self.setGeometry(100, 100, 800, 600)

        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Группа параметров
        params_group = QGroupBox("Параметры")
        params_layout = QGridLayout()
        params_group.setLayout(params_layout)

        # Поля ввода
        self.prime_input = QSpinBox()
        self.prime_input.setRange(2, 10000)
        self.prime_input.setValue(257)
        params_layout.addWidget(QLabel("Простое число:"), 0, 0)
        params_layout.addWidget(self.prime_input, 0, 1)

        self.shares_input = QSpinBox()
        self.shares_input.setRange(3, 100)
        self.shares_input.setValue(5)
        params_layout.addWidget(QLabel("Количество долей:"), 0, 2)
        params_layout.addWidget(self.shares_input, 0, 3)

        # Поля для секрета
        secret_group = QGroupBox("Секретная точка")
        secret_layout = QHBoxLayout()
        secret_group.setLayout(secret_layout)

        self.secret_x = QSpinBox()
        self.secret_y = QSpinBox()
        self.secret_z = QSpinBox()
        for spin in [self.secret_x, self.secret_y, self.secret_z]:
            spin.setRange(0, 10000)
        self.secret_x.setValue(5)
        self.secret_y.setValue(3)
        self.secret_z.setValue(4)

        secret_layout.addWidget(QLabel("X:"))
        secret_layout.addWidget(self.secret_x)
        secret_layout.addWidget(QLabel("Y:"))
        secret_layout.addWidget(self.secret_y)
        secret_layout.addWidget(QLabel("Z:"))
        secret_layout.addWidget(self.secret_z)

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Сгенерировать доли")
        self.generate_btn.clicked.connect(self.run_scheme)
        buttons_layout.addWidget(self.generate_btn)

        # Лог операций
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.highlighter = LogHighlighter(self.log_text.document())

        # Добавляем все виджеты в основной layout
        layout.addWidget(params_group)
        layout.addWidget(secret_group)
        layout.addLayout(buttons_layout)
        layout.addWidget(QLabel("Лог операций:"))
        layout.addWidget(self.log_text)

    def run_scheme(self):
        """Запуск схемы Блэкли"""
        try:
            prime = self.prime_input.value()
            n_shares = self.shares_input.value()
            secret = (self.secret_x.value(), self.secret_y.value(), self.secret_z.value())

            scheme = BlackleyScheme(prime)
            shares = scheme.generate_shares(secret, n_shares)
            recovered_secret = scheme.reconstruct_secret(shares)

            log_text = "\n".join(scheme.log)
            if secret == recovered_secret:
                log_text += "\nТест успешно пройден: секрет восстановлен корректно"
            else:
                log_text += f"\nОшибка: секрет восстановлен неверно!"
                log_text += f"\nОжидалось: {secret}"
                log_text += f"\nПолучено: {recovered_secret}"

            self.log_text.setText(log_text)

        except Exception as e:
            self.log_text.setText(f"Ошибка: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = BlackleyGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()