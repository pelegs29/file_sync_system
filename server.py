import socket
import random
import string
import os
import sys


# input check - raise exception if the program args count isn't 1.
def args_num_check():
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
def existing_client(client_sock, fold_path):
    for path, dirs, files in os.walk(fold_path):
        for file in files:
            file_path = os.path.join(path, file)
            file_name = os.path.relpath(file_path, os.getcwd())
            file_size = str(os.path.getsize(file_path))
            protocol = "file," + file_name + "," + file_size
            protocol_size = len(protocol).to_bytes(4, 'big')
            client_sock.send(protocol_size)
            client_sock.send(protocol.encode())
            f = open(file_path, "r")
            client_socket.send(f.read().encode())
        for folder in dirs:
            fol_path = os.path.join(path, folder)
            folder_name = os.path.relpath(fol_path, path)
            folder_size = str(0)
            protocol = "folder," + folder_name + "," + folder_size
            protocol_size = len(protocol).to_bytes(4, 'big')
            client_sock.send(protocol_size)
            client_sock.send(protocol.encode())
    client_sock.send(len("0,0,0").to_bytes(4, 'big'))
    client_sock.send("0,0,0".encode())


# If we didn't get user_identifier as parameter, it means we are new clients and
# we should push the folder to the server.
def new_client(client_sock):
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
        else:
            break


def update_client(update_list):
    for s in update_list:
        client_socket.send(len(s).to_bytes(4, 'big'))
        client_socket.send(s.encode())
        event_type, file_type, path = s.split(',')
        if (event_type == "created" or event_type == "modified") and file_type == "file":
            client_socket.send(os.path.getsize(os.path.join(os.getcwd(), path)).to_bytes(4, 'big'))
            f = open(os.path.join(os.getcwd(), path))
            client_socket.send(f.read().encode())
    client_socket.send("0,0,0".encode())


# get all the folder names in certain path.
def list_dirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


# generate random user identifier which contains digits and letters.
def generate_user_identifier():
    return ''.join(random.choice(string.digits + string.ascii_letters) for i in range(128))


def event(sock):
    event_size = int.from_bytes(sock.recv(4), 'big')
    data = sock.recv(event_size).decode("UTF-8", 'strict')
    event_type, file_type, path = data.split(',')
    if event_type != "modified" and file_type != "folder":
        for client_add, change_list in changes_map[user_id].items():
            if client_add != client_address:
                change_list.append(data)
    if event_type == "created":
        if file_type == "folder":
            os.makedirs(os.path.join(os.getcwd(), path))
        else:
            size = int.from_bytes(sock.recv(4), 'big')
            f = open(os.path.join(os.getcwd(), path))
            f.write(sock.recv(size))
    if event_type == "deleted":
        if file_type == "folder":
            for root, dirs, files in os.walk(os.path.join(os.getcwd(), path), topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(os.path.join(os.getcwd(), path))
    if event_type == "modified":
        new_client(sock)
    # if event_type == "moved":
    # if file_type == "folder":
    #    new_client(sock)



# input checks
args_num_check()
port_check(sys.argv[1])
port = int(sys.argv[1])
changes_map = dict()
current_dir = os.getcwd()
user_id = ""
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)

# 0 - first connection
# 1 - get update from server
# 2- event

while True:
    os.chdir(current_dir)
    client_socket, client_address = server.accept()
    client_id, operation = client_socket.recv(130).decode("UTF-8", 'strict').split(',')
    folders_list = list_dirs(os.getcwd())
    if client_id in folders_list:
        if client_address not in changes_map.get(user_id).keys():
            (changes_map[user_id])[client_address] = []
        os.chdir(os.path.join(current_dir, user_id))
        if operation == "2":
            event(client_socket)
        elif operation == "1":
            if len(changes_map.get(user_id).get(client_address)) == 0:
                client_socket.send("0".encode())
            else:
                client_socket.send("1".encode())
                update_client(changes_map.get(user_id).get(client_address))
        else:
            existing_client(client_socket, os.getcwd())
    else:
        user_id = generate_user_identifier()
        os.makedirs(user_id)
        os.chdir(os.path.join(current_dir, user_id))
        changes_map[user_id] = dict()
        (changes_map[user_id])[client_address] = []
        client_socket.send(user_id.encode())
        new_client(client_socket)
    client_socket.close()
