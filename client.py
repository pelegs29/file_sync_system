import socket
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

# input check - raise exception if the program args count isn't 4 or 5
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


def new_client(sock):
    for path, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(path, file)
            file_name = os.path.relpath(file_path, path)
            file_size = str(os.path.getsize(file_path))
            protocol = "file," + file_name + "," + file_size
            protocol_size = len(protocol).to_bytes(4, 'big')
            sock.send(protocol_size)
            sock.send(protocol.encode())
            f = open(file_path, "r")
            sock.send(f.read().encode())
        for folder in dirs:
            # path = os.path.join(path, folder)
            # folder_name = os.path.relpath(folder_path, folder_path)
            folder_size = str(0)
            protocol = "folder," + folder + "," + folder_size
            protocol_size = len(protocol).to_bytes(4, 'big')
            sock.send(protocol_size)
            sock.send(protocol.encode())
    sock.send(len("0,0,0").to_bytes(4, 'big'))
    sock.send("0,0,0".encode())


def old_client(sock):
    os.chdir(folder_path)
    # TODO test large files.
    while True:
        data_size = int.from_bytes(sock.recv(4), 'big')
        data = sock.recv(data_size).decode("UTF-8", 'strict')
        file_type, file_name, file_size = data.split(',')
        if file_type == "file":
            f = open(file_name, "wb")
            data = sock.recv(int(file_size))
            f.write(data)
            f.close()
        elif file_type == "folder":
            os.makedirs(file_name, exist_ok=True)
            os.chdir(os.path.join(os.getcwd(), file_name))
        else:
            break


# running input checks
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
folder_path = sys.argv[3]
time_to_reach = float(sys.argv[4])

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
                time.sleep(5)
        except Exception:
            self.observer.stop()
            print("error")
        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        s.connect((ip, port))
        s.send((user_identifier + ",event").encode())
        if event.is_directory:
            if event.event_type == 'created':
                rel_path = os.path.relpath(event.src_path, folder_path)
                s.send(("folder,create," + rel_path).encode())
            elif event.event_type == 'modified':
                return None
            elif event.event_type == 'moved':
                change = "folder moved." + event.src_path
            elif event.event_type == 'deleted':
                change = "folder deleted." + event.src_path
        elif event.event_type == 'created':
            change = "Created new file"
        elif event.event_type == 'modified':
            change = "file modified."
        elif event.event_type == 'moved':
            change = "file moved."
        elif event.event_type == 'deleted':
            change = "file deleted."


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
s.send((user_identifier + ",NEW").encode())


# In case we are new client.
# TODO deal with folder names of ","
if user_identifier == "NEW":
    user_identifier = s.recv(128).decode("UTF-8", 'strict')
    new_client(s)
else:
    old_client(s)
s.close()
w = Watcher()
w.run()

# while True:
#     time.sleep(time_to_reach)
#     for root, dirs, files in os.walk(user_identifier, topdown=False):
#         for name in files:
#             os.remove(os.path.join(root, name))
#         for name in dirs:
#             os.rmdir(os.path.join(root, name))
#     s.connect((ip, port))
#     s.send((user_identifier + ",get_update").encode())
#     old_client(s)
#     s.close()

# s.close()
