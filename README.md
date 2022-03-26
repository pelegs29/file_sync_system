# network_hw2 - made by Peleg Shlomo and Eliran Eiluz.
# Arguments for the client (BY THIS ORDER!) - server IP, server port, the path to the directory that the client wishes to be backed up on the server, time(in seconds) to be synchronized with the server, client ID(optional).
# Argument for the server - the port that the server should bind to.
# PLEASE INSTALL WATCHDOG ON THE CLIENT'S COMPUTER(S) BEFORE USE! 
This project is demonstrating a cross-platform server that acts like a cloud for saving files(like Google Drive), and a client that uses this server.
The server works by the following method:

If it's a new client:
  1. When a new client connects to the server, the server generating a random-128-chars string that uses as the client's ID. the ID will be sent to the client and saved
  by him. Furthermore, the ID will be printed on the server's console for later use.
  2. An empty folder with the ID of the client will be created on the server's working directory.
  3. All the files and directories inside the path that given as an srgument to the client will be copied to the directory that created by the server in step 2.

If it's an existing client who wishes to connect from a different machine:
  1. The client should include as the last argument it's client ID. The directory to be backed up by the server should be EMPTY!
  2. The client will connect to the server, and the last will copy all the files and directories inside the directory which it's name is the client ID 
  to the folder given as an agrument by the client.
  
From now on, the client will connect to the server in case of the two following reasons:
  1. The time to be synchronized with the server(given as an argument to the client) has passed.
  because of the ability to connect to the server from different machines on the same client ID,
  when connecting to the server to synchronize, any changes that has been made on any machine that uses the same client ID will be updated.
  For example, 2 machines uses the same client ID and 1 file has been deleted from the first machine, when the second client will connect to the server
  to synchronize, this file will be deleted from it's machine.
  2. The client made a change in one of the files inside the directory that given as an argument to the client.
  In this case, the client will immediately connect to the server to update him with the change.The directory is monitored by WatchDog.
  For example, the client created a file inside the monitored directory. In this case, WatchDog will immediately recognize it, and an automaticly connection to
  the server will be established, and the same file will be created in the client's directory on the server.
