import blocks as bl
import assistant_functions as af


def enc(e, n, text):  # Шифрование


    C = []
    M = bl.blocks(text, n)

    for i in range(len(M)):
        C.append(af.fast_pow(M[i], e) % n)

    C_str = af.list_to_str(C)
    C_text = af.num_to_text(C_str)

    return C_text
