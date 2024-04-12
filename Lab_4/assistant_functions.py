Alfavit = {'А': 10, 'Б': 11, 'В': 12, 'Г': 13, 'Д': 14, 'Е': 15, 'Ж': 16, 'З': 17, 'И': 18, 'Й': 19, 'К': 20, 'Л': 21,
           'М': 22, 'Н': 23, 'О': 24, 'П': 25, 'Р': 26, 'С': 27, 'Т': 28, 'У': 29, 'Ф': 30, 'Х': 31, 'Ц': 32, 'Ч': 33,
           'Ш': 34, 'Щ': 35, 'Ъ': 36, 'Ы': 37, 'Ь': 38, 'Э': 39, 'Ю': 40, 'Я': 41, ' ': 99}

Alf_2 = {v: k for k, v in Alfavit.items()}


def num_to_text(text):  # Преобразование из чисел в буквы
    Alf_2 = {v: k for k, v in Alfavit.items()}
    for key in Alf_2.keys():
        text = text.replace(str(key), str(Alf_2[key]))
    return text


def list_to_str(l):  # Преобразование массива в строку чисел
    lst = list(map(str, l))
    string = ''

    for element in lst:
        string += str(element)  # Превращаем каждый элемент списка в строку

    return string


def fast_pow(x, y):  # Возведение в степень
    if y == 0:
        return 1
    if y == -1:
        return 1. / x
    num = fast_pow(x, y // 2)
    num *= num
    if y % 2:
        num *= x
    return num


def multiplicative_inverse(a, b):  # Расширенный алгоритм Евклида для нахождения e
    x = 0
    y = 1
    lx = 1
    ly = 0
    oa = a
    ob = b
    while b != 0:
        q = a // b
        (a, b) = (b, a % b)
        (x, lx) = ((lx - (q * x)), x)
        (y, ly) = ((ly - (q * y)), y)
    if lx < 0:
        lx += ob
    if ly < 0:
        ly += oa
    return lx


def text_to_num_3(text):
    for key in Alfavit.keys():
        text = text.replace(key, str(Alfavit[key]))
    return text
