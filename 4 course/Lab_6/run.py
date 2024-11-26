# run.py
from server import SecretServer

if __name__ == "__main__":
    secret_point = (42, 23, 65)
    server = SecretServer(secret_point)
    server.start()