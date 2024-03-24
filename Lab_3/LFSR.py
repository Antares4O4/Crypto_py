s_1, s_2, s_3 = -1, -3, -8  # Номер битов,которые ксорим


def solution(text, n):  # Последовательности на разбиение на строки по 8 бит
    a = [text[i:i + n] for i in range(0, len(text), n)]
    return a


def count_ch(a):  # Четность нечетность внутри массива с подстроками
    count_cht = 0
    for i in range(len(a)):
        for j in range(len(a[i])):
            if j % 8 == 7 and a[i][j] == "0":
                count_cht += 1
    return count_cht


def func_conciders(y):  # Счёт количества нулей
    count_zero = 0
    for i in range(len(y)):
        if y[i] == "0":
            count_zero += 1
    return count_zero


def main_func():
    count = 1  # Общий счётчик (начинается с одного т.к первый элемент обрабатывается вне цикла)
    i = 1  # Ещё один счётчик
    bin_i = "11010101"  # Начальное состояние регистра;

    # Обработка нулевого элемента вне цикла:

    a_0 = str((int(bin_i[s_1]) + int(bin_i[s_2]) + int(bin_i[s_3])) % 2)

    gen_bit = bin_i[7]  # Массив хранящий вытесненые биты
    buf = a_0 + bin_i[0:7]

    while True:

        a = str((int(buf[s_1]) + int(buf[s_2]) + int(buf[s_3])) % 2)

        count += 1
        gen_bit += buf[7]
        buf = a + buf[0:7]

        i += 1

        if bin_i == buf:
            break

    return list(map(int, solution(gen_bit, 1)))
