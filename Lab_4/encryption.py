import blocks as bl
import assistant_functions as af


def enc(e, n, text):  # Шифрование

    C = []
    M = bl.enc_blocks(text, n)
    print(f"Блоки первоначального текста = {M}")
    for i in range(len(M)):
        C.append((pow(M[i],e)) % n)
    print(f"Зашифрованный блоки = {C}")
    C_str = af.list_to_str(C)
    C_text = af.num_to_text_enc(C_str)
    print(f"Зашифрованный текст = {C_text}")
    return C_text
