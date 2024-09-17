def xor(a, b):
    # Функция XOR для двух бинарных строк
    return ''.join(str(int(x) ^ int(y)) for x, y in zip(a, b))


def crc(data, generating_polynomial):
    # Функция для вычисления CRC
    gx_len = len(generating_polynomial)
    data += '0' * gx_len
    num = data[:gx_len]

    if len(str(int(data))) < gx_len:
        return str(int(num))

    data = data.replace(data[:gx_len], "", 1)

    while True:
        remainder = str(int(xor(num, generating_polynomial)))

        if remainder == '0':
            if len(data) <= gx_len and int(data) == 0:
                return remainder

            num = data[:gx_len]
            data = data.replace(data[:gx_len], "", 1)

            if len(num) < gx_len:
                return num
        else:
            remainder_len = gx_len - len(remainder)
            num = remainder + data[:remainder_len]
            data = data.replace(data[:remainder_len], "", 1)

            if len(num) < gx_len:
                return num


def detect_crc_collision(iterations, generating_polynomial):
    # Функция для обнаружения коллизий CRC
    collisions = {}

    for num in range(iterations):
        temp = crc(bin(num)[2:], generating_polynomial)

        if temp in collisions:
            collisions[temp].append(num)
        else:
            collisions[temp] = [num]

    return collisions


def dict_output(dictionary):
    # Функция для вывода словаря в отсортированном порядке
    for key, items in sorted(dictionary.items()):
        print(f"Хэш: {key} || Числа: {items}")


if __name__ == '__main__':
    generating_polynomial = "111"  # Полином для генерации CRC
    input_data = "10101010"  # Входные данные
    print(f'CRC от {input_data} =', crc(input_data, generating_polynomial))

    collisions = detect_crc_collision(256, generating_polynomial)
    print("Коллизии:")
    dict_output(collisions)