import encryption

e, n, d = 51173, 84671, 66677

def main_enc(e, n):

    text = "Удивленная грусть с невесомым тончайшим телом"
    text = text.upper()
    C = encryption.enc(e, n, text)
    return C

main_enc(e, n)

