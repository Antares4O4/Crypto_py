import blocks as bl
import assistant_functions as af


def dec(d, n, text):  # Дешифрование

    M = []
    C = bl.dec_blocks(text, n)
    print(f"Блоки зашифрованные = {C}")
    for i in range(len(C)):
        M.append((pow(C[i], d) % n))

    print(f"Блоки дешифрованные = {M}")
    M_str = af.list_to_str(M)
    M = af.num_to_text_dec(M_str)

    return M
