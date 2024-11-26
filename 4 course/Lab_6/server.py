# server.py
import socket
import json
import threading
from common import generate_shares, share_to_binary, reconstruct_from_shares, verify_secret


class SecretServer:
    def __init__(self, secret_point):
        self.secret = secret_point
        self.clients = []
        self.shares = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', 5000))
        self.sock.listen(3)

        # Генерируем доли и проверяем их корректность
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            try:
                # Генерируем плоскости
                self.plane_shares = generate_shares(secret_point, 3)

                # Проверяем уникальность
                if len(set(self.plane_shares)) != 3:
                    raise ValueError("Non-unique shares generated")

                # Проверяем восстановление
                test_secret = reconstruct_from_shares(self.plane_shares)
                if test_secret != secret_point:
                    raise ValueError("Incorrect reconstruction")

                # Проверяем, что все плоскости проходят через точку
                if not verify_secret(secret_point, self.plane_shares):
                    raise ValueError("Planes don't intersect at secret point")

                # Если все проверки пройдены, конвертируем в бинарный формат
                self.binary_shares = [share_to_binary(share) for share in self.plane_shares]
                print("Successfully generated and verified shares")
                break

            except Exception as e:
                attempt += 1
                if attempt == max_attempts:
                    raise ValueError(f"Failed to generate valid shares after {max_attempts} attempts")
                continue

    def start(self):
        """Запуск сервера и обработка подключений клиентов"""
        print(f"Server started with secret point: {self.secret}")
        share_index = 0

        while len(self.clients) < 3:
            client, addr = self.sock.accept()
            self.clients.append(client)

            # Отправляем бинарную долю секрета (коэффициенты плоскости)
            share = self.binary_shares[share_index]
            self.shares[addr] = share

            client.send(json.dumps({
                "type": "share",
                "data": share
            }).encode())

            print(f"Client connected: {addr}")
            print(f"Sent plane coefficients (binary): {share[:50]}...")

            threading.Thread(target=self.handle_client,
                             args=(client, addr)).start()
            share_index += 1

    def handle_client(self, client, addr):
        """Обработка сообщений от клиента"""
        # Множество для отслеживания уже отправленных долей этому клиенту
        sent_shares = set()

        while True:
            try:
                data = client.recv(1024).decode()
                if not data:
                    break

                msg = json.loads(data)
                if msg['type'] == 'request_share':
                    # Отправляем только те доли, которые еще не отправляли этому клиенту
                    for other_addr, share in self.shares.items():
                        if other_addr != addr and share not in sent_shares:
                            response = {
                                'type': 'share',
                                'data': share
                            }
                            client.send(json.dumps(response).encode())
                            sent_shares.add(share)
                            print(f"Sending share to {addr}")

                elif msg['type'] == 'chat':
                    # Рассылаем сообщение всем клиентам кроме отправителя
                    for other_client in self.clients:
                        if other_client != client:
                            response = {
                                'type': 'chat',
                                'message': msg['message']
                            }
                            other_client.send(json.dumps(response).encode())

            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break

        self.clients.remove(client)
        client.close()