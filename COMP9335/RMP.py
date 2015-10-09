#
# RIP-like Multi-hop Protocol (RMP)
# RMP is a light-weight dynamic routing protocol for sensor network, used in the research
# project: Time Synchronisation for Activity Monitoring from course COMP(49)335
# Each node in the protocol will finally has a topology of the whole network while
# in the convergence status. The metric in RMP is based on hop number, with server
# (called designated node) flooding mechanism, triggered update, and a periodical hello
# behaviour between neighbours acting as heart-beat detection for keep-alive
#
# Developed on: Python 2.7.10
# Author: Chengjia Xu, 5025306, CSE of UNSW
# Oct - Nov, 2015
#

import sys
import re
import time
import socket
import itertools
import ctypes
import curses
import curses.ascii
import threading
from string import printable

# From: http://stackoverflow.com/a/1695250/1800854
def enum(**enums):
    return type('Enum', (), enums)

STATUS = enum(NORMAL = 1, WARNING = 2, COMMAND = 3, RED = 4, GREEN = 5, ERROR = 6, YELLOW = 7, BLUE = 8, RESULT = 9)
PEER_STATUS = enum(OK = 1, INVALID = 2, DEAD = 3)
CONTROL = enum(NORMAL = 1, WARNING = 2, UPDATE = 3, HELLO = 4, ERROR = 5, RESULT = 6)
MESSAGE_TYPE = enum(UPDATE = 1, HELLO = 2, ACK = 3, DATA = 4, DATAACK = 5, SERVER = 6)
PRINTABLE = map(ord, printable)

# Initiate the program
def init():
    global PORT, UPDATE_INTERVAL, UPDATE_TIMEOUT, HELLO_INTERVAL, HELLO_TIMEOUT, SUCCESSIVE_LOST, HELLO_LOST
    global SUSPEND, INTERVAL
    global SEQ, CONVERGENCE, BUFFER

    PORT = 5678 # for sending / listening table updates
    UPDATE_INTERVAL = 5
    UPDATE_TIMEOUT = 15
    HELLO_INTERVAL = 5
    HELLO_TIMEOUT = 2
    SUCCESSIVE_LOST = 3
    SUSPEND = 2.0
    INTERVAL = 5.0
    SEQ = 65535
    CONVERGENCE = 0
    BUFFER = 1024
    HELLO_LOST = 4

    # The main function will runs in a new screen which can support customised commands
    curses.wrapper(main)


# Main function will allow user to run customised command, e.g.:
# show routingtable
# show neighbour
# show destination
# show neighbour status
def main(screen):
    global history, window_size, HOST, HOST_ADDRESS
    global DHList, ROUTETable, DESTList
    global TOTAL_NODES, SERVER, GATEWAY

    TOTAL_NODES = 0
    SERVER = 0
    GATEWAY = "10.11.11.100"
    DHList = [] # neighbour list
    ROUTETable = [] # routing table, contains routing list
    DESTList = [] # destination list
    history = []
    Y, X = screen.getmaxyx()
    window_size = Y - 3
    height = Y - 1

    screen.clear()
    curses.use_default_colors()
    curses.start_color()
    curses.init_pair(STATUS.NORMAL, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(STATUS.WARNING, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(STATUS.COMMAND, curses.COLOR_CYAN, -1)
    curses.init_pair(STATUS.RED, curses.COLOR_RED, -1)
    curses.init_pair(STATUS.GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(STATUS.BLUE, curses.COLOR_BLUE, -1)
    curses.init_pair(STATUS.ERROR, curses.COLOR_YELLOW, curses.COLOR_WHITE)
    curses.init_pair(STATUS.RESULT, curses.COLOR_GREEN, curses.COLOR_WHITE)
    curses.init_pair(STATUS.YELLOW, curses.COLOR_YELLOW, -1)
    print_screen(screen, CONTROL.NORMAL, "Please input data under the following scheme to initiate the protocol:")
    print_screen(screen, CONTROL.NORMAL, "1. Input the total number of nodes in the network. (e.g.: network 6)")
    print_screen(screen, CONTROL.NORMAL, "2. Input the local identifier, followed by Direct Hop (DH) identifiers. (e.g.: node 5 4 6)")
    print_screen(screen, CONTROL.NORMAL, "3. Designate server node (on the expecting server node itself, e.g.: server)")
    print_screen(screen, CONTROL.NORMAL, "4. Input \"done\" to skip designating server")

    network_configured = 0
    node_configured = 0
    display_type = 0
    done = 0
    while True:
        command = input(screen, height, display_type)

        if (network_configured and node_configured and done):
            display_type = 1
            break
        elif (command.startswith("node") or command.startswith("network") or command.startswith("server") or command.startswith("done")):
            if (command.startswith("network")): # record the total number of nodes
                try:
                    parameter = int(command.split()[1])
                    print_screen(screen, CONTROL.NORMAL, "Command: " + "C" + str(STATUS.COMMAND) + "[" + command + "]")
                    TOTAL_NODES = parameter
                    network_configured = 1
                except:
                    print_screen(screen, CONTROL.ERROR, "Invalid parameter(s): " + "C" + str(STATUS.YELLOW) + "[" + command + "]")
                    continue

            elif (command.startswith("node")): # record the information of DHs
                try:
                    parameter = command.split()
                    HOST = int(parameter[1])
                    HOST_ADDRESS = socket.gethostbyname(socket.gethostname())
                    for num in parameter[2:]:
                        DH = int(num)
                        DHList.append([DH, 0, 0]) # DHList: [A, B, C], A is DH identifier, B is received sequence number, C is successive lost number
                        ROUTETable.append([HOST, DH])
                        DESTList.append([DH, 1])
                    print_screen(screen, CONTROL.NORMAL, "Command: " + "C" + str(STATUS.COMMAND) + "[" + command + "]")
                    node_configured = 1
                except:
                    print_screen(screen, CONTROL.ERROR, "Invalid parameter(s): " + "C" + str(STATUS.YELLOW) + "[" + command + "]")
                    continue

            elif (command.startswith("server") and node_configured == 1): # local node is the server
                SERVER = int(HOST)
                done = 1

            elif (command.startswith("server") and node_configured == 0):
                print_screen (screen, CONTROL.ERROR, "Node must be configured firstly before being designated as a server.")

            elif (command.startswith("done")):
                done = 1
                print_screen(screen, CONTROL.NORMAL, "Command: " + "C" + str(STATUS.COMMAND) + "[" + command + "]")

        elif (command == ''):
            print_screen(screen, CONTROL.NORMAL, "")
        else:
            print_screen (screen, CONTROL.ERROR, "Command unknown: " + "C" + str(STATUS.YELLOW) + "[" + command + "]")

        roll_up_screen(screen)
        screen.refresh()
        # end of while

    print_screen(screen, CONTROL.NORMAL, "Protocol initialising ...")
    print_screen(screen, CONTROL.NORMAL, "Local identifier: " + "C" + str(STATUS.BLUE) + "[" + str(HOST) + "]")
    print_screen(screen, CONTROL.NORMAL, "Local address: " + "C" + str(STATUS.BLUE) + "[" + HOST_ADDRESS + "]")
    print_screen(screen, CONTROL.NORMAL, "Tips:")
    print_screen(screen, CONTROL.NORMAL, "[C" + str(STATUS.COMMAND) + "[show routingtable]] will display the current routing table.")
    print_screen(screen, CONTROL.NORMAL, "[C" + str(STATUS.COMMAND) + "[show neighbour]] will display the current neighbour list.")
    print_screen(screen, CONTROL.NORMAL, "[C" + str(STATUS.COMMAND) + "[show destination]] will display the current known destinations.")
    print_screen(screen, CONTROL.NORMAL, "[C" + str(STATUS.COMMAND) + "[show metric]] will display the metric of every destination")
    print_screen(screen, CONTROL.NORMAL, "[C" + str(STATUS.COMMAND) + "[show server]] will display the current server node")
    print_screen(screen, CONTROL.NORMAL, "[C" + str(STATUS.COMMAND) + "[quit]] will terminate the program.")



    # user can input command now
    while True:
        command = input(screen, height, display_type)

        # Quit command
        if (command == "quit"):
            if (tHandleSensorEvent.isAlive()):
                terminate(tHandleSensorEvent)
            if (tHandleUdpAll.isAlive()):
                terminate(tHandleUdpAll)

            print_screen(screen, CONTROL.NORMAL, "Local node is leaving network now.")
            screen.refresh()
            time.sleep(SUSPEND)
            break

        # functional commands
        # show routingtable
        # show neighbour
        # show destination
        # show neighbourstatus
        # show server
        elif (command.startswith("show")):
            try:
                parameter = command.split()[1]
                print_screen(screen, CONTROL.NORMAL, "Command: " + "C" + str(STATUS.COMMAND) + "[" + command + "]")
                if (parameter == "routingtable"):
                    print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[Current routing table:]")
                    for r_list in ROUTETable:
                        result = '# %s #' % ' - '.join(map(str, r_list))
                        print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[" + result + "]")

                elif (parameter == "neighbour"):
                    for DH in DHList:
                        result = "DH identifier: " + str(DH[0])
                        print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[" + result + "]")

                elif (parameter == "destination"):
                    print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[Known destination(s):]")
                    for Dest in DESTList:
                        result = "# " + str(Dest[0])
                        print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[" + result + "]")

                elif (parameter == "metric"):
                    print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[Destination  Metric]")
                    for Dest in DESTList:
                        result = '     ' + str(Dest[0]) + '          ' + str(Dest[1])
                        print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[" + result + "]")

                # elif (parameter is "neighbourstatus"):
                elif (parameter == "server"):
                    if (not SERVER):
                        print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[No designated node]")
                    elif (SERVER == HOST):
                        result = "Designated node is local node: " + str(SERVER)
                        print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[" + result + "]")
                    else:
                        result = "Designated node is: node " + str(SERVER)
                        print_screen(screen, CONTROL.RESULT, "C" + str(STATUS.GREEN) + "[" + result + "]")

                else:
                    print_screen (screen, CONTROL.ERROR, "Unknown \"show\" parameter(s): " + "C" + str(STATUS.YELLOW) + "[" + parameter + "]")

            except:
                print_screen (screen, CONTROL.ERROR, "Invalid parameter(s): " + "C" + str(STATUS.YELLOW) + "[" + command + "]")
                continue

        elif (command == ''):
            print_screen(screen, CONTROL.NORMAL, "")
        else:
            print_screen (screen, CONTROL.ERROR, "Command unknown: " + "C" + str(STATUS.YELLOW) + "[" + command + "]")

        roll_up_screen(screen)
        screen.refresh()
        # end of while
    # start threads now
    tHandleUdpAll = threading.Thread(target = handle_udp_all, args = (screen)) # a bug in here, _curses.urses has no window
    tHandleUdpAll.start()
    tHandleSensorEvent = threading.Thread(target = handle_sensor_event, args = (screen))
    tHandleSensorEvent.start()


def terminate(thread):
    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def input(screen, height, type):
    screen.move(height, 0)
    screen.clrtoeol()
    if (type == 0):
        screen.addstr("[Command Line Interface] >> ")
    elif (type == 1):
        screen.addstr(height, 0, "[Command Line Interface][node " + str(HOST) + "]$ ")

    ERASE = input.ERASE = getattr(input, "erasechar", ord(curses.erasechar()))
    Y, X = screen.getyx()
    s = []
    while True:
        c = screen.getch()

        if c in (curses.ascii.LF, curses.ascii.CR, curses.KEY_ENTER): # accept KEY_ENTER, LF or CR for compatibility
            break
        elif c == ERASE or c == curses.KEY_BACKSPACE: # both erase and KEY_BACKSPACE used for compatibility
            y, x = screen.getyx()
            if x > X:
                del s[-1]
                screen.move(y, (x - 1))
                screen.clrtoeol()
                screen.refresh()
        elif c in PRINTABLE:
            s.append(chr(c))
            screen.addch(c)
        else:
            pass
    return "".join(s)


def print_screen(screen, control, message):
    global history
    height = len(history)
    Y, X = screen.getyx() # save current position
    print_single_line(screen, height, control, message)
    history.append([control, message])

    roll_up_screen(screen)
    screen.move(Y, X) # restore the position
    screen.refresh()


def print_single_line(screen, height, control, message):
    if (control == CONTROL.WARNING): # display the status message with colors
        screen.addstr(height, 0, "[WARNING]", curses.color_pair(STATUS.WARNING))
    elif (control == CONTROL.UPDATE):
        screen.addstr(height, 0, "[UPDATE]", curses.color_pair(STATUS.NORMAL))
    elif (control == CONTROL.HELLO):
        screen.addstr(height, 0, "[HELLO]", curses.color_pair(STATUS.NORMAL))
    elif (control == CONTROL.NORMAL):
        screen.addstr(height, 0, "[NORMAL]", curses.color_pair(STATUS.NORMAL))
    elif (control == CONTROL.ERROR):
        screen.addstr(height, 0, "[ERROR]", curses.color_pair(STATUS.ERROR))
    elif (control == CONTROL.RESULT):
        screen.addstr(height, 0, "[RESULT]", curses.color_pair(STATUS.RESULT))

    # store the message into a list
    message = re.split("(C\d\[.*?\])", message)
    offset = 10
    for line in message:

        color_match = re.match("C(\d{1})\[(.*)\]", line)
        color_key = 0

        if color_match:
            color_key = int((color_match.groups()[0])) # get color key
            str = color_match.groups()[1] # get the original string
        else:
            str = line # if not match, which means it is a normal string without color

        Y, X = screen.getmaxyx()
        if offset + len(str) >= X: # has to wrap
            wrap_index = X - offset
            wrap_string = (str)[:wrap_index]
            if color_match:
                screen.addstr(height, offset, wrap_string, curses.color_pair(color_key))
            else:
                screen.addstr(height, offset, wrap_string)
            break

        if color_match: # print contents and colour
            screen.addstr(height, offset, str, curses.color_pair(color_key))
        else:
            screen.addstr(height, offset, str)

        offset += len(str)


# this function will roll up the screen if the screen has been fully occupied
def roll_up_screen(screen):
    global history
    global window_size

    if len(history) >= window_size: # if overflow, remove the first line
        history = history[1:]

    for index in range(0, window_size): # remove all lines
        screen.move(index, 0)
        screen.clrtoeol()
    for index, line in enumerate(history): # then display new lines
            if index >= window_size:
                break
            print_single_line(screen, index, line[0], line[1])


def address_generator(host):
    prefix = "10.11.11."
    host_address = prefix + str(host)
    return host_address


# this function will do sending/receving updates, processing packets
def handle_udp_all(screen):
    # Listening socket on port 5678 (UDP)
    socket_l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_l.settimeout(UPDATE_TIMEOUT)
    socket_l.bind(HOST_ADDRESS, PORT)
    sent_time = 0
    sent_time2 = 0
    sent_time3 = 0
    sequenceNum = 0

    while True:
        if (((time.time() - sent_time2) >= INTERVAL) and SERVER != 0): # send SERVER message, this is a fload message
            for DH in DHList:
                dh_address = address_generator(DH[0])
                send_server_info(dh_address)
            sent_time2 = time.time()

        if (((time.time() - sent_time) >= INTERVAL) and (not CONVERGENCE)): # Before convergence, send UPDATE
            for DH in DHList:
                dh_address = address_generator(DH[0])
                send_update(dh_address)
            sent_time = time.time()

        elif (((time.time() - sent_time3) >= INTERVAL) and CONVERGENCE): # After convergence, send HELLO
            for DH in DHList:
                dh_address = address_generator(DH[0])
                send_hello(dh_address, sequenceNum)
            sequenceNum = (sequenceNum + 1) % SEQ
            sent_time3 = time.time()

        # calculate the successive lost ACK from a DH, then check whether it is larger then the limitation of SUCCESSIVE_LOST
        for DH in DHList:
            DH[2] = 0
            if (sequenceNum < DH[1]):
                DH[2] = (SEQ - DH[1]) + sequenceNum
            else:
                DH[2] = sequenceNum - DH[1]

            # if a DH is lost, then delete every information from database, and CONVERGENCE status becomes false
            if (DH[2] >= SUCCESSIVE_LOST):
                print_screen(screen, CONTROL.WARNING, "DH node: " + "C" + str(STATUS.RED) + "[" + str(DH[0]) + "]" + " is lost")
                tBlinkRed = threading.Thread(target = blink_red)
                tBlinkRed.start()

                CONVERGENCE = 0
                lostDH = int(DH[0])
                DHList.remove(DH)
                for routing_list in ROUTETable:
                    for identifier in routing_list:
                        if (int(identifier) == lostDH) :
                            ROUTETable.remove(routing_list)
                            break

                for dest in DESTList:
                    if (int(dest) == lostDH):
                        DESTList.remove(dest)
                        break

        # receive the messages from DHs or remote nodes
        try:
            data, address = socket_l.recvfrom(BUFFER)
            data = data.split()
            msgType = int(data[0])
            sourceNode = int(data[1])

            if (msgType == MESSAGE_TYPE.DATA): # A triggered message sending to server node, response to hop via LED
                tBlinkGreen = threading.Thread(target = blink_green)
                tBlinkGreen.start()












            if (msgType == MESSAGE_TYPE.SERVER): # A server node is designated, fload to other nodes
                SERVER = int(data[2])
                for DH in DHList:
                    if (sourceNode != DH[0]):
                        dh_address = address_generator(DH[0])
                        send_server_info(dh_address)

            if (msgType == MESSAGE_TYPE.UPDATE): # Update message
                print_screen(screen, CONTROL.UPDATE, "An table update received from node: " + "C" + str(STATUS.GREEN) + "[" + str(sourceNode) + "]")
                received_table = []
                temp_list = []
                for identifier in data[1:]:
                    sourceNode = int(identifier)
                    if (data[data.index(identifier) + 1] == sourceNode):
                        temp_list.append(identifier)
                        received_table.append(temp_list)
                        temp_list = []
                    else:
                        temp_list.append(identifier)

                handle_route_update(received_table)

            if (msgType == MESSAGE_TYPE.HELLO):  # HELLO message, get sequence number from HELLO then send ACK with the sequence number back
                print_screen(screen, CONTROL.UPDATE,
                             "A hello message received from node: " + "C" + str(STATUS.BLUE) + "[" + str(sourceNode) + "]")
                seqNum = int(data[2])
                dh_address = address_generator(sourceNode)
                reply_ack(dh_address, seqNum)

            if (msgType == MESSAGE_TYPE.ACK):  # ACK from DH, record the received sequence number
                seqNum = int(data[2])
                for DH in DHList:
                    if (sourceNode == DH):
                        DH[1] = seqNum
                        break

            if (msgType == MESSAGE_TYPE.DATAACK):  # DataACK from remote node, in here the LED will blink to it
                print_screen(screen, CONTROL.UPDATE, "A triggered message received from node: " + "C" + str(STATUS.GREEN) + "[" + str(sourceNode) + "]")
                dh_address = address_generator(sourceNode)
                reply_data_ack(dh_address)
                tBlinkBlue = threading.Thread(target=blink_blue)
                tBlinkBlue.start()

        except socket.error:
            pass


# this function will do sending updates
def send_update(dh_address):
    chain = itertools.chain(*ROUTETable)  # flat the routing table then convert to a flat list
    message = list(chain)
    message = [str(x) for x in message]
    message = ' '.join(message)
    message = str(MESSAGE_TYPE.UPDATE) + ' ' + message

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))


def send_hello(dh_address, sequenceNum):
    message = str(MESSAGE_TYPE.HELLO)
    message = message + ' ' + str(HOST) + ' ' + str(sequenceNum)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(HELLO_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))


def reply_ack(dh_address, sequenceNum):
    message = str(MESSAGE_TYPE.ACK)
    message = message + ' ' + str(HOST) + ' ' + str(sequenceNum)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(HELLO_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))


def reply_data_ack(dh_address):
    message = str(MESSAGE_TYPE.DATAACK)
    message = message + ' ' + str(HOST)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))
    tBlinkBlue = threading.Thread(target=blink_blue)
    tBlinkBlue.start()


def send_server_info(dh_address):
    message = str(MESSAGE_TYPE.SERVER)
    message = message + ' ' + str(HOST) + ' ' + str(SERVER)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))


# this function will monitor sensor, generate triggered packet while sensors being triggered
def handle_sensor_event(screen):
    server_address = address_generator(SERVER)
    send_sensor_event(server_address)


# this function will generate triggered message to server, incuding timestamp
def send_sensor_event(server_address):
    sourceNode = HOST
    message = str(MESSAGE_TYPE.DATA)
    message = message + ' ' + str(HOST) + str(sourceNode)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (server_address, PORT))
    tBlinkGreen = threading.Thread(target=blink_green)
    tBlinkGreen.start()


# this function will update local table and destination based on the received table
def handle_route_update(received_table):
    destination_temp = []
    for update_list in received_table:
        destination_temp.append(update_list[-1])



    print("")































# this function will blink blue LED in order to react to ACK of triggered message
def blink_blue():
    print("")


# this function will blink red LED in order to react to DH lost & packet lost (no ACK)
def blink_red():
    print("")


# this function will blink green LED in order to react to triggered message, the number of LED is based on distance
def blink_green():
    print("")



if __name__ == "__main__":
    init()
