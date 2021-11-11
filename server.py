# This file is the server file.
# Eliran Eiluz 313268146 and Peleg Shlomo 318509700

# The timout import is used because the usage of the method "settimeout".
from socket import socket, AF_INET, SOCK_DGRAM, timeout
import sys


# input check - Check that the user sent only one argument.
if len(sys.argv) != 2:
    raise Exception("Only 1 argument allowed.")


# input check - In case we got one argument as expected, check that it's length is 5 and it contains
# only numbers, as this argument is a port, and port is a 5-digits number.
def port_check(port_input):
    if len(str(port_input)) != 5 or not str(port_input).isnumeric():
        raise Exception("Given port is not valid")


# Checking the validity of the port argument and creating socket.
port_check(sys.argv[1])
s = socket(AF_INET, SOCK_DGRAM)

# client_addr is used to save the IP address of the client.
client_addr = 0

# the number 501 representing the last package.
final_packet = 501

# Make the socket wait to a package when using the "recvfrom" method to 5 seconds.
s.settimeout(5)
port = int(sys.argv[1])
s.bind(('', port))

# This is a packet counter.using this counter we can check that the packet we just received is the packet
# the server is waiting for.
current_packet = 1

# The operation of the while-loop:
# First, the server is waiting for a packet for 5 seconds. if he doesn't get one, the "recvfrom" method will throw
# an Exception, so we catch it and trying to get a packet again.
# Once we get a packet, we take it's five first bytes, because according to the protocol we made, the first 5 bytes
# of every packet represents it's number. after getting the packet's number, we check that the number of the packet
# is the number of the packet the server is waiting for. If it is, we send it back to the client, and increasing the
# packet counter variable, "current_packet".
# If not, we throw it away and trying to receive the next packet.
# In case the packet number is 501, it means that it's the last packet the client sends.
while True:
    try:
        data, addr = s.recvfrom(1024)
    except timeout:
        continue
    client_addr = addr
    num_packet = int.from_bytes(data[:5], "big")
    chunk = data[5:]
    if num_packet == final_packet:
        break
    elif num_packet != current_packet:
        s.sendto(data, addr)
    else:
        s.sendto(data, addr)
        print(data[5:].decode("UTF-8", 'strict'), end="")
        current_packet = current_packet + 1

# sending to the client that we got the last packet.
while True:
    s.sendto(final_packet.to_bytes(5, 'big'), client_addr)
    try:
        data, addr = s.recvfrom(1024)
    except timeout:
        continue
