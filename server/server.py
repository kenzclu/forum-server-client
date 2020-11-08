# forum server (python3)
# z5259931

import socket as s
import sys
import threading
import time
from datetime import datetime

UPDATE_INTERVAL = 1

mapPortToUser = {}


def socketToIndex(socket: s.socket):
    global clients
    for i in range(len(clients)):
        clientSocket = clients[i][0]
        if clientSocket.getpeername()[1] == socket.getpeername()[1]:
            return i
    return -1

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
        [type, *content] = message.split(" ")
        content = " ".join(content)

        with t_lock:
            client = socketToIndex(clientSocket)
            clientPort = clientSocket.getpeername()[1]
            if client == -1:  # New client connection
                client = len(clients)
                clients.append([clientSocket, "AWAIT", ""])

            if type == "AUTH_USERNAME":
                sendMessageToClient(client, None, "Client connected")
                mapPortToUser[clientPort] = content
                if checkUsernameExists(content):
                    sendMessageToClient(client, f"{type} SUCCESS", None)
                else:
                    sendMessageToClient(client, f"{type} FAIL", None)
            elif type == 'AUTH_PASSWORD':
                if checkPassword(mapPortToUser[clientPort], content):
                    sendMessageToClient(client, f"{type} SUCCESS", f"{mapPortToUser[clientPort]} successfully login")
                else:  # delete user from list of active users
                    sendMessageToClient(client, f"{type} FAIL", "Incorrect password")
                    mapPortToUser.pop(mapPortToUser[clientPort], None)
            elif type == 'AUTH_NEW_PASSWORD':
                addLogin(mapPortToUser[clientPort], content)
                sendMessageToClient(client, f"{type} SUCCESS", f"{mapPortToUser[clientPort]} successfully login")
            elif type == 'CRT':
                if createFile(content, mapPortToUser[clientPort]):
                    sendMessageToClient(client, f"{type} SUCCESS", f"Thread {content} created")
                else:
                    sendMessageToClient(client, f"{type} FAIL", f"Thread {content} exists")
            elif type == 'XIT':
                del clients[client]
                print(f"{mapPortToUser[clientPort]} exited")
                mapPortToUser.pop(mapPortToUser[clientPort], None)
                clientSocket.close()
                break
            else:
                clients[client][1] = "INVALID"
                clients[client][2] = f"Invalid command {type} received"

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
                clientSocket.send(f"{clientMessage}\n{displayMessage}".encode())
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
