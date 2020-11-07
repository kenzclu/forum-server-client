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

seq = 0
loggedIn = False

while not loggedIn:
    username = input("Enter username: ")
    password = input("Enter password: ")

    clientSocket.send(f"{seq} AUTH {username} {password}".encode())
    message, serverAddress = clientSocket.recvfrom(2048)

    if message.decode() == f"{seq + 1} SUCCESS":
        loggedIn = True
        seq += 1
    else:
        print("AUTH Failed")
 
clientSocket.sendto(f"{seq} XIT".encode(), (SERVER_IP, SERVER_PORT))
clientSocket.close()
