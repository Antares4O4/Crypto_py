Alfavit = {'А': 10, 'Б': 11, 'В': 12, 'Г': 13, 'Д': 14, 'Е': 15, 'Ж': 16, 'З': 17, 'И': 18, 'Й': 19, 'К': 20, 'Л': 21,
           'М': 22, 'Н': 23, 'О': 24, 'П': 25, 'Р': 26, 'С': 27, 'Т': 28, 'У': 29, 'Ф': 30, 'Х': 31, 'Ц': 32, 'Ч': 33,
           'Ш': 34, 'Щ': 35, 'Ъ': 36, 'Ы': 37, 'Ь': 38, 'Э': 39, 'Ю': 40, 'Я': 41, ' ': 99}

Alf_2 = {v: k for k, v in Alfavit.items()}


def num_to_text_enc(text):  # Преобразование из чисел в буквы
    for key in Alf_2.keys():
        text = text.replace(str(key), str(Alf_2[key]))
    return text


def num_to_text_dec(str_num):
    text = ""
    for i in range(0, len(str_num), 2):
        text += Alf_2[int(str_num[i: i + 2])]
    return text


def list_to_str(l):  # Преобразование массива в строку чисел
    lst = list(map(str, l))
    string = ''

    for element in lst:
        string += str(element)  # Превращаем каждый элемент списка в строку

    return string


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

def num_to_text_2(text):
    decrypted_text = ''.join([Alf_2[int(text[i:i + 2])] for i in range(0, len(text), 2)])
    return decrypted_text
    print("Расшифрованный текст:", decrypted_text)

def num_to_text(text):  # Преобразование из чисел в буквы
    Alf_2 = {v: k for k, v in Alfavit.items()}
    for key in Alf_2.keys():
        text = text.replace(str(key), str(Alf_2[key]))
    return text

