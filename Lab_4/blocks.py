import assistant_functions as af


def split_string_into_blocks(str_num_text, n):
    lenth = len(str_num_text)
    blocks = []

    while lenth > 0:
        i = 1
        block = str_num_text[:i]

        while int(str_num_text[:i]) < n and i <= lenth:
            block = str_num_text[:i]
            i += 1

        if i <= lenth and str_num_text[i - 1] == "0":
            i -= 1
            block = block[:-1]

        str_num_text = str_num_text[i - 1:]
        lenth -= i - 1
        blocks.append(block)

    return blocks


def enc_blocks(text, mod):
    str_num = af.text_to_num_3(text)
    U = split_string_into_blocks(str_num, mod)
    blocks_list = list(map(int, U))
    return blocks_list


def split_string_into_blocks_2(text, modulus):
    block_size = len(str(modulus))
    blocks = []

    for i in range(0, len(text), block_size):
        block = text[i:i + block_size]
        if int(block) >= modulus:
            blocks.append(block[:-1])
        else:
            blocks.append(block)
    return blocks


def dec_blocks(text, mod):
    str_num = af.text_to_num_3(text)
    U = split_string_into_blocks(str_num, mod)
    blocks_list = list(map(int, U))
    return blocks_list
