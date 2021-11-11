import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)
while True:
    client_socket, client_address = server.accept()
    client_id = client_socket.recv(100)
    client_socket.send(str("NEW").encode())
    with server, server.makefile('rb') as client_file:
        while True:
            folder = client_file.readline()
            # if client closes the connection we'll get folder = ''.
            if not folder:
                break

    client_socket.close()
    print('Client disconnected')
