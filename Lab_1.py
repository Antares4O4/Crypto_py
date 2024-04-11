x_0 = 1
a = 9
c = 12
m = 137

def func_parity_check(n):  # Проверка на чётность/нечетность
    n_bin = format(n, '#010b')
    n_str = str(n_bin[2:])

    if n_str[7] == "0":
        return int(1)
    else:
        return int(0)


def func_conciders(n):  # Счёт количества нулей
    count_zero = 0
    n_bin = format(n, '#010b')
    n_str = str(n_bin[2:])

    for i in range(len(n_str)):
        if n_str[i] == "0":
            count_zero += 1
    return count_zero


def func():
    count_zero = 0
    count_one = 0
    count_ch = 0
    l_t = 0

    count_ch += func_parity_check(x_0)

    x_bin = format(x_0, '#010b')
    x_str = str(x_bin[2:])
    buf = func_conciders(x_0)
    count_one += len(x_str) - buf
    count_zero += buf

    print(f"x_{l_t} =", x_0, "|", x_str, "\n")

    x = x_0

    while True:
        x = (a * x + c) % m

        if x == x_0:
            break

        count_ch += func_parity_check(x)

        x_bin = format(x, '#010b')
        x_str = str(x_bin[2:])
        buf = func_conciders(x)
        count_one += len(x_str) - buf
        count_zero += buf

        l_t += 1
        print(f"x_{l_t} =", x, "|", x_str, "\n")

    print("Длина периода генератора в битах: ", (l_t + 1) * 8, "\n")
    print("Количество чётных чисел: ", count_ch, "\n")
    print("Количество нечётных чисел: ", l_t - count_ch + 1, "\n")
    print("Количество нулей: ", count_zero, "\n")
    print("Количество единиц:", count_one)


func()
