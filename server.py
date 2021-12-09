import socket
import random
import string
import sys
from utils import *


# input check - raise exception if the program args count isn't 1.
def args_num_check():
    if len(sys.argv) != 2:
        raise Exception("Only 1 argument allowed.")


# the method handles the following case :
# created event and modified event (rename event) which are for the same file,
# in order to avoid trying to move the file from the wrong src path.
# this method will create new and merged changes map with only 1 creation event for each
# created and moved (renamed) events in the original changes map.
def event_merger():
    i = 0
    # creates a new change map and edit the new map.
    new_list = changes_map.get(user_id).get(pc_id).copy()
    while i < len(changes_map.get(user_id).get(pc_id)):
        j = i + 1
        while j < len(changes_map.get(user_id).get(pc_id)):
            event_i = changes_map.get(user_id).get(pc_id)[i]
            event_j = changes_map.get(user_id).get(pc_id)[j]
            event_type_i, file_type_i, path_i = event_i.split(',')
            event_type_j, file_type_j, path_j = event_j.split(',')
            # catch the 2 events which have the same file type and matching created and moved types
            if file_type_j == file_type_i:
                if event_type_j == "moved" and event_type_i == "created":
                    src, dest = path_j.split('>')
                    if path_i == src:
                        new_list[i] = "created," + file_type_i + "," + dest
                        new_list.remove(event_j)
                elif event_type_i == "moved" and event_type_j == "created":
                    src, dest = path_i.split('>')
                    if path_j == src:
                        new_list[j] = "created," + file_type_i + "," + dest
                        new_list.remove(event_i)
            j += 1
        i += 1
    changes_map.get(user_id)[pc_id] = new_list


# method to update the client of changes that has been made by other computers
# this method also handle the case when the server needs to send a file to the client
def update_client():
    event_merger()
    for s in changes_map.get(user_id).get(pc_id):
        event_type, file_type, path = s.split(',')
        path = win_to_lin(path)
        # if the event is a creation or modification of a file, this file needs to be sent to the client
        if (event_type == "created" or event_type == "modified") and file_type == "file":
            if not os.path.exists(os.path.join(os.getcwd(), path)):
                continue
            protocol_sender(client_socket, s)
            client_socket.send(os.path.getsize(os.path.join(os.getcwd(), path)).to_bytes(4, 'big'))
            f = open(os.path.join(os.getcwd(), path), "rb")
            client_socket.send(f.read())
            f.close()
        else:
            protocol_sender(client_socket, s)
    # reset the changes map and send an indicator protocol that this update round has ended.
    changes_map.get(user_id)[pc_id] = []
    protocol_sender(client_socket, "0,0,0")


# get all the folder names in certain path.
def list_dirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


# generate random user identifier which contains digits and letters.
def generate_user_identifier():
    return ''.join(random.choice(string.digits + string.ascii_letters) for i in range(128))


# this method will handle the event of getting updates from the client.
# at first receive protocol from the client about the event information and operate accordingly.
def event(sock):
    event_size = int.from_bytes(sock.recv(4), 'big')
    event_data = sock.recv(event_size).decode()
    event_type, file_type, path = event_data.split(',')
    path = win_to_lin(path)
    # if the event file type is file but in the current server state the file is directory
    # change the event file type to folder.
    if file_type == "file" and os.path.isdir(os.path.join(os.getcwd(), path)):
        file_type = "folder"
        event_data = event_type + "," + file_type + "," + path
    # in the following cases do not handle the event in the server :
    #   if the event is a modified of a folder.
    #   if the event is a deleted event of a file or folder that doesn't exist already.
    if (event_type == "modified" and file_type == "folder") or \
            (event_type == "deleted" and not os.path.exists(os.path.join(os.getcwd(), path))):
        return
    # in the following cases sent a false alarm indicator to the client :
    #   if the event is a created event and the path exists in the server.
    #   if the event is a modified event and the path doesn't exist in the server.
    # the false alarm indicator indicates the client that the event is flast alarm and cannot be continued.
    if (event_type == "created" and os.path.exists(os.path.join(os.getcwd(), path))) or \
            (event_type == "modified" and not os.path.exists(os.path.join(os.getcwd(), path))):
        sock.send(int(1).to_bytes(4, 'big'))
        return
    # add the event to all the computers change list of the same user id
    for comp_id, change_list in changes_map[user_id].items():
        if comp_id != pc_id:
            change_list.append(event_data)

    # handle each event by the event type and send confirmation to the client in created or modified events.
    if event_type == "created":
        if file_type == "file":
            sock.send(int(0).to_bytes(4, 'big'))
        created_event(sock, file_type, os.getcwd(), path)
    elif event_type == "deleted":
        deleted_event(file_type, os.getcwd(), path)
    elif event_type == "modified":
        sock.send(int(0).to_bytes(4, 'big'))
        modified_event(sock, os.getcwd(), path)
    else:
        moved_event(file_type, os.getcwd(), path)


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
server.listen(150)

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
    data = client_socket.recv(protocol_size).decode()
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
        # if there are changes, send 1. otherwise, send 0.
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

        # get all files from the client.
        rec_bulk_recv(client_socket)
    client_socket.close()
