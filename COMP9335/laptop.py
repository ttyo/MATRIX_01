import sys
import time
import socket

HOST_ADDRESS = "192.168.1.x"
PORT = 55056
UPDATE_TIMEOUT = 15
BUFFER = 1024

socket_l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_l.settimeout(UPDATE_TIMEOUT)
socket_l.bind((HOST_ADDRESS, PORT))
while True:
    try:
        data, address = socket_l.recvfrom(BUFFER)
        data = data.split()
        node = int(data[1])
        time = int(data[2])
        f = open('workfile', 'w')
        f.write(node + " " + time)
    except:
        print("Error in handling packet")
        continue
        
