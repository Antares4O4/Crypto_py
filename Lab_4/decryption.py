import blocks as bl
import assistant_functions as af


def dec(d, n, text):  # Дешифрование

    print(f"d = {d}, n = {n}")

    M = []

    C = bl.blocks(text, n)

    for i in range(len(C)):
        M.append(af.fast_pow(C[i], d) % n)

    M_str = af.list_to_str(M)

    M = af.num_to_text(M_str)

    return M
