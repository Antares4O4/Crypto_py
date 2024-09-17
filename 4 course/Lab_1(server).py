import socket

# Настройки сервера
SERVER_HOST = '127.0.0.1'  # Локальный хост
SERVER_PORT = 12345  # Порт для прослушивания

# Создание TCP сокета
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Привязка сокета к хосту и порту
server_socket.bind((SERVER_HOST, SERVER_PORT))

# Перевод сервера в режим прослушивания
server_socket.listen(1)
print(f"Сервер слушает на {SERVER_HOST}:{SERVER_PORT}...")

# Ожидание подключения клиента
client_socket, client_address = server_socket.accept()
print(f"Клиент {client_address} подключился.")

# Основной цикл для получения и отправки сообщений
while True:
    # Получение сообщения от клиента
    message = client_socket.recv(1024).decode()
    if message.lower() == 'exit':
        print("Клиент отключился.")
        break

    print(f"Сообщение от клиента: {message}")

    # Ответ клиенту
    server_response = input("Введите ответ для клиента: ")
    client_socket.send(server_response.encode())

# Закрытие соединений
client_socket.close()
server_socket.close()