from socket import socket, AF_INET, SOCK_DGRAM, timeout
import sys


# input check - raise exception if the program args count isn't 3
if len(sys.argv) != 4:
    raise Exception("Only 3 args allowed")


# input check - raise exception if one of the condition is met :
# -> there are less or more than 4 dots in the ip address
# -> there is a section in the ip that not contains only numbers
# -> there are less then 1 or more than 4 numbers in each section of the op
def ip_check(ip_input):
    ip_parts = str(ip_input).split(".")
    if len(ip_parts) != 4:
        raise Exception("Given ip is not valid")
    for part in ip_parts:
        if len(part) not in range(1, 4) or not part.isnumeric():
            raise Exception("Given ip is not valid")


# input check - raise exception if the port given is not a five digits number
def port_check(port_input):
    if len(str(port_input)) != 5 or not str(port_input).isnumeric():
        raise Exception("Given port is not valid")


# running input checks
ip_check(sys.argv[1])
port_check(sys.argv[2])

# socket init with timeout of 5 seconds
s = socket(AF_INET, SOCK_DGRAM)
s.settimeout(5)

# argument 1 -> ip address
# argument 2 -> port
# argument 3 -> input file name in folder
port = int(sys.argv[2])
file = open(sys.argv[3], 'rb')

# input check - checks if the given file size is not exceeding 50,000 bytes
file.seek(0, 2)
file_size = file.tell()
if file_size > 50000:
    raise Exception("Sorry, file is exceeding 50,000 bytes ")
file = open(sys.argv[3], 'rb')

# in this part we create our protocol. we read 95 bytes and concat empty 5 bytes at the beginning,
# then we split the protocol to two parts : the header with the packet number and the data.
# and in the last step we increment the packet number in the header and rebuild the packet parts all together.
chunk = file.read(95)
chunk = bytes(5) + chunk
num_packet = int.from_bytes(chunk[:5], "big")
chunk = chunk[5:]
num_packet = num_packet + 1
chunk = num_packet.to_bytes(5, 'big') + chunk

# this while loop iterate as long as there are more chucks of 95 byte to read from the input file,
# in each iteration we are sending a packet to the server then waiting for confirmation from it,
# if no confirmation has benn sent back (socket timeout) we send the packet once again.
# otherwise, a packet has been received and the program will compare the packet given from the server
# to the packet we as a client sent.
# in the case that the confirmation packet doesn't match the one we have sent, we send out packet again and
# waiting for another confirmation packet.
# if the confirmation packet indeed match ours, we read another 95 bytes from the file,
# adding a header with the incremented number packet and iterate again.

while chunk:
    s.sendto(chunk, (sys.argv[1], port))
    try:
        data_recv, addr = s.recvfrom(1024)
    except timeout:
        continue
    while data_recv != chunk:
        s.sendto(chunk, (sys.argv[1], port))
        try:
            valid, addr = s.recvfrom(1024)
        except timeout:
            continue
    chunk = file.read(95)
    # check if the file has more bytes to be read.
    if chunk == b'':
        break
    chunk = bytes(5) + chunk
    chunk = chunk[5:]
    num_packet = num_packet + 1
    chunk = num_packet.to_bytes(5, 'big') + chunk

file.close()
final_msg = 501

# after sending the last packet, we notify the server that the packet he just got was the last one,
# by sending him a packet with the number 501, which represents according to our protocol the last
# packet.
# The client will terminate when we get a message from the server that he got the packet with
# number 501.
s.sendto(final_msg.to_bytes(5, 'big'), (sys.argv[1], port))
end_client = b'0'
while end_client != final_msg.to_bytes(5, 'big'):
    try:
        end_client, addr = s.recvfrom(5)
    except timeout:
        continue

s.close()
file.close()
