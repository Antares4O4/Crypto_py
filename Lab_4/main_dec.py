import decryption

e, n, d = 51173, 84671, 66677


def main_dec(d, n):
    enc_blocks = "Н4ОН4ОН4ОН4ОН4ОН4О65645468544ЦЖЗ483"
    M = decryption.dec(d, n, enc_blocks)
    print(f"Расшифрованное сообщение = {M}")


main_dec(d, n)
