# forum client (python3)
# z5259931

import os
import select
import socket as s
import sys
import time

if len(sys.argv) != 3:
    sys.stderr.write("USAGE: python3 client.py <SERVER_IP> <SERVER_PORT>")
    exit(1)

SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])
clientSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
clientSocket.connect((SERVER_IP, SERVER_PORT))

loggedIn = False

CONNECTION_STATE = 'DISCONNECTED'
USERNAME = None

inputs = [clientSocket, sys.stdin]

while CONNECTION_STATE != 'LOGGED_IN':
    if CONNECTION_STATE == 'DISCONNECTED':
        print("Enter username: ", end='')
    elif CONNECTION_STATE == 'IN_PROGRESS':
        print("Enter password: ", end='')
    elif CONNECTION_STATE == 'CREATE_IN_PROGRESS':
        print(f"{USERNAME} does not exist\nEnter a new password: ", end='')

    sys.stdout.flush()

    readable, _, _ = select.select(inputs, [], [])

    for s in readable:
        if s == sys.stdin:
            command = sys.stdin.readline().rstrip()
            if CONNECTION_STATE == 'DISCONNECTED':
                USERNAME = command
                clientSocket.send(f"AUTH_USERNAME {command}".encode())
            elif CONNECTION_STATE == 'IN_PROGRESS':
                clientSocket.send(f"AUTH_PASSWORD {command}".encode())
            elif CONNECTION_STATE == 'CREATE_IN_PROGRESS':
                clientSocket.send(f"AUTH_NEW_PASSWORD {command}".encode())
            CONNECTION_STATE = 'SENDING'

        if s == clientSocket:
            message, serverAddress = clientSocket.recvfrom(2048)
            message = message.decode()
            if message == '':
                print("Socket has been closed")
                exit(0)
            [status, serverMessage] = message.split("\n")

            if status == 'EXIT':
                print("Disconnected from server")
                exit(0)
            elif status == 'AUTH_USERNAME SUCCESS':
                CONNECTION_STATE = 'IN_PROGRESS'
            elif status == 'AUTH_USERNAME FAIL':
                CONNECTION_STATE = 'CREATE_IN_PROGRESS'
            elif status == 'AUTH_PASSWORD SUCCESS' or status == 'AUTH_NEW_PASSWORD SUCCESS':
                print(f"Logged in as user {USERNAME}")
                print("Welcome to the forum")
                CONNECTION_STATE = 'LOGGED_IN'
            else:
                print(serverMessage)
                USERNAME = None
                CONNECTION_STATE = 'DISCONNECTED'

        sys.stdout.flush()

f = None

while True:
    if CONNECTION_STATE != 'SENDING':
        print("Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT, SHT: ", end='')
    sys.stdout.flush()
    readable, _, _ = select.select(inputs, [], [])

    for s in readable:
        if s == sys.stdin and not CONNECTION_STATE == 'SENDING':
            command = sys.stdin.readline().rstrip()
            type = command.split(" ")[0]
            clientSocket.send(command.encode())

            CONNECTION_STATE = 'SENDING'

            if type == 'UPD':
                # Sends the current working directory for UPD and DWN commands
                f = command.split(" ")[-1]
            elif type == 'DWN':
                f = command.split(" ")[-1]

        if s == clientSocket:
            message = clientSocket.recv(2048).decode()
            [status, *serverMessage] = message.split("\n")

            if status == 'UPD OK':
                file = open(f, 'rb')
                fileData = file.read(2048)
                while fileData:
                    clientSocket.send(fileData)
                    fileData = file.read(2048)
                file.close()
                time.sleep(0.1)
                clientSocket.send('UPD DONE'.encode())
            elif status == 'DWN OK':
                file = open(f, 'wb')
                fileData = clientSocket.recv(2048)
                while fileData:
                    if fileData == b'DWN DONE':
                        break
                    file.write(fileData)
                    fileData = clientSocket.recv(2048)
                file.close()
            else:
                print("\n".join(serverMessage).rstrip())
                if status == 'EXIT':
                    print("Disconnected from server")
                    exit(0)
                CONNECTION_STATE = 'RECEIVED'

clientSocket.close()
