import os


def recv_file(sock, file_size):
    bytes = bytearray()
    while len(bytes) < file_size:
        data = sock.recv(file_size - len(bytes))
        bytes.extend(data)
    return bytes


def rec_folder_delete(path, rel_path):
    full_path = os.path.join(path, rel_path)
    for root, dirs, files in os.walk(full_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(full_path)
