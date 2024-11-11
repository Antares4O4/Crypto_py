import rsa

# Генерация ключей RSA (публичного и приватного)
(public_key, private_key) = rsa.newkeys(512)

# Сохранение публичного ключа в файл
with open("public_key.pem", "wb") as f:
    f.write(public_key.save_pkcs1())

# Сохранение приватного ключа в файл
with open("private_key.pem", "wb") as f:
    f.write(private_key.save_pkcs1())

print("Ключи успешно сгенерированы и сохранены в файлы.")
