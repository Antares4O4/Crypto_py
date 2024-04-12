import random
import math
import assistant_functions as af

p, q = 227, 373
n = p * q
phi = (p - 1) * (q - 1)

print(f"phi(n) = {phi}")


def generate_d(a):  # Генерация d
    while True:
        d = random.randint(2, a)
        if math.gcd(a, d) == 1:
            return d


def keys_main():
    d1, d2, d3 = generate_d(phi), generate_d(phi), generate_d(phi)

    e1, e2, e3 = af.multiplicative_inverse(d1, phi), af.multiplicative_inverse(d2, phi), af.multiplicative_inverse(d3,
                                                                                                                   phi)

    print(
        "\nВыберите пару открытый ключ/закрытый ключ (пары распалагаются следующим образом [[e1, n, d1, n], [e2, n, d2, "
        "n], [e3, n, d3, n]]):")

    keys = [[e1, n, d1, n], [e2, n, d2, n], [e3, n, d3, n]]

    print(keys)

    i = True
    while i:
        flag = input("\nВведите номер пары (число от 1 до 3 включительно):")

        if flag == "1":
            print(f"\nВы выбрали пару {keys[0]}.")
            i = False
            return keys[0]


        elif flag == "2":
            print(f"\nВы выбрали пару {keys[1]}.")
            i = False
            return keys[1]

        elif flag == "3":
            print(f"\nВы выбрали пару {keys[2]}.")
            i = False
            return keys[2]

        else:
            print("\nНекорректный номер пары,введите корректный номер пары:")
