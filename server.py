import socket
import random
import string
import os
import sys
from utils import *


# input check - raise exception if the program args count isn't 1.
def args_num_check():
    if len(sys.argv) != 2:
        raise Exception("Only 1 argument allowed.")


# method to update the client of changes that has been made by other computers
# this method also handle the case when the server needs to send a file to the client
def update_client():
    for s in changes_map.get(user_id).get(pc_id):
        protocol_sender(client_socket, s)
        event_type, file_type, path = s.split(',')
        path = win_to_lin(path)
        # if the event is a creation or modification of a file, this file needs to be sent to the client
        if (event_type == "created" or event_type == "modified") and file_type == "file":
            if not os.path.exists(os.path.join(os.getcwd(), path)):
                continue
            client_socket.send(os.path.getsize(os.path.join(os.getcwd(), path)).to_bytes(4, 'big'))
            f = open(os.path.join(os.getcwd(), path), "rb")
            client_socket.send(f.read())
            f.close()
    changes_map.get(user_id)[pc_id] = []
    protocol_sender(client_socket, "0,0,0")


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
    path = win_to_lin(path)
    if file_type == "file" and os.path.isdir(os.path.join(os.getcwd(), path)):
        file_type = "folder"
        data = event_type + "," + file_type + "," + path
    if event_type == "modified" and file_type == "folder":
        return
    else:
        for comp_id, change_list in changes_map[user_id].items():
            if comp_id != pc_id:
                change_list.append(data)
                print(str(pc_id) + " : " + data)
    if event_type == "created":
        if file_type == "folder":
            if not os.path.exists(os.path.join(os.getcwd(), path)):
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
                rec_folder_delete(os.getcwd(), src)
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

# init of the changes and pc id counter databases
changes_map = dict()
counter_map = dict()

# sets the current dir and empty user id
current_dir = os.getcwd()
user_id = ""

# socket init
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)

# this is the main loop of the server,
# each iteration: 1) reset the current dir to the main folder of the server.
#                 2) the server accepts a client and receive a protocol from the client.
#                 3) analyze the protocol and update the client id, pc id, and given operation.
#                 4) operate accordingly to the given client ID ( new / old / old with new PC ).
#                   4.1) new client -> create query in the change_map, and create changes list,
#                                      then push client's folder to the server.
#                   4.2) old client -> preforms this actions :
#                       4.2.1) if client logged from new PC -> increment counter_map of client ID,
#                                                              and add query for the new PC in the changes_map.
#                       4.2.2) set current dir to the client ID dir.
#                       4.2.3) operate accordingly to the given operation ID ( 0 / 1 / 2 )
#                           4.2.3.1) operation ID == 0 -> this is the first connection,
#                                                         pulls everything from the server.
#                           4.2.3.2) operation ID == 1 -> client is seeking for updates from the server.
#                           4.2.3.3) operation ID == 2 -> client is pushing an update to the server.
while True:
    os.chdir(current_dir)
    client_socket, client_address = server.accept()
    protocol_size = int.from_bytes(client_socket.recv(4), 'big')
    data = client_socket.recv(protocol_size).decode("UTF-8", 'strict')
    client_id, pc_id, operation = data.split(',')
    pc_id = int(pc_id)
    folders_list = list_dirs(os.getcwd())
    # check if the id given has been registered before
    if client_id in folders_list:
        # check if this connection is from a new computer
        if pc_id not in changes_map.get(user_id).keys():
            counter_map[user_id] += 1
            pc_id = counter_map.get(user_id)
            client_socket.send(pc_id.to_bytes(4, 'big'))
            (changes_map[user_id])[pc_id] = []
        os.chdir(os.path.join(current_dir, user_id))
        # handle update from client
        if operation == "2":
            event(client_socket)
        # updates the client of changes, if they exist:
        # if there are changes, send 1. otherwise send 0.
        elif operation == "1":
            if len(changes_map.get(user_id).get(pc_id)) == 0:
                client_socket.send("0".encode())
            else:
                client_socket.send("1".encode())
                update_client()
        # this is the first connection of an existing client.
        else:
            rec_bulk_send(client_socket, os.getcwd())

    # if this is a new client -> set up a new query in the change_map and
    # save his data in the server.
    else:
        # generate and send newly created ID to the client.
        user_id = generate_user_identifier()
        print(user_id)
        os.makedirs(user_id)
        os.chdir(os.path.join(current_dir, user_id))
        client_socket.send(user_id.encode())
        client_socket.send(int(1).to_bytes(4, 'big'))

        # setup new query to the user id and the pc id
        counter_map[user_id] = 1
        changes_map[user_id] = dict()
        pc_id = counter_map.get(user_id)
        (changes_map[user_id])[pc_id] = []

        # get all files from the client
        rec_bulk_recv(client_socket)
    client_socket.close()
