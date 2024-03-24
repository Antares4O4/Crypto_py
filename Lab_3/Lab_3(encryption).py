import os
from LFSR import main_func as lfsr
from tkinter import filedialog


def enc_func(path_0):
    with open(path_0, 'rb') as file_0:
        file_code = file_0.read()

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

    enc_data = (map(lambda a, b: a ^ b, file_code, gamma))

    enc_path = os.path.splitext(path_0)[0] + '_enc' + os.path.splitext(path_0)[1]

    with open(enc_path, 'wb+') as file_1:
        file_1.write(bytes(enc_data))


name_0 = filedialog.askopenfilename()
enc_func(name_0)
