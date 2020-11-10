# forum client (python3)
# z5259931

import socket as s
import sys

if len(sys.argv) != 3:
    sys.stderr.write("USAGE: python3 client.py <SERVER_IP> <SERVER_PORT>")
    exit(1)

SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])
ADMIN_PASSWD = "admin"
clientSocket = s.socket(s.AF_INET, s.SOCK_STREAM)
clientSocket.connect((SERVER_IP, SERVER_PORT))

loggedIn = False

while not loggedIn:
    username = input("Enter username: ")

    clientSocket.send(f"AUTH_USERNAME {username}".encode())
    message, serverAddress = clientSocket.recvfrom(2048)
    [status, serverMessage] = message.decode().split("\n")

    if status == "AUTH_USERNAME SUCCESS":
        password = input("Enter password: ")
        clientSocket.send(f"AUTH_PASSWORD {password}".encode())

        message, serverAddress = clientSocket.recvfrom(2048)
        [status, serverMessage] = message.decode().split("\n")

        if status == "AUTH_PASSWORD SUCCESS":
            print(f"Logged in as user {username}")
            print("Welcome to the forum")
            loggedIn = True
        else:
            print(serverMessage)
    else:
        password = input("Enter new password: ")
        clientSocket.send(f"AUTH_NEW_PASSWORD {password}".encode())

        message, serverAddress = clientSocket.recvfrom(2048)
        [status, serverMessage] = message.decode().split("\n")

        if status == "AUTH_NEW_PASSWORD SUCCESS":
            print(f"Logged in as user {username}")
            print("Welcome to the forum")
            loggedIn = True
        else:
            print(serverMessage)

while True:
    command = input("Enter one of the following commands: CRT, MSG, DLT, LST, XIT: ")
    if command == 'XIT':
        break
    clientSocket.send(command.encode())
    message = clientSocket.recv(2048).decode()
    [status, *serverMessage] = message.split("\n")

    print("\n".join(serverMessage).rstrip())
    
 
clientSocket.sendto(f"XIT".encode(), (SERVER_IP, SERVER_PORT))
clientSocket.close()
