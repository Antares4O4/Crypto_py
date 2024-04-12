import blocks as bl
import assistant_functions as af


def dec(d, n, text):  # Дешифрование



    M = []

    C = bl.blocks(text, n)
    print(f"C = {C}")
    for i in range(len(C)):
        M.append(af.fast_pow(C[i], d) % n)
    print(f"M = {M}")
    M_str = af.list_to_str(M)
    print(M_str)
    M = af.num_to_text_3(M_str)

    return M
