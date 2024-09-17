def binary_xor(bin1, bin2):
    # XOR двух бинарных строк
    return ''.join('1' if a != b else '0' for a, b in zip(bin1, bin2))


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


def crc_remainder(data, polynom):
    # Вычисление остатка CRC
    dividend = data + '0' * (len(polynom))
    remainder = poly_division(dividend, polynom)
    return remainder


# Функция для вычисления коллизий CRC
def find_crc_collisions(polynom):
    # Словарь для хранения хешей и соответствующих чисел
    hashes = {}

    # Перебираем числа от 0 до 255
    for i in range(256):
        # Преобразуем число в бинарную строку
        number_str = bin(i)[2:].zfill(8)
        # Вычисляем хеш числа
        hash_value = crc_remainder(number_str, polynom)
        # Добавляем хеш и число в словарь
        if hash_value in hashes:
            hashes[hash_value].append(i)
        else:
            hashes[hash_value] = [i]

    # Находим коллизии
    collisions = {key: value for key, value in hashes.items() if len(value) > 2}

    # Выводим результаты
    print("Коллизии:")
    for hash_value, numbers in collisions.items():
        print(f"Хеш: {hash_value} || Числа: {numbers}")


polynom = "111"
print(crc_remainder("10101010", polynom))
find_crc_collisions(polynom)
