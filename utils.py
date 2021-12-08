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
    bytes_arr = bytearray()
    while len(bytes_arr) < file_size:
        data = sock.recv(file_size - len(bytes_arr))
        bytes_arr.extend(data)
    return bytes_arr


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
    if os.path.exists(full_path):
        os.rmdir(full_path)


# this method will receive from the given socket all the files and folder recursively
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
# by sending all the files to the client recursively.
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


def rec_folder_move(dest, src, home):
    os.makedirs(os.path.join(home, dest))
    for root, dirs, files in os.walk(os.path.join(home, src)):
        for name in files:
            rel_path = os.path.relpath(os.path.join(root, name), home)
            move_file(os.path.join(root, name), os.path.join(dest, rel_path))
        for name in dirs:
            rel_path = os.path.relpath(os.path.join(root, name), home)
            os.makedirs(os.path.join(dest, rel_path))
    rec_folder_delete(home, src)


def created_event(sock, file_type, home_path, path):
    if file_type == "folder":
        if not os.path.exists(os.path.join(home_path, path)):
            os.makedirs(os.path.join(home_path, path))
    else:
        size = int.from_bytes(sock.recv(4), 'big')
        f = open(os.path.join(home_path, path), "wb")
        f.write(recv_file(sock, size))
        f.close()


def deleted_event(file_type, home_path, path):
    if os.path.exists(os.path.join(home_path, path)):
        if file_type == "folder":
            rec_folder_delete(home_path, path)
        else:
            os.remove(os.path.join(home_path, path))


def modified_event(sock, home_path, path):
    size = int.from_bytes(sock.recv(4), 'big')
    f = open(os.path.join(home_path, path), "wb")
    f.write(recv_file(sock, size))
    f.close()


def moved_event(file_type, home_path, path):
    src, dest = str(path).split('>')
    if os.path.exists(os.path.join(home_path, src)):
        if os.path.dirname(src) == os.path.dirname(dest):
            if os.path.exists(os.path.join(home_path, dest)) and file_type == "folder":
                if os.path.exists(os.path.join(home_path, src)):
                    os.rmdir(os.path.join(home_path, src))
                return
            os.renames(os.path.join(home_path, src), os.path.join(home_path, dest))
            return
        if file_type == "folder":
            rec_folder_move(dest, src, home_path)
        else:
            if not os.path.exists(os.path.join(home_path, os.path.dirname(dest))):
                os.makedirs(os.path.join(home_path, os.path.dirname(dest)))
            move_file(os.path.join(home_path, src), os.path.join(home_path, dest))
            os.remove(os.path.join(home_path, src))


def move_file(src_path, dest_path):
    src_file = open(src_path, "rb")
    dest_file = open(dest_path, "wb")
    dest_file.write(src_file.read())
    src_file.close()
    dest_file.close()
