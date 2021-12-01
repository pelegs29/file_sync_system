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


def time_to_reach_check(time_to_connect):
    try:
        float(time_to_connect)
    except ValueError:
        raise Exception("Given time to reach is not valid")



def update(sock):
    while True:
        size = int.from_bytes(sock.recv(4), 'big')
        data = sock.recv(size).decode("UTF-8", 'strict')
        if data == "0,0,0":
            break
        event_type, file_type, path = data.split(',')
        path = win_to_lin(path)
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
                    rec_folder_delete(folder_path, path)
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
                    dest_path = os.path.join(folder_path, dest)
                    for root, dirs, files in os.walk(os.path.join(folder_path, src)):
                        for name in files:
                            src_path = open(os.path.join(root, name), "rb")
                            f = open(os.path.join(dest_path, name), "wb")
                            f.write(src_path.read())
                            f.close()
                            src_path.close()
                        for name in dirs:
                            dest_path = os.path.join(dest_path, name)
                            os.makedirs(dest_path)
                    rec_folder_delete(folder_path, src)
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
                protocol_sender(sock, user_identifier + "," + str(pc_id) + ",1")
                check = sock.recv(1).decode("UTF-8", 'strict')
                if check == "1":
                    update(sock)
                sock.close()
                dog_flag = False
        except Exception as e:
            self.observer.stop()
            print(e)
        self.observer.join()


def handle_event(event_type, file_type, sock, event):
    if ".goutputstream" in event.src_path:
        src_path = event.dest_path
    else:
        src_path = event.src_path
    if event_type == "moved":
        rel_src_path = os.path.relpath(event.src_path, folder_path)
        rel_dest_path = os.path.relpath(event.dest_path, folder_path)
        rel_path = rel_src_path + ">" + rel_dest_path
    else:
        rel_path = os.path.relpath(src_path, folder_path)
    event_desc = event_type + "," + file_type + "," + rel_path
    protocol_sender(sock, event_desc)
    if (event.event_type == "created" or "modified") and file_type == "file":
        if os.path.isfile(src_path):
            sock.send(os.path.getsize(src_path).to_bytes(4, 'big'))
            f = open(src_path, "rb")
            sock.send(f.read())
            f.close()
    # if event.event_type == "moved" and file_type == "folder":
    # new_client(sock, event.src_path)


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if (event.is_directory and event.event_type == "modified") or event.event_type == "closed":
            return None
        if ".goutputstream" in event.src_path:
            if event.event_type == "created" or event.event_type == "modified":
                return None
            else:
                event.event_type = "modified"
        file_type = ""
        # global dog_flag
        if not dog_flag:
            event_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            event_sock.connect((ip, port))
            protocol_sender(event_sock, user_identifier + "," + str(pc_id) + ",2")
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
start_protocol = user_identifier + "," + "999" + ",0"
protocol_sender(s, start_protocol)

# client initial code before changes monitoring,
# if no user_ID given as args ->  inform the server and get a new ID, then upload all of the folder to the server
# else -> this is an existing user, create the folder and download all of the files from the server.
if user_identifier == "NEW":
    user_identifier = s.recv(128).decode("UTF-8", 'strict')
    pc_id = int.from_bytes(s.recv(4), 'big')
    rec_bulk_send(s, folder_path)
else:
    os.makedirs(folder_path)
    pc_id = int.from_bytes(s.recv(4), 'big')
    if os.getcwd() != folder_path:
        os.chdir(folder_path)
    rec_bulk_recv(s)

s.close()
w = Watcher()
w.run()
