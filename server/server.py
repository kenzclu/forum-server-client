# forum server (python3)
# z5259931

import socket as s
import sys
import threading
import time
from datetime import datetime

UPDATE_INTERVAL = 1

def recv_handler():
    global t_lock
    global clients
    global serverSocket
    print(f"Server is now listening on PORT {PORT}")
    print("Waiting for clients to connect...")
    while True:
        # clientSocket: socket
        # clientAddress: [IP: string, PORT: string]
        clientSocket, clientAddress = serverSocket.accept()
        message = clientSocket.recv(2048).decode()
        
        with t_lock:
            date_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
            print(
                f'Received request from {clientAddress[0]} listening at {clientAddress[1]}: {message} at time {date_time}')
            clients.append(clientSocket)
            # Handle various messages the clients send


def send_handler():
    global t_lock
    global clients
    global serverSocket
    while True:
        with t_lock:
            for clientSocket in clients:
                date_time = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                message = 'Current time is ' + date_time
                clientSocket.send(message.encode())
                print(f"Sending time to {clientSocket.getpeername()[1]}")
        time.sleep(UPDATE_INTERVAL)


if len(sys.argv) != 3:
    sys.stderr.write("USAGE: python3 server.py <PORT> <ADMIN_PASSWD>")
    exit(1)

PORT = int(sys.argv[1])
ADMIN_PASSWD = sys.argv[2]

# list of clients
clients = []

t_lock = threading.RLock()

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
