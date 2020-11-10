# forum server (python3)
# z5259931

import os
import socket as s
import sys
import threading
import time
from datetime import datetime

UPDATE_INTERVAL = 1

mapPortToUser = {}


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
    mapPortToUser.pop(username, None)


# Sets the client as waiting
def putClientOnWait(client):
    sendMessageToClient(client, "AWAIT", "")


# Sends an error message to client if provided arguments are invalid
def checkMessageValid(numArgs: int, content: str, client: int, username: str, error: str, exact=True):
    content = content.rstrip()
    if exact:
        if len(content) == 0 or len(content.split(" ")) != numArgs:
            sendMessageToClient(client, "INVALID", error)
            return False
    else:
        if len(content.split(" ")) < numArgs:
            sendMessageToClient(client, "INVALID", error)
            return False
    return True


# Sends clientMessage to the client, and prints the display message
def sendMessageToClient(client: int, clientMessage: str, displayMessage: str):
    global clients
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
    if not os.path.isfile(name):
        return False

    # source: https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a-large-file-cheaply-in-python
    num_lines = sum(1 for line in open(name, "r"))
    f = open(name, "a")
    f.write(f"{num_lines} {username}: {content}\n")
    f.close()
    return True


# deletes the specified message number if valid
def deleteFileLine(name: str, username: str, messageNumber: int):
    if not os.path.isfile(name):
        return f"Thread {name} does not exist"

    # source: https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a-large-file-cheaply-in-python
    num_lines = sum(1 for line in open(name, "r"))
    if messageNumber >= num_lines or messageNumber < 1:
        return f"Message number {messageNumber} is invalid"

    with open(name) as f:
        content = f.readlines()
        f.close()

    user = content[messageNumber].split(" ")[1]
    if user[:-1] != username: # Checks if user is the user that posted
        return "Permission denied"
    f = open(name, "w")
    del content[messageNumber]
    for i in range(1, len(content)):
        [_, *rest] = content[i].split(" ")
        content[i] = f"{i} {' '.join(rest)}" # Updates the line numbers
    f.write(''.join(content))
    f.close()
    return "SUCCESS"


def socket_handler(clientSocket: s.socket):
    while True:
        message = clientSocket.recv(2048).decode()
        type = message.split(" ")[0]

        with t_lock:
            client = socketToIndex(clientSocket)
            clientPort = clientSocket.getpeername()[1]
            username = ''

            if client == -1:  # New client connection
                client = len(clients)
                clients.append([clientSocket, "AWAIT", ""])
            elif clientPort in mapPortToUser:
                username = mapPortToUser[clientPort]

            if type == "AUTH_USERNAME":
                sendMessageToClient(client, None, "Client connected")
                content = getContent(message)
                if not checkMessageValid(1, content, client, username, "Username must be at least one character with no whitespace"):
                    continue
                mapPortToUser[clientPort] = content
                if checkUsernameExists(content):
                    sendMessageToClient(client, f"{type} SUCCESS", None)
                else:
                    sendMessageToClient(client, f"{type} FAIL", None)
            elif type == 'AUTH_PASSWORD':
                content = getContent(message)
                if not checkMessageValid(1, content, client, username, "Password must be at least one character with no whitespace"):
                    untrackUser(username)
                    continue
                if checkPassword(username, content):
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"{username} successfully login")
                else:  # delete user from list of active users
                    sendMessageToClient(
                        client, f"{type} FAIL", "Incorrect password")
                    untrackUser(username)
            elif type == 'AUTH_NEW_PASSWORD':
                content = getContent(message)
                if not checkMessageValid(1, content, client, username, "Password must be at least one character with no whitespace"):
                    untrackUser(username)
                    continue
                addLogin(username, content)
                sendMessageToClient(
                    client, f"{type} SUCCESS", f"{username} successfully login")
            elif type == 'CRT':
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(1, content, client, username, "Thread title must be at least one character with no whitespace"):
                    continue
                if createFile(content, username):
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"Thread {content} created")
                else:
                    sendMessageToClient(
                        client, f"{type} FAIL", f"Thread {content} exists")
            elif type == 'MSG':
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(2, content, client, username, "Must provide both a thread name and a message", False):
                    continue
                [thread, *message] = content.split(" ")
                if writeToFile(thread, username, " ".join(message).rstrip()):
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"Message posted to {thread} thread")
                else:
                    sendMessageToClient(
                        client, f"{type} FAIL", f"Thread {thread} does not exist")
            elif type == 'DLT':
                print(f"{username} issued {type} command")
                content = getContent(message)
                if not checkMessageValid(2, content, client, username, "Must provide both a thread name and a message number"):
                    continue
                [thread, messageNumber] = content.split(" ")
                result = deleteFileLine(thread, username, int(messageNumber))
                if result != "SUCCESS":
                    sendMessageToClient(client, f"{type} FAIL", result)
                else:
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"{messageNumber} deleted from {thread} thread")
            elif type == 'XIT':
                del clients[client]
                print(f"{username} exited")
                untrackUser(username)
                clientSocket.close()
                t_lock.notify()
                break
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
        socket_thread.daemon = False
        socket_thread.start()


def send_handler():
    global t_lock
    global clients
    global serverSocket
    while True:
        with t_lock:
            for i in range(len(clients)):
                [clientSocket, clientMessage, displayMessage] = clients[i]
                if clientMessage == "AWAIT":
                    continue
                clientSocket.send(
                    f"{clientMessage}\n{displayMessage}".encode())
                print(displayMessage)
                putClientOnWait(i)

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
    time.sleep(0.1)
