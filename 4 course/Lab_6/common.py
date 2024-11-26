# common.py
import numpy as np
from numpy.linalg import solve
import random


def generate_plane_coefficients():
    """
    Генерирует случайные коэффициенты для плоскости ax + by + cz + d = 0
    """
    # Генерируем коэффициенты с меньшими значениями для лучшей численной стабильности
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    c = random.randint(1, 10)
    return (a, b, c)


def generate_shares(secret_point, n):
    """
    Генерирует n долей секрета по схеме Блэкли.
    """
    x, y, z = secret_point
    shares = []
    used_coeffs = set()

    while len(shares) < n:
        # Генерируем коэффициенты a, b, c
        a, b, c = generate_plane_coefficients()
        coeff_key = (a, b, c)

        if coeff_key in used_coeffs:
            continue

        # Вычисляем d так, чтобы плоскость проходила через секретную точку
        d = -(a * x + b * y + c * z)

        # Проверяем линейную независимость
        if len(shares) >= 2:
            test_shares = shares[-2:] + [(a, b, c, d)]
            A = np.array([[s[0], s[1], s[2]] for s in test_shares])
            if abs(np.linalg.det(A)) < 1e-10:
                continue

        shares.append((a, b, c, d))
        used_coeffs.add(coeff_key)

    return shares


def reconstruct_from_shares(shares):
    """
    Восстанавливает секрет из трех долей по схеме Блэкли.
    """
    if len(shares) < 3:
        raise ValueError("Need at least 3 shares to reconstruct the secret")

    shares = shares[:3]  # Берем только первые три доли

    # Формируем систему уравнений
    A = np.array([[s[0], s[1], s[2]] for s in shares])
    b = np.array([-s[3] for s in shares])

    try:
        # Решаем систему и округляем результат до ближайших целых
        solution = np.round(solve(A, b))
        return tuple(map(int, solution))
    except np.linalg.LinAlgError:
        raise ValueError("Shares are linearly dependent")


def verify_secret(secret_point, shares):
    """
    Проверяет, что все плоскости проходят через секретную точку
    """
    x, y, z = secret_point
    for a, b, c, d in shares:
        if abs((a * x + b * y + c * z + d)) > 1e-10:
            return False
    return True


def share_to_binary(share):
    """
    Преобразует долю в бинарную строку
    """
    a, b, c, d = share
    result = ''
    for num in (a, b, c, d):
        result += format(num & 0xFFFFFFFF, '032b')
    return result


def binary_to_share(binary):
    """
    Преобразует бинарную строку в долю
    """
    if len(binary) != 128:
        raise ValueError("Invalid binary share length")

    coefficients = []
    for i in range(0, 128, 32):
        num = int(binary[i:i + 32], 2)
        if num & 0x80000000:
            num = num - 0x100000000
        coefficients.append(num)

    return tuple(coefficients)