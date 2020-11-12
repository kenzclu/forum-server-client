# forum client (python3)
# z5259931

import os
import select
import socket as s
import sys

if len(sys.argv) != 3:
    sys.stderr.write("USAGE: python3 client.py <SERVER_IP> <SERVER_PORT>")
    exit(1)


# Checks if socket is closed
def isSocketClosed(message: str):
    if message == '':
        print("Connection closed")
        exit(0)


SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])
clientSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
clientSocket.connect((SERVER_IP, SERVER_PORT))

loggedIn = False

while not loggedIn:
    username = input("Enter username: ")

    clientSocket.send(f"AUTH_USERNAME {username}".encode())
    message, serverAddress = clientSocket.recvfrom(2048)
    isSocketClosed(message.decode())
    [status, serverMessage] = message.decode().split("\n")

    if status == "AUTH_USERNAME SUCCESS":
        password = input("Enter password: ")
        clientSocket.send(f"AUTH_PASSWORD {password}".encode())

        message, serverAddress = clientSocket.recvfrom(2048)
        isSocketClosed(message.decode())
        [status, serverMessage] = message.decode().split("\n")

        if status == "AUTH_PASSWORD SUCCESS":
            print(f"Logged in as user {username}")
            print("Welcome to the forum")
            loggedIn = True
        else:
            print(serverMessage)
    elif status == "AUTH_USERNAME FAIL":
        password = input("Enter new password: ")
        clientSocket.send(f"AUTH_NEW_PASSWORD {password}".encode())

        message, serverAddress = clientSocket.recvfrom(2048)
        isSocketClosed(message.decode())
        [status, serverMessage] = message.decode().split("\n")

        if status == "AUTH_NEW_PASSWORD SUCCESS":
            print(f"Logged in as user {username}")
            print("Welcome to the forum")
            loggedIn = True
        else:
            print(serverMessage)
    else:
        print(serverMessage)

while True:
    command = input(
        "Enter one of the following commands: CRT, MSG, DLT, LST, RDT, UPD, DWN, RMV, XIT, SHT: ")
    type = command.split(" ")[0]
    if type == 'UPD' or type == 'DWN':
        # Sends the current working directory for UPD and DWN commands
        command = f"{command.rstrip()} {os.getcwd()}"
    clientSocket.send(command.encode())
    message = clientSocket.recv(2048).decode()
    isSocketClosed(message)
    [status, *serverMessage] = message.split("\n")

    print("\n".join(serverMessage).rstrip())
    if (status == 'EXIT'):
        break

clientSocket.close()
