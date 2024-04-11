import blocks as bl
import assistant_functions as af


def enc(e, n, text):  # Шифрование
    print(f"e = {e}, n = {n}")

    C = []
    M = bl.enc_blocks(text, n)

    for i in range(len(M)):
        C.append(af.fast_pow(M[i], e) % n)

    C_str = af.num_to_str(C)
    C_text = af.num_to_text(C_str)

    print(f"Зашифрованный текст = {C_text}")

    return C
