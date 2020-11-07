# forum server (python3)
# z5259931

from socket import *
import sys

if len(sys.argv) != 3:
    sys.stderr.write("USAGE: python3 server.py <PORT> <ADMIN_PASSWD>")
    exit(1)

PORT = int(sys.argv[1])
ADMIN_PASSWD = sys.argv[2]

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind('localhost', PORT)
serverSocket.listen(1)


