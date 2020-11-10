# forum server (python3)
# z5259931

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


def untrackUser(clientPort: str):
    mapPortToUser.pop(mapPortToUser[clientPort], None)


# Sends an error message to client if provided arguments are invalid
def checkMessageValid(numArgs: int, content: str, client: int, clientPort: str, error: str):
    if numArgs == 1:
        if len(content.split(" ")) != 1:
            sendMessageToClient(client, "INVALID",
                                "No whitespaces allowed")
            return False
        elif len(content) == 0:
            untrackUser(clientPort)
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


def checkPassword(username, password):
    credentials = open("credentials.txt", "r")
    for credential in credentials:
        if f"{username} {password}" == credential.rstrip():
            return True
    credentials.close()
    return False


def addLogin(username, password):
    credentials = open("credentials.txt", "a")
    credentials.write(f"\n{username} {password}")
    credentials.close()


def createFile(name, username):
    try:
        f = open(name, "x")
        f.write(f"{username}\n")
        return True
    except:
        return False


def socket_handler(clientSocket: s.socket):
    while True:
        message = clientSocket.recv(2048).decode()
        type = message.split(" ")[0]

        with t_lock:
            client = socketToIndex(clientSocket)
            clientPort = clientSocket.getpeername()[1]
            if client == -1:  # New client connection
                client = len(clients)
                clients.append([clientSocket, "AWAIT", ""])

            if type == "AUTH_USERNAME":
                sendMessageToClient(client, None, "Client connected")
                content = getContent(message)
                if not checkMessageValid(1, content, client, clientPort, "Username must be at least one character"):
                    continue
                mapPortToUser[clientPort] = content
                if checkUsernameExists(content):
                    sendMessageToClient(client, f"{type} SUCCESS", None)
                else:
                    sendMessageToClient(client, f"{type} FAIL", None)
            elif type == 'AUTH_PASSWORD':
                content = getContent(message)
                if not checkMessageValid(1, content, client, clientPort, "Password must be at least one character"):
                    continue
                if checkPassword(mapPortToUser[clientPort], content):
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"{mapPortToUser[clientPort]} successfully login")
                else:  # delete user from list of active users
                    sendMessageToClient(
                        client, f"{type} FAIL", "Incorrect password")
                    untrackUser(clientPort)
            elif type == 'AUTH_NEW_PASSWORD':
                content = getContent(message)
                if not checkMessageValid(1, content, client, clientPort, "Password must be at least one character"):
                    continue
                addLogin(mapPortToUser[clientPort], content)
                sendMessageToClient(
                    client, f"{type} SUCCESS", f"{mapPortToUser[clientPort]} successfully login")
            elif type == 'CRT':
                content = getContent(message)
                if not checkMessageValid(1, content, client, clientPort, "Thread title must be at least one character"):
                    continue
                if createFile(content, mapPortToUser[clientPort]):
                    sendMessageToClient(
                        client, f"{type} SUCCESS", f"Thread {content} created")
                else:
                    sendMessageToClient(
                        client, f"{type} FAIL", f"Thread {content} exists")
            elif type == 'XIT':
                del clients[client]
                print(f"{mapPortToUser[clientPort]} exited")
                untrackUser(clientPort)
                clientSocket.close()
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
                clients[i][1] = "AWAIT"
                clients[i][2] = ""

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
