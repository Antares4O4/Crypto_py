import random
import tkinter as tk
from tkinter import messagebox

# Функция для возведения в степень в кольце вычетов
def modular_exponentiation(base, exponent, modulus):
    result = 1
    base = base % modulus  # Уменьшаем базу по модулю
    while exponent > 0:
        if (exponent % 2) == 1:  # Если exponent нечетное
            result = (result * base) % modulus  # Умножаем на базу
        exponent = exponent >> 1  # Делим exponent на 2
        base = (base * base) % modulus  # Квадратируем базу
    return result

# Функция для вычисления НОД двух чисел (алгоритм Евклида)
def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

# Расширенный алгоритм Евклида для нахождения обратного значения
def extended_gcd(a, b):
    if a == 0:
        return b, 0, 1
    gcd_val, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd_val, x, y

# Функция для проверки, является ли число простым (тест Рабина-Миллера)
def miller_rabin(n, k=5):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0:
        return False

    r, d = 0, n - 1
    while d % 2 == 0:
        d //= 2
        r += 1

    for _ in range(k):
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue

        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

# Генерация случайного простого числа
def generate_large_prime(bits):
    while True:
        candidate = random.getrandbits(bits) | 1  # Убедимся, что число нечетное
        if miller_rabin(candidate):
            return candidate

# Основная функция для обработки выбранной операции
def perform_operation():
    operation = operation_var.get()  # Получаем выбранную операцию
    try:
        if operation == "Возведение в степень":
            base = int(base_entry.get())
            exponent = int(exponent_entry.get())
            modulus = int(modulus_entry.get())
            result = modular_exponentiation(base, exponent, modulus)
            result_var.set(f"Результат: {result}")

        elif operation == "НОД двух чисел":
            a = int(first_number_entry.get())
            b = int(second_number_entry.get())
            result = gcd(a, b)
            result_var.set(f"НОД: {result}")

        elif operation == "Обратное значение":
            a = int(inverse_number_entry.get())
            modulus = int(inverse_modulus_entry.get())
            gcd_val, x, _ = extended_gcd(a, modulus)
            if gcd_val != 1:
                result_var.set("Обратное значение не существует")
            else:
                result_var.set(f"Обратное значение: {x % modulus}")

        elif operation == "Генерация простого числа":
            bits = int(bits_entry.get())
            prime = generate_large_prime(bits)
            result_var.set(f"Случайное простое число с {bits} бит: {prime}")

    except ValueError as e:
        messagebox.showerror("Ошибка", str(e))  # Отображаем сообщение об ошибке

# Функция для обновления интерфейса в зависимости от выбранной операции
def update_interface(*args):
    operation = operation_var.get()  # Получаем выбранную операцию
    # Скрываем все поля
    for widget in input_frame.winfo_children():
        widget.grid_remove()

    if operation == "Возведение в степень":
        # Показываем поля для возведения в степень
        base_entry.grid(row=0, column=1)
        exponent_entry.grid(row=1, column=1)
        modulus_entry.grid(row=2, column=1)
        tk.Label(input_frame, text="Основание:").grid(row=0, column=0)
        tk.Label(input_frame, text="Степень:").grid(row=1, column=0)
        tk.Label(input_frame, text="Модуль:").grid(row=2, column=0)

    elif operation == "НОД двух чисел":
        # Показываем поля для нахождения НОД
        first_number_entry.grid(row=3, column=1)
        second_number_entry.grid(row=4, column=1)
        tk.Label(input_frame, text="Первое число:").grid(row=3, column=0)
        tk.Label(input_frame, text="Второе число:").grid(row=4, column=0)

    elif operation == "Обратное значение":
        # Показываем поля для нахождения обратного значения
        inverse_number_entry.grid(row=5, column=1)
        inverse_modulus_entry.grid(row=6, column=1)
        tk.Label(input_frame, text="Число для обратного значения:").grid(row=5, column=0)
        tk.Label(input_frame, text="Модуль:").grid(row=6, column=0)

    elif operation == "Генерация простого числа":
        # Показываем поле для генерации простого числа
        bits_entry.grid(row=7, column=1)
        tk.Label(input_frame, text="Количество бит:").grid(row=7, column=0)

# Создание основного окна приложения
root = tk.Tk()
root.title("Криптографические операции")  # Заголовок окна

# Переменная для хранения результата
result_var = tk.StringVar()  # Хранение результата

# Выбор операции
operation_var = tk.StringVar(value="Возведение в степень")  # По умолчанию выбрана первая операция
operation_var.trace("w", update_interface)  # Отслеживаем изменения в переменной

operation_menu = tk.OptionMenu(root, operation_var,
                                "Возведение в степень",
                                "НОД двух чисел",
                                "Обратное значение",
                                "Генерация простого числа")
operation_menu.pack(pady=10)

# Фрейм для ввода данных
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

# Поля ввода для операции "Возведение в степень"
base_entry = tk.Entry(input_frame)
exponent_entry = tk.Entry(input_frame)
modulus_entry = tk.Entry(input_frame)

# Поля ввода для операции "НОД двух чисел"
first_number_entry = tk.Entry(input_frame)
second_number_entry = tk.Entry(input_frame)

# Поля ввода для операции "Обратное значение"
inverse_number_entry = tk.Entry(input_frame)
inverse_modulus_entry = tk.Entry(input_frame)

# Поля ввода для операции "Генерация простого числа"
bits_entry = tk.Entry(input_frame)

# Кнопка для выполнения операции
execute_button = tk.Button(root, text="Выполнить", command=perform_operation)
execute_button.pack(pady=20)

# Метка для вывода результата с зелёным цветом
result_label = tk.Label(root, textvariable=result_var, fg="green")  # Установка цвета текста на зелёный
result_label.pack(pady=10)

# Инициализация интерфейса
update_interface()

# Запуск основного цикла приложения
root.mainloop()
