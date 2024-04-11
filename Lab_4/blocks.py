import assistant_functions as af


def split_string_into_blocks(text, modulus):

    block_size = len(str(modulus))
    blocks = []

    for i in range(0, len(text), block_size):
        block = text[i:i + block_size]
        if int(block) >= modulus:
            blocks.append(block[:-1])
        else:
            blocks.append(block)



    return blocks


def enc_blocks(text, mod):
    str_num = af.text_to_num(text)
    U = split_string_into_blocks(str_num, mod)
    blocks_list = list(map(int, U))


    return blocks_list


def dec_blocks(text):
    str_num = af.num_to_text_2(text)

    print(f"str_num = {str_num}")

    return str_num
