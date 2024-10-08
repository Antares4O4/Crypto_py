# порождающий многочлен
g_x = '1011'  # G(x) = 1+x+x3
# словарь для хранения значений CRC-функции и сообщений, которые дают это значение
ans = {
    '0': [],
    '1': [],
    '10': [],
    '11': [],
    '100': [],
    '101': [],
    '110': [],
    '111': [],
}


# функция для преобразования сообщения и вызова хеш-функции
def hash(message):
    # пока в начале сообщения стоят 0, будем их убирать
    while len(message) > 0 and message[0] == '0':
        message = message[1:]

    # добавляем в конец N нулей, то есть домножаем многочлен на x^N, где N - длина g_x
    message = message + '0'*(len(g_x))

    return crc(message)  # вызываем хеш-функцию и возвращаем её результат


# хеш-функция CRC
def crc(message):
    n = len(g_x)  # инициализируем n - количество битов, которыми нужно дополнить d
    d = ''  # инициализируем d - битовая последовательность длины N, которая используется для вычисления функции
    # пока длина d и длина оставшегося сообщения >= длины порождающего многочлена,
    # то есть пока не найдём остаток - число меньшей длины, чем N, делаем вычисления
    while len(message) + len(d) >= len(g_x):
        # если d и оставшееся сообщение не содержат 1, тоесть нулевые,
        # тогда остаток нулевой, значит значение функции равно 0
        if message.count('1') + d.count('1') == 0:
            return '0'

        d += message[0: n]  # добавляем к d n битов из message
        message = message[n:]  # убираем из message биты, добавление к d
        # пока вначале d стоят 0, убираем их и добавляем в конец биты из message, откуда их убираем
        while len(d) > 0 and d[0] == '0':
            d = d[1:]
            d += message[0]
            message = message[1:]

        res = ''  # инициализируем res - результат побитового XOR d и g_x
        for i in range(0, len(d)):
            res += str(int(d[i]) ^ int(g_x[i]))  # побитовый XOR

        # пока вначале res стоят 0, убираем их
        while len(res) > 0 and res[0] == '0':
            res = res[1:]
        d = res  # записываем в d результат побитового XOR, без 0 в начале
        n = len(g_x) - len(res)  # записываем в n число недостающих битов

    return d + message  # остаток определяется как последнее значение + оставшиеся биты в message


# перебираем все однобайтовые числа
for num in range(0, 256):
    bait = format(num, '08b')  # переводим в битовую строку длины 8
    result = hash(bait)  # вызываем функцию и получаем её результат
    ans[result].append(num)  # по этому результату добавляем число в словарь

# вывод словаря значений CRC
print("Список всех значений функции CRC и соответствующих им сообщений.")
for key in ans.keys():
    items = ans[key]
    print(f"{key}: {items}")

print(hash("10101010"))