# forum server (python3)
# z5259931

import os
import socket as s
import sys
import threading
import time
from datetime import datetime

UPDATE_INTERVAL = 1
SHUTDOWN = 'DISABLED'

mapPortToUser = {}
# Forum threads
threads = []
# Stores list of downloaded files (value) at the thread (key)
uploadedFiles = {}
# active socketHandlers
activeThreads = {}


# Returns the index of the respective socket
def socketToIndex(socket: s.socket):
    global clients
    for i in range(len(clients)):
        clientSocket = clients[i][0]
        if clientSocket.getpeername()[1] == socket.getpeername()[1]:
            return i
    return -1


# Gets the content of the message from client
def getContent(message):
    [_, *content] = message.split(" ")
    return " ".join(content)


# Removes the user from list of active users
def untrackUser(username: str):
    for k, v in mapPortToUser.items():
        if v == username:
            del mapPortToUser[k]
            break


# Sets the client as waiting
def putClientOnWait(client):
    sendMessageToClient(client, "AWAIT", "")


# Checks if user is logged in
def checkUserLoggedIn(user: str):
    for port in mapPortToUser:
        if mapPortToUser[port] == user:
            return True
    return False


# Sends an error message to client if provided arguments are invalid
def checkMessageValid(numArgs: int, content: str, client: int, error: str, exact=True):
    content = content.rstrip()
    if numArgs == 0 and len(content) == 0:
        return True
    if exact:
        if len(content) == 0 or len(content.split(" ")) != numArgs:
            sendMessageToClient(client, "INVALID", error)
            return False
    else:
        if len(content.split(" ")) < numArgs:
            sendMessageToClient(client, "INVALID", error)
            return False
    return True


# Check if file has been uploaded assuming thread has an uploaded file
def checkFileUploaded(thread: str, file: str):
    for message in uploadedFiles[thread]:
        uploadedFile = message.split(" ")[-1]
        if uploadedFile == file:
            return True
    return False


# Sends clientMessage to the client, and prints the display message
def sendMessageToClient(client: int, clientMessage: str, displayMessage: str):
    if clientMessage != None:
        clients[client][1] = clientMessage
    if displayMessage != None:
        clients[client][2] = displayMessage


def checkUsernameExists(username: str):
    credentials = open("credentials.txt", "r")
    for credential in credentials:
        existingUsername = credential.rstrip().split(" ")[0]
        if username == existingUsername:
            return True
    return False


def checkPassword(username: str, password: str):
    credentials = open("credentials.txt", "r")
    for credential in credentials:
        if f"{username} {password}" == credential.rstrip():
            return True
    credentials.close()
    return False


def addLogin(username: str, password: str):
    credentials = open("credentials.txt", "a")
    credentials.write(f"\n{username} {password}")
    credentials.close()


def createFile(name: str, username: str):
    try:
        f = open(name, "x")
        f.write(f"{username}\n")
        f.close()
        return True
    except:
        return False


def writeToFile(name: str, username: str, content: str):
    if not name in threads:
        return False

    # source: https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a-large-file-cheaply-in-python
    num_lines = sum(1 for line in open(name, "r"))
    f = open(name, "a")
    f.write(f"{num_lines} {username}: {content}\n")
    f.close()
    return True


# deletes the specified message number if valid
def deleteFileLine(name: str, username: str, messageNumber: int):
    if not name in threads:
        return f"Thread {name} does not exist"

    # source: https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a-large-file-cheaply-in-python
    num_lines = sum(1 for line in open(name, "r"))
    if messageNumber >= num_lines or messageNumber < 1:
        return f"Message number {messageNumber} is invalid"

    with open(name) as f:
        content = f.readlines()  # stores lines of file as a list
        f.close()

    user = content[messageNumber].split(" ")[1]
    if user[:-1] != username:  # Checks if user is the user that posted
        return "Permission denied"
    f = open(name, "w")
    del content[messageNumber]
    for i in range(1, len(content)):
        [_, *rest] = content[i].split(" ")
        content[i] = f"{i} {' '.join(rest)}"  # Updates the line numbers
    f.write(''.join(content))
    f.close()
    return "SUCCESS"


# Reads every line except for the first line of the thread
def readThread(name: str):
    if not name in threads:
        return "error"

    with open(name) as f:
        content = f.readlines()  # stores lines of file as a list
        f.close()

    if name in uploadedFiles:
        for file in uploadedFiles[name]:
            content.append(file + '\n')

    if len(content) == 1:
        return f"Thread {name} is empty"
    return "".join(content[1:])


# Lists active threads
def showThreads():
    if len(threads) == 0:
        return "No active threads exist"
    message = "The list of active threads:\n"
    for thread in threads:
        message += f"{thread}\n"
    return message


# Deletes the given thread
def deleteThread(thread: str, username: str):
    if not thread in threads:
        return f"Thread {thread} does not exist"
    f = open(thread, "r")
    owner = f.readline().rstrip()
    f.close()
    if owner != username:
        return f"Permission denied"
    os.remove(thread)
    threads.remove(thread)
    if thread in uploadedFiles:
        for files in uploadedFiles[thread]:
            file = files.split(" ")[-1]
            os.remove(f"{thread}-{file}")
        del uploadedFiles[thread]
    return "SUCCESS"


# Uploads file to thread
def uploadFile(thread: str, file: str, path: str):
    if not thread in threads:
        return f"Thread {thread} does not exist"
    if not os.path.isfile(f"{path}/{file}"):
        return f"File {file} does not exist"
    # Source: https://stackoverflow.com/questions/36875258/copying-one-files-contents-to-another-in-python
    # Copies content of one file to another
    with open(f"{thread}-{file}", 'wb+') as output, open(f"{path}/{file}", 'rb') as input:
        while True:
            data = input.read(100000)
            if data == b'':  # end of file reached
                break
            output.write(data)
        output.close()
        input.close()
    return "SUCCESS"


# Download file from thread
def downloadFile(thread: str, file: str, path: str):
    if not thread in threads:
        return f"Thread {thread} does not exist"
    elif not thread in uploadedFiles or not checkFileUploaded(thread, file):
        return f"{file} does not exist in Thread {thread}"
    with open(f"{path}/{file}", 'wb+') as output, open(f"{thread}-{file}", 'rb') as input:
        while True:
            data = input.read(100000)
            if data == b'':  # end of file reached
                break
            output.write(data)
        output.close()
        input.close()
    return "SUCCESS"


def shutdown():
    global SHUTDOWN
    for i in range(len(clients)):
        sendMessageToClient(i, "EXIT", "Shutting down server\n")
    for thread in threads:  # remove all threads
        os.remove(thread)
    for _, v in uploadedFiles.items():  # remove all uploaded files
        for files in v:
            file = files.split(" ")[-1]
            os.remove(f"{thread}-{file}")
    SHUTDOWN = 'IN_PROGRESS'


def socket_handler(clientSocket: s.socket):
    while True:
        message = clientSocket.recv(2048).decode()
        type = message.split(" ")[0]

        if message == '':
            break

        with t_lock:
            client = socketToIndex(clientSocket)
            clientPort = f"{clientSocket.getpeername()[0]}:{clientSocket.getpeername()[1]}"
            username = ''
            if client == -1:  # New client connection
                client = len(clients)
                clients.append([clientSocket, "AWAIT", ""])
            elif clientPort in mapPortToUser:
                username = mapPortToUser[clientPort]

            if type == "AUTH_USERNAME":  # Clience inputs a username
                sendMessageToClient(client, None, "Client connected")
                content = getContent(message)
                if not checkMessageValid(1, content, client, "Username must be at least one character with no whitespace"):
                    continue
                elif checkUserLoggedIn(content):
                    sendMessageToClient(client, "INVALID",
                                        f"{content} is already logged in")
                    continue
                mapPortToUser[clientPort] = content
                if checkUsernameExists(content):
                    sendMessageToClient(client, f"{type} SUCCESS", None)
                else:
                    sendMessageToClient(client, f"{type} FAIL", None)
            elif type == 'AUTH_PASSWORD':  # Client inputs a password
                content = getContent(message)
                if not checkMessageValid(1, content, client, "Password must be at least one character with no whitespace"):
                    untrackUser(username)
                    continue
                if checkPassword(username, content):
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"{username} successfully login")
                else:  # delete user from list of active users
                    sendMessageToClient(
                        client, f"{type} FAIL", "Incorrect password")
                    untrackUser(username)
            elif type == 'AUTH_NEW_PASSWORD':  # Client creates a new user with a new password
                content = getContent(message)
                if not checkMessageValid(1, content, client, "Password must be at least one character with no whitespace"):
                    untrackUser(username)
                    continue
                addLogin(username, content)
                sendMessageToClient(
                    client, f"{type} SUCCESS", f"{username} successfully login")
            elif type == 'CRT':  # Client creates a thread
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(1, content, client, "Thread title must be at least one character with no whitespace"):
                    continue
                if createFile(content, username):
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"Thread {content} created")
                    threads.append(content)
                else:
                    sendMessageToClient(
                        client, f"{type} FAIL", f"Thread {content} exists")
            elif type == 'MSG':  # Client sends a message to a thread
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(2, content, client, "Must provide both a thread name and a message", False):
                    continue
                [thread, *message] = content.split(" ")
                if writeToFile(thread, username, " ".join(message).rstrip()):
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"Message posted to {thread} thread")
                else:
                    sendMessageToClient(
                        client, f"{type} FAIL", f"Thread {thread} does not exist")
            elif type == 'DLT':  # Client deletes a message from a thread
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(2, content, client, "Must provide both a thread name and a message number"):
                    continue
                [thread, messageNumber] = content.split(" ")
                result = deleteFileLine(thread, username, int(messageNumber))
                if result != "SUCCESS":
                    sendMessageToClient(client, f"{type} FAIL", result)
                else:
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"{messageNumber} deleted from {thread} thread")
            elif type == 'LST':  # Client lists all active threads
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(0, content, client, "No argument should be given"):
                    continue
                sendMessageToClient(client, f"{type} SUCCESS", showThreads())
            elif type == 'RDT':  # Client reads content of thread
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(1, content, client, "Must provide only a thread name"):
                    continue
                result = readThread(content)
                if result == "error":
                    sendMessageToClient(
                        client, f"{type} FAIL", f"Thread {content} does not exist")
                else:
                    sendMessageToClient(client, f"{type} SUCCESS", result)
            elif type == 'UPD':  # Upload a file
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(3, content, client, "Must provide a thread and filename"):
                    continue
                [thread, file, path] = content.split(" ")
                result = uploadFile(thread, file, path)
                if result == "SUCCESS":
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"{username} successfully uploaded {file} to {thread} thread")
                    uploadedFileMessage = f"{username} uploaded {file}"
                    if not thread in uploadedFiles:
                        uploadedFiles[thread] = [uploadedFileMessage]
                    else:
                        uploadedFiles[thread].append(uploadedFileMessage)
                else:
                    sendMessageToClient(client, f"{type} FAIL", result)
            elif type == 'DWN':
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(3, content, client, "Must provide a thread and filename"):
                    continue
                [thread, file, path] = content.split(" ")
                result = downloadFile(thread, file, path)
                if result == "SUCCESS":
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"{file} successfully downloaded")
                else:
                    sendMessageToClient(client, f"{type} FAIL", result)
            elif type == 'RMV':  # Remove thread
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(1, content, client, "Must provide a thread"):
                    continue
                [thread] = content.split(" ")
                result = deleteThread(thread, username)
                if result == "SUCCESS":
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"{username} deleted {thread} thread")
                else:
                    sendMessageToClient(client, f"{type} SUCCESS", result)
            elif type == 'XIT': # Client leaves
                print(f"{username} issued {type} command")
                sendMessageToClient(client, "EXIT", f"Goodbye {username}")
                untrackUser(username)
                t_lock.notify()
                break
            elif type == 'SHT': # Server is shutdown
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(1, content, client, "Must provide the admin password"):
                    continue
                if content != ADMIN_PASSWD:
                    sendMessageToClient(
                        client, f"{type} FAIL", "Incorrect admin password")
                else:
                    shutdown()
            else:
                sendMessageToClient(client, "INVALID",
                                    f"Invalid command {type} received")

            # notify other threads
            t_lock.notify()


def recv_handler():
    global t_lock
    global clients
    global serverSocket
    print(f"Server is now listening on PORT {PORT}")
    print("Waiting for clients to connect...")
    while True:
        clientSocket, clientAddress = serverSocket.accept()

        # Creates a new thread to handle each client
        socket_thread = threading.Thread(
            name=str(clientAddress), target=socket_handler, args=[clientSocket])
        socket_thread.daemon = True
        socket_thread.start()
        activeThreads[str(clientAddress)] = socket_thread


def send_handler():
    global t_lock
    global clients
    global serverSocket
    global SHUTDOWN
    while True:
        with t_lock:
            for i in reversed(range(len(clients))):  # iterate backwards
                [clientSocket, clientMessage, displayMessage] = clients[i]
                if clientMessage == "AWAIT":
                    continue
                clientSocket.send(
                    f"{clientMessage}\n{displayMessage}".encode())
                if SHUTDOWN == 'DISABLED':
                    print(displayMessage.rstrip())
                if clientMessage == "EXIT":
                    clientSocket.shutdown(s.SHUT_RDWR)
                    del clients[i]
                else:
                    putClientOnWait(i)
            if SHUTDOWN == 'IN_PROGRESS':
                SHUTDOWN = 'READY'
                break
            # notify other threads
            t_lock.notify()

        time.sleep(UPDATE_INTERVAL)


if len(sys.argv) != 3:
    sys.stderr.write("USAGE: python3 server.py <PORT> <ADMIN_PASSWD>")
    exit(1)

PORT = int(sys.argv[1])
ADMIN_PASSWD = sys.argv[2]

# list of clients containing a list of sockets, messages to send, messages to display
clients = []

t_lock = threading.Condition()

serverSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
serverSocket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
serverSocket.bind(('localhost', PORT))
serverSocket.listen(1)

recv_thread = threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon = True
recv_thread.start()

send_thread = threading.Thread(name="SendHandler", target=send_handler)
send_thread.daemon = True
send_thread.start()

while True:
    if SHUTDOWN == 'READY':
        print("Shutting down server")
        break
    time.sleep(0.1)
