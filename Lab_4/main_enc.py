import encryption

e, n, d = 84671, 66677


def main_enc(e, n):
    text = "ааааааааааааа праздник"
    text = text.upper()
    C = encryption.enc(e, n, text)
    return C


main_enc(e, n)
