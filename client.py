import socket
import sys
import random
import string
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
    if not str(time_to_connect).isnumeric():
        raise Exception("Given time to reach is not valid")


def generate_user_identifier():
    return ''.join(random.choice(string.digits + string.ascii_letters) for i in range(129))


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
time_to_reach = sys.argv[4]


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
        change = ""
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            change = "Created new file"
        elif event.event_type == 'modified':
            change = "file modified."
        elif event.event_type == 'moved':
            change = "file moved."
        elif event.event_type == 'deleted':
            change = "file deleted."
        print(change)


# in case the user did not entered user identifier, generate one with 128 chars with generate_user_identifier function.
if len(sys.argv) == 5:
    user_identifier = generate_user_identifier()
w = Watcher()
w.run()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 12345))
s.send(b'hello')
data = s.recv(100)
print("Server sent: ", data)
s.close()
