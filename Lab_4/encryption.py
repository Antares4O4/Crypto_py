import blocks as bl
import assistant_functions as af


def enc(e, n, text):  # Шифрование

    C = []
    M = bl.blocks(text, n)
    for i in range(len(M)):
        C.append((M[i] ** e) % n)
    print(C)
    C_str = af.list_to_str(C)
    C_text = af.num_to_text_enc(C_str)
    print(f"Зашифрованный текст = {C_text}")
    return str(C)
