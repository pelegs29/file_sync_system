import socket
import random
import string
import os
import sys


# input check - raise exception if the program args count isn't 1.
if len(sys.argv) != 2:
    raise Exception("Only 1 argument allowed.")


# input check - raise exception if the port given is not a five digits number
def port_check(port_input):
    if len(str(port_input)) != 5 or not str(port_input).isnumeric():
        raise Exception("Given port is not valid")


# If we got user_identifier as parameter, it means we are old clients and
# we should pull from the server the folder.
# we also use this method every time the "time_to_reach" passes, because we want to get
# the most updated version of the folder.
def existing_client(client_sock, path):
    for path, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(path, file)
            file_name = os.path.relpath(file_path, path)
            file_size = str(os.path.getsize(file_path))
            protocol = "file," + file_name + "," + file_size
            protocol_size = len(protocol).to_bytes(4, 'big')
            client_sock.send(protocol_size)
            client_sock.send(protocol.encode())
            f = open(file_path, "r")
            client_socket.send(f.read().encode())
        for folder in dirs:
            # path = os.path.join(path, folder)
            # folder_name = os.path.relpath(folder_path, folder_path)
            folder_size = str(0)
            protocol = "folder," + folder + "," + folder_size
            protocol_size = len(protocol).to_bytes(4, 'big')
            client_sock.send(protocol_size)
            client_sock.send(protocol.encode())
    client_sock.send(len("0,0,0").to_bytes(4, 'big'))
    client_sock.send("0,0,0".encode())


# If we didn't get user_identifier as parameter, it means we are new clients and
# we should push the folder to the server.
def new_client(client_sock):
    user_id = generate_user_identifier()
    client_sock.send(user_id.encode())
    os.makedirs(user_id, exist_ok=True)
    os.chdir(os.path.join(os.getcwd(), user_id))
    # TODO test large files.
    while True:
        data_size = int.from_bytes(client_sock.recv(4), 'big')
        data = client_sock.recv(data_size).decode("UTF-8", 'strict')
        file_type, file_name, file_size = data.split(',')
        if file_type == "file":
            f = open(file_name, "wb")
            data = client_sock.recv(int(file_size))
            f.write(data)
            f.close()
        elif file_type == "folder":
            os.makedirs(file_name, exist_ok=True)
            os.chdir(os.path.join(os.getcwd(), file_name))
        else:
            break


# def event(user_ident, client_sock):
#     data =


# get all the folder names in certain path.
def list_dirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


# generate random user identifier which contains digits and letters.
def generate_user_identifier():
    return ''.join(random.choice(string.digits + string.ascii_letters) for i in range(128))


port_check(sys.argv[1])
port = int(sys.argv[1])
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)
while True:
    client_socket, client_address = server.accept()
    client_id, operation = client_socket.recv(128).decode("UTF-8", 'strict').split(',')
    folders_list = list_dirs(os.getcwd())
    if client_id in folders_list:
        folder_path = os.path.join(os.getcwd(), client_id)
        if operation == "event":
            break
        else:
            existing_client(client_socket, folder_path)
    else:
        new_client(client_socket)
    client_socket.close()
