import os
from tkinter import filedialog
import encryption
import decryption

e, n, d = 78085, 84671, 2317


def main_enc(e, n, path_0):
    with open(path_0, 'r', encoding='utf-8') as f:
        text = f.read()

    C = encryption.enc(e, n, text)
    print(f"C = {C}")

    enc_path = os.path.splitext(path_0)[0] + '_enc' + os.path.splitext(path_0)[1]

    with open(enc_path, 'w') as file_1:
        file_1.write(C)


def main_dec(d, n, path_text_2):
    with open(path_text_2, 'r') as f:
        text = f.read()

    M = decryption.dec(d, n, text)

    dec_path = os.path.splitext(path_text_2)[0][:-4] + '_dec' + os.path.splitext(path_text_2)[1]

    with open(dec_path, 'w') as f_1:
        f_1.write(M)


name_1 = filedialog.askopenfilename()
main_enc(e, n, name_1)

name_2 = filedialog.askopenfilename()
main_dec(d, n, name_2)
