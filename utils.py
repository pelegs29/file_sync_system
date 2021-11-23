import os


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
