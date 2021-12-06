import socket
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils import *


# input check - raise exception if the program args count isn't 4 or 5
def args_num_check():
    if len(sys.argv) != 5 and len(sys.argv) != 6:
        raise Exception("Only 4 or 5 arguments allowed.")


def compare_event(event, event_str):
    event_type, file_type, path = event_str.split(',')
    rel_src_path = os.path.relpath(event.src_path, folder_path)
    if event_type != event.event_type:
        return False
    if file_type == "folder" and not event.is_directory:
        return False
    if event_type == "moved":
        rel_dest_path = os.path.relpath(event.dest_path, folder_path)
        src, dest = path.split('>')
        if src != rel_src_path or dest != rel_dest_path:
            return False
    else:
        if path != rel_src_path:
            return False
    return True


def event_exist(event):
    for e in ignored_events:
        if compare_event(event, e):
            return True
    return False


# input check - raise exception if one of the condition is met :
# -> there are less or more than 4 dots in the ip address.
# -> there is a section in the ip that not contains only numbers.
# -> there are less than 1 or more than 4 numbers in each section of the op
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
    ignored_events.clear()
    while True:
        size = int.from_bytes(sock.recv(4), 'big')
        data = sock.recv(size).decode("UTF-8", 'strict')
        if data == "0,0,0":
            break
        ignored_events.append(data)
        event_type, file_type, path = data.split(',')
        if event_type == "created" and file_type == "file":
            modified_data = data.replace("created", "modified")
            ignored_events.append(modified_data)
        path = win_to_lin(path)
        if event_type == "created":
            created_event(sock, file_type, folder_path, path)
        elif event_type == "deleted":
            deleted_event(file_type, folder_path, path)
        elif event_type == "modified":
            modified_event(sock, folder_path, path)
        else:
            moved_event(file_type, folder_path, path)


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
ignored_events = []
SYS_TEMP_FILE = ".goutputstream"

# in case the user did not enter user identifier, generate one with 128 chars with generate_user_identifier function.
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
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, port))
                protocol_sender(sock, user_identifier + "," + str(pc_id) + ",1")
                check = sock.recv(1).decode("UTF-8", 'strict')
                if check == "1":
                    update(sock)
                sock.close()
        except Exception as e:
            self.observer.stop()
            print(e)
        self.observer.join()


def handle_event(event_type, file_type, sock, event):
    if SYS_TEMP_FILE in event.src_path:
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


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if (event.is_directory and event.event_type == "modified") or event.event_type == "closed":
            return None
        if SYS_TEMP_FILE in event.src_path:
            if event.event_type == "created" or event.event_type == "modified":
                return None
            else:
                event.event_type = "modified"
        if not event_exist(event):
            event_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            event_sock.connect((ip, port))
            protocol_sender(event_sock, user_identifier + "," + str(pc_id) + ",2")
            if event.is_directory:
                file_type = "folder"
            else:
                file_type = "file"
            handle_event(event.event_type, file_type, event_sock, event)
            event_sock.close()


if os.path.exists(folder_path) and user_identifier != "NEW":
    raise Exception("Folder already exists")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
start_protocol = user_identifier + "," + "999" + ",0"
protocol_sender(s, start_protocol)

# client initial code before changes monitoring,
# if no user_ID given as args ->  inform the server and get a new ID, then upload all the folder to the server
# else -> this is an existing user, create the folder and download all the files from the server.
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
