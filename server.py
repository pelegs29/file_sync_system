import socket
import random
import string
import os


def list_dirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


def generate_user_identifier():
    return ''.join(random.choice(string.digits + string.ascii_letters) for i in range(128))


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)
while True:
    client_socket, client_address = server.accept()
    client_id = client_socket.recv(128)
    folders_list = list_dirs(os.getcwd())
    if client_id in folders_list:
        client_socket.send("OLD".encode())
        for path, dirs, files in os.walk(client_id):
            for file in files:
                filename = os.path.join(path, file)
                relpath = os.path.relpath(filename, client_id)
                filesize = os.path.getsize(filename)
                with open(filename, 'rb') as f:
                    client_socket.sendall(relpath.encode() + b'\n')
                    client_socket.sendall(str(filesize).encode() + b'\n')

                    # Send the file in chunks so large files can be handled.
                    while True:
                        data = f.read()
                        if not data:
                            break
                        client_socket.sendall(data)
    else:
        os.makedirs(generate_user_identifier(), exist_ok=True)

    client_socket.close()
    print('Client disconnected')
