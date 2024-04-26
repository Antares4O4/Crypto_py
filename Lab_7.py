def perfectsquare(x):
    return (int(x ** 0.5)) ** 2 == x


def factorizeferma(n):
    a = 0
    b = 0
    x = int(n ** 0.5) + 1
    while not perfectsquare(x * x - n):
        x += 1
        y = int((x * x - n) ** 0.5)
        a = x - y
        b = x + y
    return a, b


# Функция для нахождения обратного элемента по модулю
def mod_inverse(a, m):
    m0, x0, x1 = m, 0, 1
    while a > 1:
        q = a // m
        m, a = a % m, m
        x0, x1 = x1 - q * x0, x0
    return x1 + m0 if x1 < 0 else x1


# Дано
N = 21733
e = 131
ciphertext = 258

# 1. Факторизация N
p, q = factorizeferma(N)

# 2. Вычисление функции Эйлера
phi = (p - 1) * (q - 1)

# 3. Определение закрытого ключа d
d = mod_inverse(e, phi)

# 4. Расшифровка сообщения
plaintext = pow(ciphertext, d, N)

print("Простые множители числа N:", p, q)
print("Закрытый ключ d:", d)
print("Расшифрованное сообщение:", plaintext)
