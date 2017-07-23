
import socket

HOST_ADDRESS = "192.168.1.106"  # this is address is of the laptop
PORT = 55056
UPDATE_TIMEOUT = 15
BUFFER = 1024

def enum(**enums):
    return type('Enum', (), enums)
MESSAGE_TYPE = enum(UPDATE = 1, HELLO = 2, ACK = 3, SERVERACK = 4, DATAACK = 5, SERVER = 6, DATA_IN = 7, DATA_OUT = 8)

socket_l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_l.settimeout(UPDATE_TIMEOUT)
socket_l.bind((HOST_ADDRESS, PORT))
f = open('sensor_monitor.txt', 'w')

while True:
    try:
        data, address = socket_l.recvfrom(BUFFER)
        data = data.split()
        msg_type = int(data[0])
        server = data[1]
        source = data[2]
        time_string = data[3]
        time_float = data[4]

        if (msg_type == MESSAGE_TYPE.DATA_IN):
            f.write("IN" + ' ' + server + ' ' + source + ' '  + time_string + ' ' + time_float)
        elif (msg_type == MESSAGE_TYPE.DATA_OUT):
            f.write("OUT" + ' ' + server + ' ' + source + ' '  + time_string + ' ' + time_float)
    except:
        print("Error in handling packet")
        continue

