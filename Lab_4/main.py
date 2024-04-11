import encryption
import decryption
from keys import keys_main as key

e, n, d = key()[:-1]


def main_func(e, d, n):
    text = "пярпхфжыпгцяфцмцошещ"

    C = encryption.enc(e, n, text)

    M = decryption.dec(d, n, C)


main_func(e, d, n)
