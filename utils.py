import os


# this method will get path and manipulate it according to the current os the program runs on.
def win_to_lin(path):
    if os.name == 'nt':
        if '/' in path:
            return path.replace('/', '\\')
    else:
        if '\\' in path:
            return path.replace('\\', '/')
    return path


# input check - raise exception if the port given is not a five digits number
def port_check(port_input):
    if len(str(port_input)) != 5 or not str(port_input).isnumeric():
        raise Exception("Given port is not valid")


# this method will get string and socket as args and make sure that the receiver will know exactly
# the amount of bytes required to read the message that about to be sent,
# by sending first the string length in bytes, then the encoded string itself.
def protocol_sender(sock, pro_string):
    sock.send(len(pro_string).to_bytes(4, 'big'))
    sock.send(pro_string.encode())


# this method handle receiving a file using the given information about its size in bytes,
# by calculating the maximum amount needed to be pulled at the socket at each time.
def recv_file(sock, file_size):
    bytes = bytearray()
    while len(bytes) < file_size:
        data = sock.recv(file_size - len(bytes))
        bytes.extend(data)
    return bytes


# this method will receive a path and a relative path and will delete its content recursively
def rec_folder_delete(path, rel_path):
    path = win_to_lin(path)
    rel_path = win_to_lin(rel_path)
    full_path = os.path.join(path, rel_path)
    for root, dirs, files in os.walk(full_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(full_path)


# this method will receive from the given socket all of the files and folder recursively
def rec_bulk_recv(sock):
    while True:
        data_size = int.from_bytes(sock.recv(4), 'big')
        data = sock.recv(data_size).decode("UTF-8", 'strict')
        file_type, file_rel_path, file_size = data.split(',')
        file_rel_path = win_to_lin(file_rel_path)
        if file_type == "file":
            f = open(file_rel_path, "wb")
            f.write(recv_file(sock, int(file_size)))
            f.close()
        elif file_type == "folder":
            os.makedirs(file_rel_path, exist_ok=True)
        else:
            break


# this method handles the case when we accept an existing user,
# by sending all of the files to the client recursively.
def rec_bulk_send(sock, fold_path):
    for path, dirs, files in os.walk(fold_path):
        for file in files:
            file_path = os.path.join(path, file)
            file_name = os.path.relpath(file_path, fold_path)
            file_size = str(os.path.getsize(file_path))
            protocol = "file," + file_name + "," + file_size
            protocol_sender(sock, protocol)
            f = open(file_path, "rb")
            sock.send(f.read())
        for folder in dirs:
            fol_path = os.path.join(path, folder)
            folder_name = os.path.relpath(fol_path, fold_path)
            folder_size = str(0)
            protocol = "folder," + folder_name + "," + folder_size
            protocol_sender(sock, protocol)
    protocol_sender(sock, "0,0,0")
