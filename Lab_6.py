import random

def crc(data, polynom="111"):
    # Вычисление остатка CRC
    dividend = data + '0' * (len(polynom) - 1)
    remainder = poly_division(dividend, polynom)
    return remainder

def poly_division(dividend, divisor):
    # Функция для деления многочленов
    while len(dividend) >= len(divisor):

        if dividend[0] == '0':
            dividend = dividend[1:]
            continue

        # Получение степени многочлена
        degree_diff = len(dividend) - len(divisor)

        # XOR многочленов
        dividend = binary_xor(dividend, divisor + '0' * degree_diff)

    # Остаток - оставшийся многочлен после деления
    remainder = dividend
    return remainder

def binary_xor(bin1, bin2):
    # XOR двух бинарных строк
    return ''.join('1' if a != b else '0' for a, b in zip(bin1, bin2))

# Функция для вычисления обратного элемента в кольце по модулю
def mod_inverse(a, m):
    m0, x0, x1 = m, 0, 1
    while a > 1:
        q = a // m
        m, a = a % m, m
        x0, x1 = x1 - q * x0, x0
    return x1 + m0 if x1 < 0 else x1

# Функция для генерации закрытого и открытого ключей
def generate_keys(p, g):
    x = 3
    y = pow(g, x, p)
    return x, y

# Функция для подписи сообщения
def sign_message(message, x, p, g):
    x = 1
    print(f"x = {x}")
    h = int(crc(message), 2) % (p - 1)
    k = random.randint(1, p - 1)
    r = pow(g, k, p)
    u = (h - x * r) % (p - 1)
    k_inv = mod_inverse(k, p - 1)
    s = (k_inv * u) % (p - 1)
    return (r, s)

# Функция для проверки подписи
def verify_signature(message, signature, y, p, g):
    h = int(crc(message), 2) % (p - 1)
    r, s = signature
    v1 = pow(y, r, p)
    v2 = pow(r, s, p)
    gh = (v1 * v2) % p
    return gh == pow(g, h, p)

# Генерация параметров
p, g = 227, 24

# Генерация ключей
x, y = generate_keys(p, g)

# Сообщение для подписи
message = "100010110"

# Формирование подписи
signature = sign_message(message, x, p, g)

print("Сформированная подпись:", signature)

# Проверка подписи
is_valid = verify_signature(message, signature, y, p, g)
if is_valid:
    print("Подпись верна.")
else:
    print("Подпись недействительна.")