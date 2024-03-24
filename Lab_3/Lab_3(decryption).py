import os
from LFSR import main_func as lfsr
from tkinter import filedialog


def dec_func(path_2):
    with open(path_2, 'rb') as f:
        file_code = f.read()

    gamma = lfsr()
    i = 0

    if len(file_code) > len(gamma):
        while True:

            gamma.append(gamma[i])
            i += 1

            if len(gamma) == len(file_code):
                break

    elif len(file_code) < len(gamma):
        while True:

            gamma.pop()
            i += 1

            if len(gamma) == len(file_code):
                break

    dec_data = (map(lambda a, b: a ^ b, file_code, gamma))

    dec_path = os.path.splitext(path_2)[0][:-4] + '_dec' + os.path.splitext(path_2)[1]

    with open(dec_path, 'wb+') as f_1:
        f_1.write(bytes(dec_data))


name_1 = filedialog.askopenfilename()
dec_func(name_1)
