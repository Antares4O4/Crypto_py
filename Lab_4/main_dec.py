import decryption

e, n, d = 51173, 84671, 66677


def main_dec(d, n):
    enc_blocks = [38602, 23602, 13721, 57026, 1603, 78084, 26664, 45217, 76163, 18464, 71181, 4775, 78241, 20905, 33125,
                  39606, 78241, 77460, 73650]
    M = decryption.dec(d, n, enc_blocks)
    print(f"Расшифрованное сообщение = {M}")


main_dec(d, n)
