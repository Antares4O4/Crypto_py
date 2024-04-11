import assistant_functions as af


def dec(d, n, C):  # Дешифрование

    print(f"d = {d}, n = {n}")

    M = []

    for i in range(len(C)):
        M.append(af.fast_pow(C[i], d) % n)

    M_str = af.add_zero_if_less_than_n(M, n)

    M = af.num_to_str(M_str)

    M = af.num_to_text_2(M)

    return M
