import socket
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from utils import *


# input check - raise exception if the program args count isn't 4 or 5
def args_num_check():
    if len(sys.argv) != 5 and len(sys.argv) != 6:
        raise Exception("Only 4 or 5 arguments allowed.")


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


def time_to_reach_check(time_to_connect):
    try:
        float(time_to_connect)
    except ValueError:
        raise Exception("Given time to reach is not valid")


def new_client(sock, fol_path):
    for path, dirs, files in os.walk(fol_path):
        for file in files:
            file_path = os.path.join(path, file)
            file_name = os.path.relpath(file_path, fol_path)
            file_size = str(os.path.getsize(file_path))
            protocol = "file," + file_name + "," + file_size
            protocol_size = len(protocol).to_bytes(4, 'big')
            sock.send(protocol_size)
            sock.send(protocol.encode())
            f = open(file_path, "rb")
            sock.send(f.read())
        for folder in dirs:
            fold_path = os.path.join(path, folder)
            folder_name = os.path.relpath(fold_path, folder_path)
            folder_size = str(0)
            protocol = "folder," + folder_name + "," + folder_size
            protocol_size = len(protocol).to_bytes(4, 'big')
            sock.send(protocol_size)
            sock.send(protocol.encode())
    sock.send(len("0,0,0").to_bytes(4, 'big'))
    sock.send("0,0,0".encode())


# TODO change name of function
def old_client(sock):
    if os.getcwd() != folder_path:
        os.chdir(folder_path)
    # TODO test large files.
    while True:
        data_size = int.from_bytes(sock.recv(4), 'big')
        data = sock.recv(data_size).decode("UTF-8", 'strict')
        file_type, file_name, file_size = data.split(',')
        if file_type == "file":
            f = open(file_name, "wb")
            f.write(recv_file(sock, int(file_size)))
            f.close()
        elif file_type == "folder":
            os.makedirs(file_name, exist_ok=True)
        else:
            break


def update(sock):
    while True:
        size = int.from_bytes(sock.recv(4), 'big')
        data = sock.recv(size).decode("UTF-8", 'strict')
        if data == "0,0,0":
            break
        event_type, file_type, path = data.split(',')
        if event_type == "created":
            if file_type == "folder":
                os.makedirs(os.path.join(folder_path, path))
            else:
                size = int.from_bytes(sock.recv(4), 'big')
                f = open(os.path.join(folder_path, path), "wb")
                f.write(recv_file(sock, size))
                f.close()
        elif event_type == "deleted":
            if file_type == "folder":
                if os.path.isdir(os.path.join(folder_path, path)):
                    for root, dirs, files in os.walk(os.path.join(folder_path, path), topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(os.path.join(folder_path, path))
            else:
                if os.path.isfile(os.path.join(folder_path, path)):
                    os.remove(os.path.join(folder_path, path))
        elif event_type == "modified":
            if file_type == "file":
                size = int.from_bytes(sock.recv(4), 'big')
                f = open(os.path.join(folder_path, path), "wb")
                f.write(recv_file(sock, size))
                f.close()
        else:
            src, dest = str(path).split('>')
            if os.path.exists(os.path.join(folder_path, src)):
                if file_type == "folder":
                    os.makedirs(os.path.join(folder_path, dest))
                    for root, dirs, files in os.walk(os.path.join(folder_path, src)):
                        for name in files:
                            name = open(os.path.join(root, name), "rb")
                            f = open(os.path.join(folder_path, dest), "wb")
                            f.write(name.read())
                            f.close()
                            name.close()
                        for name in dirs:
                            os.makedirs(os.path.join(root, name))
                    for root, dirs, files in os.walk(os.path.join(folder_path, src), topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(os.path.join(folder_path, src))
                else:
                    src_file = open(os.path.join(folder_path, src), "rb")
                    dest_file = open(os.path.join(folder_path, dest), "wb")
                    dest_file.write(src_file.read())
                    src_file.close()
                    dest_file.close()
                    os.remove(os.path.join(folder_path, src))


# running input checks
args_num_check()
ip_check(sys.argv[1])
port_check(sys.argv[2])
time_to_reach_check(sys.argv[4])

# argument 1 -> ip address
# argument 2 -> port
# argument 3 -> input folder path
# argument 4 -> time to reach in seconds.
# argument 5 -> user identifier(optional).
ip = sys.argv[1]
port = int(sys.argv[2])
folder_path = os.path.abspath(sys.argv[3])
time_to_reach = float(sys.argv[4])
dog_flag = False
pc_id = 999

# in case the user did not entered user identifier, generate one with 128 chars with generate_user_identifier function.
if len(sys.argv) == 5:
    user_identifier = "NEW"
else:
    user_identifier = sys.argv[5]


class Watcher:
    DIRECTORY_TO_WATCH = folder_path

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(time_to_reach)
                global dog_flag
                dog_flag = True
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, port))
                sock.send((user_identifier + "," + str(pc_id) + ",1").encode())
                check = sock.recv(1).decode("UTF-8", 'strict')
                if check == "1":
                    update(sock)
                sock.close()
                dog_flag = False
        except Exception:
            self.observer.stop()
            print("error")
        self.observer.join()


def handle_event(event_type, file_type, sock, event):
    if event_type == "moved":
        rel_src_path = os.path.relpath(event.src_path, folder_path)
        rel_dest_path = os.path.relpath(event.dest_path, folder_path)
        rel_path = rel_src_path + ">" + rel_dest_path
    else:
        rel_path = os.path.relpath(event.src_path, folder_path)
    event_desc = event_type + "," + file_type + "," + rel_path
    sock.send(len(event_desc).to_bytes(4, 'big'))
    sock.send(event_desc.encode())
    if (event.event_type == "created" or "modified") and file_type == "file":
        if os.path.isfile(event.src_path):
            sock.send(os.path.getsize(event.src_path).to_bytes(4, 'big'))
            f = open(event.src_path, "rb")
            sock.send(f.read())
            f.close()
    # if event.event_type == "moved" and file_type == "folder":
    # new_client(sock, event.src_path)


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if (event.is_directory and event.event_type == "modified") or event.event_type == "closed":
            return None
        file_type = ""
        # global dog_flag
        if not dog_flag:
            event_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            event_sock.connect((ip, port))
            event_sock.send((user_identifier + "," + str(pc_id) + ",2").encode())
            if event.is_directory:
                file_type = "folder"
                if event.event_type == 'created':
                    handle_event(event.event_type, file_type, event_sock, event)
                elif event.event_type == 'moved':
                    handle_event(event.event_type, file_type, event_sock, event)
                elif event.event_type == 'deleted':
                    handle_event(event.event_type, file_type, event_sock, event)
            else:
                file_type = "file"
                if event.event_type == 'created':
                    handle_event(event.event_type, file_type, event_sock, event)
                elif event.event_type == 'modified':
                    handle_event(event.event_type, file_type, event_sock, event)
                elif event.event_type == 'moved':
                    handle_event(event.event_type, file_type, event_sock, event)
                elif event.event_type == 'deleted':
                    handle_event(event.event_type, file_type, event_sock, event)
            event_sock.close()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
protocol = user_identifier + "," + str(pc_id) + ",0"
s.send(len(protocol).to_bytes(4, 'big'))
s.send(protocol.encode())

# In case we are new client.
# TODO deal with folder names of ","
if user_identifier == "NEW":
    user_identifier = s.recv(128).decode("UTF-8", 'strict')
    pc_id = int.from_bytes(s.recv(4), 'big')
    new_client(s, folder_path)
else:
    old_client(s)

s.close()
w = Watcher()
w.run()
