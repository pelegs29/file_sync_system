import socket
import random
import string
import os
import sys
from utils import *


# TODO: 1) check updating is working from server side
#       2) changing port every new socket
#       3) windows <-> linux
#       4) server needs tp print client id
#       5) check existing client behavior
#       6) fix double os.path.join


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
            f = open(file_path, "rb")
            client_socket.send(f.read())
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
    while True:
        data_size = int.from_bytes(client_sock.recv(4), 'big')
        data = client_sock.recv(data_size).decode("UTF-8", 'strict')
        file_type, file_name, file_size = data.split(',')
        if file_type == "file":
            f = open(file_name, "wb")
            f.write(recv_file(client_sock, int(file_size)))
            f.close()
        elif file_type == "folder":
            os.makedirs(file_name, exist_ok=True)
        else:
            break


# method to update the client of changes that has been made by other computers
# this method also handle the case when the server needs to send a file to the client
def update_client(update_list):
    for s in update_list:
        client_socket.send(len(s).to_bytes(4, 'big'))
        client_socket.send(s.encode())
        event_type, file_type, path = s.split(',')
        # if the event is a creation or modification of a file, this file needs to be sent to the client
        if (event_type == "created" or event_type == "modified") and file_type == "file":
            client_socket.send(os.path.getsize(os.path.join(os.getcwd(), path)).to_bytes(4, 'big'))
            f = open(os.path.join(os.getcwd(), path), "rb")
            client_socket.send(f.read())
            f.close()
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
        for comp_id, change_list in changes_map[user_id].items():
            if comp_id != pc_id:
                change_list.append(data)
    if event_type == "created":
        if file_type == "folder":
            os.makedirs(os.path.join(os.getcwd(), path))
        else:
            size = int.from_bytes(sock.recv(4), 'big')
            f = open(os.path.join(os.getcwd(), path), "wb")
            f.write(recv_file(sock, size))
            f.close()
    if event_type == "deleted":
        if file_type == "folder" and os.path.isdir(os.path.join(os.getcwd(), path)):
            rec_folder_delete(os.getcwd(), path)
        else:
            if os.path.isfile(os.path.join(os.getcwd(), path)):
                os.remove(os.path.join(os.getcwd(), path))
    if event_type == "modified":
        size = int.from_bytes(sock.recv(4), 'big')
        f = open(os.path.join(os.getcwd(), path), "wb")
        f.write(recv_file(sock, size))
        f.close()
    if event_type == "moved":
        src, dest = str(path).split('>')
        if os.path.exists(os.path.join(os.getcwd(), src)):
            if os.path.dirname(src) == os.path.dirname(dest):
                os.renames(src, dest)
                return
            if file_type == "folder":
                os.makedirs(os.path.join(os.getcwd(), dest))
                dest_path = os.path.join(os.getcwd(), dest)
                for root, dirs, files in os.walk(os.path.join(os.getcwd(), src)):
                    for name in files:
                        src_path = open(os.path.join(root, name), "rb")
                        f = open(os.path.join(dest_path, name), "wb")
                        f.write(src_path.read())
                        f.close()
                        src_path.close()
                    for name in dirs:
                        dest_path = os.path.join(dest_path, name)
                        os.makedirs(dest_path)
                rec_folder_delete(os.getcwd(), path)
            else:
                src_file = open(os.path.join(os.getcwd(), src), "rb")
                dest_file = open(os.path.join(os.getcwd(), dest), "wb")
                dest_file.write(src_file.read())
                src_file.close()
                dest_file.close()
                os.remove(os.path.join(os.getcwd(), src))


# input checks
args_num_check()
port_check(sys.argv[1])
port = int(sys.argv[1])
changes_map = dict()
counter_map = dict()
current_dir = os.getcwd()
user_id = ""
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)

# 0 - first connection
# 1 - get update from server
# 2- event


# this is the main loop of the server
# each iteration: 1) the current dir is resetting to the main folder of the server
#                 2) the server accepts a client with his ID, and operation number
#                 3) operate accordingly to the given ID ( new / old / old with new connection )
#                   3.1) new client -> create query in the change_map, and create changes list,
#                                      then push client's folder to the server.
#                   3.2) old client -> TODO : Continue
while True:
    os.chdir(current_dir)
    client_socket, client_address = server.accept()
    client_id, pc_id, operation = client_socket.recv(130).decode("UTF-8", 'strict').split(',')
    folders_list = list_dirs(os.getcwd())
    # check if the id given has been registered before
    if client_id in folders_list:
        # check if this connection is from a new computer
        if pc_id not in changes_map.get(user_id).keys():
            counter_map[user_id] += 1
            pc_id = counter_map.get(user_id)
            (changes_map[user_id])[pc_id] = []
        os.chdir(os.path.join(current_dir, user_id))
        if operation == "2":
            event(client_socket)
        elif operation == "1":
            if len(changes_map.get(user_id).get(pc_id)) == 0:
                client_socket.send("0".encode())
            else:
                client_socket.send("1".encode())
                update_client(changes_map.get(user_id).get(pc_id))
        else:
            existing_client(client_socket, os.getcwd())
    # if this is a new client -> set up a new query in the change_map and
    # save his data in the server.
    else:
        user_id = generate_user_identifier()
        os.makedirs(user_id)
        os.chdir(os.path.join(current_dir, user_id))
        counter_map[user_id] = 1
        changes_map[user_id] = dict()
        pc_id = counter_map.get(user_id)
        (changes_map[user_id])[pc_id] = []
        client_socket.send(user_id.encode())
        client_socket.send(pc_id.to_bytes(4, 'big'))
        new_client(client_socket)
    client_socket.close()
