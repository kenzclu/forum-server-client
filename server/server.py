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


def socket_handler(clientSocket: s.socket):
    while True:
        message = clientSocket.recv(2048).decode()
        [type, *content] = message.split(" ")

        with t_lock:
            client = socketToIndex(clientSocket)
            clientPort = clientSocket.getpeername()[1]
            if client == -1:  # New client connection
                client = len(clients)
                clients.append([clientSocket, "AWAIT", ""])

            content = " ".join(content)
            date_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

            if type == "AUTH_USERNAME":
                clients[client][2] = "Client connected"
                mapPortToUser[clientPort] = content
                if checkUsernameExists(content):
                    clients[client][1] = f"{type} SUCCESS"
                else:
                    clients[client][1] = f"{type} FAIL"
            elif type == 'AUTH_PASSWORD':
                if checkPassword(mapPortToUser[clientPort], content):
                    clients[client][1] = f"{type} SUCCESS"
                    clients[client][2] = f"{mapPortToUser[clientPort]} successfully login"
                else:  # delete user from list of active users
                    clients[client][1] = f"{type} FAIL"
                    clients[client][2] = "Incorrect password"
                    mapPortToUser.pop(mapPortToUser[clientPort], None)
            elif type == 'AUTH_NEW_PASSWORD':
                addLogin(mapPortToUser[clientPort], content)
                clients[client][1] = f"{type} SUCCESS"
                clients[client][2] = f"{mapPortToUser[clientPort]} successfully login"
            elif type == 'XIT':
                del clients[client]
                print(f"{mapPortToUser[clientPort]} exited")
                mapPortToUser.pop(mapPortToUser[clientPort], None)
                clientSocket.close()
                break
            else:
                clients[client][1] = "INVALID"
                clients[client][2] = f"Invalid command {type} received"

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
                clientSocket.send(clientMessage.encode())
                print(displayMessage)
                clients[i][1] = "AWAIT"
                clients[i][2] = ""

            t_lock.notify()

        time.sleep(UPDATE_INTERVAL)


if len(sys.argv) != 3:
    sys.stderr.write("USAGE: python3 server.py <PORT> <ADMIN_PASSWD>")
    exit(1)

PORT = int(sys.argv[1])
ADMIN_PASSWD = sys.argv[2]

# list of clients
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
