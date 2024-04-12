import blocks as bl
import assistant_functions as af


def dec(d, n, enc_blocks):  # Дешифрование
    M = []
    C = enc_blocks
    print(C)
    for i in range(len(C)):
        M.append((C[i] ** d) % n)
    print(M)
    M_str = af.list_to_str(M)
    M = af.num_to_text_dec(M_str)

    return M
