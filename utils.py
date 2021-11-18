def recv_file(sock, file_size):
    bytes = bytearray()
    while len(bytes) < file_size:
        data = sock.recv(file_size - len(bytes))
        bytes.extend(data)
    return bytes