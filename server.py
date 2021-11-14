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
    else:
        client_socket.send("NEW".encode())
        user_id = generate_user_identifier()
        client_socket.send(user_id.encode())
        os.makedirs(user_id, exist_ok=True)
        os.chdir(os.path.join(os.getcwd(), user_id))
        # TODO test large files.
        while True:
            data = client_socket.recv(1024).decode("UTF-8", 'strict')
            file_type, file_name, file_size = data.split(',')
            if file_type == "file":
                f = open(file_name, "wb")
                data = client_socket.recv(int(file_size))
                f.write(data)
                f.close()
            elif file_type == "folder":
                os.makedirs(file_name, exist_ok=True)
                os.chdir(os.path.join(os.getcwd(), file_name))
            else:
                break
    client_socket.close()
