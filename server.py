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
    folders_list = list_dirs('')
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
        client_socket.send("NEW".encode())
        with server, server.makefile('rb') as file:
            while True:
                raw = file.readline()
                if not raw:
                    break  # no more files, server closed connection.

                filename = raw.strip().decode()
                length = int(file.readline())
                # change path.
                path = os.path.join('client', filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)

                # Read the data in chunks so it can handle large files.
                with open(path, 'wb') as f:
                    while length:
                        chunk = length
                        data = file.read(chunk)
                        if not data:
                            break
                        f.write(data)
                        length -= len(data)
                    else:  # only runs if while doesn't break and length==0
                        continue
    client_socket.close()
