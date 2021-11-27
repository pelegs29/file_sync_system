import os


# input check - raise exception if the port given is not a five digits number
def port_check(port_input):
    if len(str(port_input)) != 5 or not str(port_input).isnumeric():
        raise Exception("Given port is not valid")


def recv_file(sock, file_size):
    bytes = bytearray()
    while len(bytes) < file_size:
        data = sock.recv(file_size - len(bytes))
        bytes.extend(data)
    return bytes


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


def protocol_sender(sock, pro_string):
    sock.send(len(pro_string).to_bytes(4, 'big'))
    sock.send(pro_string.encode())


def win_to_lin(path):
    if os.name == 'nt':
        if '/' in path:
            return path.replace('/', '\\')
    else:
        if '\\' in path:
            return path.replace('\\', '/')
    return path
