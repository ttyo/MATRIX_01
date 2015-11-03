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

import re
import time
import socket
import itertools
import ctypes
import curses
import curses.ascii
import threading
import RPi.GPIO as GPIO     #import Pi general-purpose input/output (GPIO) library
from string import printable
import datetime

# From: http://stackoverflow.com/a/1695250/1800854
def enum(**enums):
    return type('Enum', (), enums)

STATUS = enum(NORMAL = 1, WARNING = 2, COMMAND = 3, RED = 4, GREEN = 5, ERROR = 6, YELLOW = 7, BLUE = 8, RESULT = 9)
PEER_STATUS = enum(OK = 1, INVALID = 2, DEAD = 3)
CONTROL = enum(NORMAL = 1, WARNING = 2, UPDATE = 3, HELLO = 4, ERROR = 5, RESULT = 6)
MESSAGE_TYPE = enum(UPDATE = 1, HELLO = 2, ACK = 3, SERVERACK = 4, DATAACK = 5, SERVER = 6, DATA_IN = 7, DATA_OUT = 8)
PRINTABLE = map(ord, printable)

# Initiate the program
def init():
    global PORT, UPDATE_INTERVAL, UPDATE_TIMEOUT, HELLO_INTERVAL, HELLO_TIMEOUT, SUCCESSIVE_LOST, HELLO_LOST, DATA_LOST, SERVER_INTERVAL
    global SEQ, CONVERGENCE, BUFFER, SERVER_CONVERGENCE, EVENT_DETECTED
    global GREEN_PIN, BLUE_PIN, RED_PIN, BUTTON_PIN, PIR_PIN
    global LED_DELAY

    PORT = 55056  # for sending / listening table updates
    UPDATE_INTERVAL = 5.0
    UPDATE_TIMEOUT = 15.0
    HELLO_INTERVAL = 5.0
    HELLO_TIMEOUT = 2.0
    SERVER_INTERVAL = 5.0
    SUCCESSIVE_LOST = 3
    SEQ = 65535
    CONVERGENCE = 0
    SERVER_CONVERGENCE = 0
    BUFFER = 1024
    HELLO_LOST = 4
    GREEN_PIN = 25
    RED_PIN = 21
    BLUE_PIN = 23
    LED_DELAY = 0.5
    PIR_PIN = 16
    EVENT_DETECTED = 0

    set_up_pins()
    curses.wrapper(main)  # The main function will runs in a new screen which can support customised commands


def set_up_pins():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GREEN_PIN, GPIO.OUT)   # set up GPIO output channel
    GPIO.setup(RED_PIN, GPIO.OUT)   # set up GPIO output channel
    GPIO.setup(BLUE_PIN, GPIO.OUT)   # set up GPIO output channel
    GPIO.setup(PIR_PIN, GPIO.IN)  # setup GPIO 16 as INPUT

    GPIO.add_event_detect(PIR_PIN, GPIO.BOTH, callback = event_call_back, bouncetime = 300)


def main(screen):
    global history, window_size, HOST, HOST_ADDRESS
    global DHList, ROUTETable, DSTList
    global TOTAL_NODES, SERVER, SERVER_CONVERGENCE, LAPTOP_ADD

    TOTAL_NODES = 0
    SERVER = 0
    LAPTOP_ADD = "192.168.1.106"
    DHList = {}  # neighbour list
    ROUTETable = []  # routing table, contains routing list
    DSTList = {}  # destination list
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
    print_screen(screen, CONTROL.NORMAL, "Please configure local node under the following scheme to ")
    print_screen(screen, CONTROL.NORMAL, "initiate the protocol:")
    print_screen(screen, CONTROL.NORMAL, "1. Input the total number of nodes in the network: ")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[network (total_number)]]")
    print_screen(screen, CONTROL.NORMAL, "2. Input the local identifier (LI) and direct hops (DH): ")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[node (LI) (DH ...)]]")
    print_screen(screen, CONTROL.NORMAL, "3. Designate local node as server, this will flood server info")
    print_screen(screen, CONTROL.NORMAL, "to all the other nodes, or use command [#" + str(STATUS.COMMAND) + "[done]] to skip:")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[server]]")

    network_configured = 0
    node_configured = 0
    display_type = 0
    done = 0

    # initialise the protocol
    while True:
        command = stdin_to_command(screen, height, display_type)
        command_color = "#" + str(STATUS.COMMAND) + "[" + command + "]"
        command_error = "#" + str(STATUS.YELLOW) + "[" + command + "]"
        if (network_configured and node_configured and done):
            display_type = 1
            break
        elif (command.startswith("node") or command.startswith("network") or command.startswith("server")
              or command.startswith("done")):
            if (command.startswith("network")):  # record the total number of nodes
                try:
                    parameter = int(command.split()[1])
                    print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                    TOTAL_NODES = parameter
                    network_configured = 1
                except:
                    print_screen(screen, CONTROL.ERROR, "Invalid parameter(s) in command: " + command_error)
                    continue

            elif (command.startswith("node")):  # record the information of DHs
                try:
                    parameter = command.split()
                    HOST = int(parameter[1])
                    HOST_ADDRESS = address_generator(HOST)
                    #HOST_ADDRESS = socket.gethostbyname(socket.gethostname())
                    for num in parameter[2:]:
                        DH = int(num)
                        DHList[DH] = [0, 0]  # DHList: [A, B, C], A is DH identifier, B is received sequence number, C is successive lost number
                        ROUTETable.append([HOST, DH])
                        DSTList[DH] = 1  # DSTList: [A, B], A is DH identifier, B is distance to A
                    print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                    node_configured = 1
                except:
                    print_screen(screen, CONTROL.ERROR, "Invalid parameter(s) in command: " + command_error)
                    continue

            elif (command == "server" and node_configured == 1):  # local node is the server
                print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                SERVER = int(HOST)
                done = 1

            elif (command == "server" and node_configured == 0):
                print_screen (screen, CONTROL.ERROR, "Node must be configured firstly before being designated as a server.")

            elif (command == "done"):
                done = 1
                print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)

        elif (command == ''):
            print_screen(screen, CONTROL.NORMAL, "")
        else:
            print_screen (screen, CONTROL.ERROR, "Command unknown: " + command_error)

        roll_up_screen(screen)
        screen.refresh()
        # end of while

    print_screen(screen, CONTROL.NORMAL, "")
    print_screen(screen, CONTROL.NORMAL, "")
    print_screen(screen, CONTROL.NORMAL, "")
    print_screen(screen, CONTROL.NORMAL, "Protocol initialising ... (RMP alpha, version 0.9)")

    # start threads now
    tHandleUdpAll = threading.Thread(target = handle_communication, args = (screen, 1))  # a bug in here, _curses.urses has no window
    tHandleUdpAll.start()
    print_screen(screen, CONTROL.NORMAL, "Communication module starting ...")
    tHandleSensorEvent = threading.Thread(target = handle_sensor_event, args = (screen, 1))
    tHandleSensorEvent.start()
    print_screen(screen, CONTROL.NORMAL, "Sensor module starting ...")
    #tSetUpPins = threading.Thread(target = set_up_pins())
    #tSetUpPins.start()

    print_screen(screen, CONTROL.NORMAL, "Local identifier: " + "#" + str(STATUS.BLUE) + "[" + str(HOST) + "]")
    print_screen(screen, CONTROL.NORMAL, "Local ip address: " + "#" + str(STATUS.BLUE) + "[" + HOST_ADDRESS + "]")
    print_screen(screen, CONTROL.NORMAL, "")
    print_screen(screen, CONTROL.NORMAL, "Tips:")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show routingtable]] will display the current routing table.")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show neighbour]] will display the current neighbour list.")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show destination]] will display the current known destinations.")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show metric]] will display the metric of every destination.")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show server]] will display the current server node.")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show info]] will display system information like ip address.")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[server]] will designate a new server node.")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[quit]] will terminate the program.")
    print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[help]] will re-display tips above.")


    # user can input command now
    while True:
        command = stdin_to_command(screen, height, display_type)
        command_color = "#" + str(STATUS.COMMAND) + "[" + command + "]"
        command_error = "#" + str(STATUS.YELLOW) + "[" + command + "]"

        # Quit command
        if (command == "quit"):
            if (tHandleSensorEvent.isAlive()):
                terminate(tHandleSensorEvent)
            if (tHandleUdpAll.isAlive()):
                terminate(tHandleUdpAll)
            #if (tSetUpPins.isAlive()):
            #    terminate(tSetUpPins)

            print_screen(screen, CONTROL.NORMAL, "Local node is leaving network now.")
            screen.refresh()
            time.sleep(2.0)
            GPIO.cleanup()
            break

        # functional commands, for example:
        # show routingtable
        # show neighbour
        # show destination
        # show server
        elif (command.startswith("show")):
            try:
                parameter = command.split()[1]
                print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                if (parameter == "routingtable"):
                    if (len(ROUTETable) == 0):
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Routing table is empty]")
                    else:
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Current routing table:]")
                        for r_list in ROUTETable:
                            result = '# %s #' % ' - '.join(map(str, r_list))
                            print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                elif (parameter == "neighbour"):
                    if (len(DHList) == 0):
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Neighbour list is empty]")
                    else:
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[List of Direct Hop(s):]")
                        for DH_key in DHList:
                            result = "DH label: " + str(DH_key)
                            print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                elif (parameter == "destination"):
                    if (len(DSTList) == 0):
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Destination list is empty]")
                    else:
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Known destination(s):]")
                        for DST_key in DSTList:
                            result = "# " + str(DST_key)
                            print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                elif (parameter == "metric"):
                    if (len(DSTList) == 0):
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Destination list is empty]")
                    else:
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Destination  Metric]")
                        for DST_key in DSTList:
                            result = '     ' + str(DST_key) + '          ' + str(DSTList[DST_key])
                            print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                elif (parameter == "server"):
                    if (not SERVER):
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[No designated node]")
                    elif (SERVER == HOST):
                        result = "Designated node is local node: " + str(SERVER)
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")
                    else:
                        result = "Designated node is: node " + str(SERVER)
                        print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                elif (parameter == "info"):
                    print_screen(screen, CONTROL.NORMAL, "RMP alpha, version 0.9")
                    print_screen(screen, CONTROL.NORMAL, "Local identifier: " + "#" + str(STATUS.BLUE) + "[" + str(HOST) + "]")
                    print_screen(screen, CONTROL.NORMAL, "Local ip address: " + "#" + str(STATUS.BLUE) + "[" + HOST_ADDRESS + "]")

                else:
                    command_error = "#" + str(STATUS.YELLOW) + "[" + parameter + "]"
                    print_screen (screen, CONTROL.ERROR, "Unknown \"show\" parameter(s): " + command_error)

            except:
                print_screen (screen, CONTROL.ERROR, "Invalid parameter(s): " + command_error)
                continue

        elif (command == "server" and SERVER == HOST):
            print_screen (screen, CONTROL.ERROR, "Local node is already designated as server.")
        elif (command == "server"):
            print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
            SERVER_CONVERGENCE = 0;
            SERVER = int(HOST)

        elif (command == "help"):
            print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
            print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show routingtable]] will display the current routing table.")
            print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show neighbour]] will display the current neighbour list.")
            print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show destination]] will display the current known destinations.")
            print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show metric]] will display the metric of every destination.")
            print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show server]] will display the current server node.")
            print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show info]] will display system information like ip address.")
            print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[server]] will designate a new server node.")
            print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[quit]] will terminate the program.")

        elif (command == ''):
            print_screen(screen, CONTROL.NORMAL, "")

        else:
            print_screen (screen, CONTROL.ERROR, "Command unknown: " + command_error)

        roll_up_screen(screen)
        screen.refresh()
    # end of while
# end of main


# This function will read the STDIN, and make it at the bottom
def stdin_to_command(screen, height, type):
    screen.move(height, 0)
    screen.clrtoeol()
    if (type == 0):  # provides two interface: before and after the protocol initialisation
        screen.addstr("[Command Line Interface] >> ")
    elif (type == 1):
        screen.addstr(height, 0, "[Command Line Interface][node " + str(HOST) + "]# ")

    # From http://stackoverflow.com/a/30259422/1800854, James Mills, keep STDIN on a fixed position
    ERASE = stdin_to_command.ERASE = getattr(stdin_to_command, "erasechar", ord(curses.erasechar()))
    Y, X = screen.getyx()
    s = []
    while True:
        c = screen.getch()
        if c in (curses.ascii.LF, curses.ascii.CR, curses.KEY_ENTER):
            break
        elif c == ERASE or c == curses.KEY_BACKSPACE:
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
    Y, X = screen.getyx()  # save current position
    print_single_line(screen, height, control, message)
    history.append([control, message])

    roll_up_screen(screen)
    screen.move(Y, X)  # restore the position
    screen.refresh()


def print_single_line(screen, height, control, message):
    if (control == CONTROL.WARNING):  # display the status message with colors
        screen.addstr(height, 0, "[WARNING]", curses.color_pair(STATUS.WARNING))
    elif (control == CONTROL.UPDATE):
        screen.addstr(height, 0, "[UPDATE]", curses.color_pair(STATUS.NORMAL))
    elif (control == CONTROL.HELLO):
        screen.addstr(height, 0, "[HELLO] ", curses.color_pair(STATUS.NORMAL))
    elif (control == CONTROL.NORMAL):
        screen.addstr(height, 0, "[NORMAL]", curses.color_pair(STATUS.NORMAL))
    elif (control == CONTROL.ERROR):
        screen.addstr(height, 0, "[ERROR] ", curses.color_pair(STATUS.ERROR))
    elif (control == CONTROL.RESULT):
        screen.addstr(height, 0, "[RESULT]", curses.color_pair(STATUS.RESULT))

    message = re.split("(\#\d\[.*?\])", message)  # store the message into a list
    offset = 10
    for line in message:

        color_match = re.match("\#(\d{1})\[(.*)\]", line)
        color_key = 0

        if color_match:
            color_key = int((color_match.groups()[0]))  # get color key
            str = color_match.groups()[1]  # get the original string
        else:
            str = line  # if not match, which means it is a normal string without color

        Y, X = screen.getmaxyx()
        if offset + len(str) >= X:  # has to wrap
            wrap_index = X - offset
            wrap_string = (str)[:wrap_index]
            if color_match:
                screen.addstr(height, offset, wrap_string, curses.color_pair(color_key))
            else:
                screen.addstr(height, offset, wrap_string)
            break

        if color_match:  # print contents and colour
            screen.addstr(height, offset, str, curses.color_pair(color_key))
        else:
            screen.addstr(height, offset, str)

        offset += len(str)


# this function will roll up the screen if the screen has been fully occupied
def roll_up_screen(screen):
    global history
    global window_size

    if len(history) >= window_size:  # if overflow, remove the first line
        history = history[1:]

    for index in range(0, window_size):  # remove all lines
        screen.move(index, 0)
        screen.clrtoeol()
    for index, line in enumerate(history):  # then display new lines
            if index >= window_size:
                break
            print_single_line(screen, index, line[0], line[1])


def address_generator(host):
    #prefix = "10.11.11."
    prefix = "192.168.1."
    host_address = prefix + str(host)
    return host_address


# this function will do sending/receving updates, processing packets
def handle_communication(screen, start):
    global DHList, ROUTETable, DSTList, SERVER, CONVERGENCE, SERVER_CONVERGENCE

    # a listen socket, listening on port 5678 (UDP)
    socket_l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_l.settimeout(UPDATE_TIMEOUT)
    print_screen(screen, CONTROL.NORMAL, "Host: " + HOST_ADDRESS);
    socket_l.bind((HOST_ADDRESS, PORT))
    sent_time = 0
    sent_time2 = 0
    #sent_time3 = 0
    #sequenceNum = 0
    server_reply = []

    while True:
        if (((time.time() - sent_time2) >= SERVER_INTERVAL) and SERVER == HOST and (not SERVER_CONVERGENCE)):  # I am the server, fload the SERVER message
            for DH_key in DHList:
                dh_address = address_generator(DH_key)
                send_server_info(dh_address)
            sent_time2 = time.time()

        #if (((time.time() - sent_time3) >= HELLO_INTERVAL) and CONVERGENCE):  # After convergence, send HELLO
        #    for DH_key in DHList:
        #        dh_address = address_generator(DH_key)
        #        send_hello(dh_address, sequenceNum)
        #    sequenceNum = (sequenceNum + 1) % SEQ
        #    sent_time3 = time.time()

        if (((time.time() - sent_time) >= UPDATE_INTERVAL) and (not CONVERGENCE)):  # Before convergence, send UPDATE
            for DH_key in DHList:
                dh_address = address_generator(DH_key)
                send_update(dh_address)
            sent_time = time.time()
            if (len(DSTList) == (TOTAL_NODES - 1)):  # if the nodes number is the length of destination list, then in convergence
                CONVERGENCE = 1

        # calculate the successive lost ACK from a DH, then check whether it is larger then the limitation of SUCCESSIVE_LOST
        #for DH_key in DHList:
        #    DHList[DH_key][1] = 0
        #    if (sequenceNum < DH[1]):
        #        DHList[DH_key][1] = (SEQ - DHList[DH_key][0]) + sequenceNum
        #    else:
        #        DHList[DH_key][1] = sequenceNum - DHList[DH_key][0]
        #
        #    # if a DH is lost, then delete every information from database, and CONVERGENCE status becomes false
        #    if (DHList[DH_key][1] >= SUCCESSIVE_LOST):
        #        print_screen(screen, CONTROL.WARNING, "DH node: " + "#" + str(STATUS.RED) + "[" + str(DH_key) + "]" + " is lost")
        #        tBlinkRed = threading.Thread(target = blink_red)
        #        tBlinkRed.start()
        #
        #        CONVERGENCE = 0
        #        lostDH = int(DH_key)
        #        del DHList[DH_key]
        #        for routing_list in ROUTETable:
        #            for identifier in routing_list:
        #                if (int(identifier) == lostDH) :
        #                    ROUTETable.remove(routing_list)
        #                    break
        #
        #        for DST_key in DSTList:
        #            if (int(DST_key) == lostDH):
        #                del DSTList[DST_key]
        #                break

        # receive the messages from DHs or remote nodes
        try:
            data, address = socket_l.recvfrom(BUFFER)
            data = data.split()
            msg_type = int(data[0])
            direct_source_node = int(data[1])

            # A server message from SERVER -> any nodes (flood), reply it according to routing table
            # then flood the message to other DHs except the source node (split horizon)
            # message sent between DHs, step by step
            if (msg_type == MESSAGE_TYPE.SERVER):
                SERVER = int(data[2])  # record the server
                SERVER_CONVERGENCE = 1
                print_screen(screen, CONTROL.UPDATE, "Local node is now aware of Designated Node: " + "#" + str(STATUS.BLUE) + "[node " + str(SERVER) + "]")
                for route_list in ROUTETable:  # reply to server, search the routing table, SOURCE -> SERVER
                    if (route_list[-1] == SERVER):
                        path_node = int(route_list[1])
                        path_address = address_generator(path_node)
                        reply_server(path_address, HOST)
                        break
                for DH_key in DHList:  # then flood the server message to other DHs
                    if (direct_source_node != DH_key):  # split horizon
                        dh_address = address_generator(DH_key)
                        send_server_info(dh_address)

            # if receive a reply from SOURCE -> LOCAL -> SERVER
            # forward it to the server according to routing table
            # this will not change the source node information
            if (msg_type == MESSAGE_TYPE.SERVERACK):
                source_node = int(data[2])
                if (SERVER == HOST):  # if I am the server, record the source node
                    if (not (source_node in server_reply)):
                        server_reply.append(source_node)
                    if (len(server_reply) == TOTAL_NODES - 1):  # all nodes know server identifier
                        SERVER_CONVERGENCE = 1
                        print_screen(screen, CONTROL.UPDATE, "Designated Node info is fully synchronised among the network now")
                else:  # I am not the server, forward it to server according to routing table
                    for route_list in ROUTETable:
                        if (route_list[-1] == SERVER):
                            path_node = int(route_list[1])
                            path_address = address_generator(path_node)
                            reply_server(path_address, source_node)
                            break

            # update message, if in convergence then drop it
            # if not in convergence, handle the update
            # recover the update information into a two dimension list
            # then pass it to another function
            if (msg_type == MESSAGE_TYPE.UPDATE and (not CONVERGENCE)):
                del data[0]
                print_screen(screen, CONTROL.UPDATE, "A routing table update received from: " + "#" + str(STATUS.BLUE) + "[node " + str(direct_source_node) + "]")
                received_table = []
                temp_list = []
                while (len(data) > 0):
                    #direct_source_node = int(identifier)
                    identifier = data.pop(0)
                    temp_list.append(int(identifier))
                    #if (data.index(identifier) < len(data) - 1):
                    if (len(data) > 0):
                        #if (int(data[data.index(identifier) + 1]) == direct_source_node):  # received data is like: 6 4 6 1 4 6 5 6 1 2 3
                        if (int(data[0]) == direct_source_node): # Check if the next node is the source node. That means that this path description is finished, so appendit
                            received_table.append(temp_list)
                            temp_list = []
                    #elif (data.index(identifier) == len(data) - 1):  # comes to the last elements
                    else: #The node we just popped was the last node
                            received_table.append(temp_list)
                            temp_list = []
                handle_route_update(received_table)

            # HELLO message, get sequence number from HELLO
            # send ACK with the sequence number back
            #if (msg_type == MESSAGE_TYPE.HELLO):
            #    print_screen(screen, CONTROL.UPDATE, "A hello from: " + "#" + str(STATUS.BLUE) + "[node " + str(direct_source_node) + "]")
            #    seq_num = int(data[2])
            #    dh_address = address_generator(direct_source_node)
            #    reply_ack(dh_address, seq_num)
            #
            # ACK from DH, record the received sequence number
            #if (msg_type == MESSAGE_TYPE.ACK):
            #    seq_num = int(data[2])
            #    for DH_key in DHList:
            #        if (direct_source_node == DH_key):
            #            DHList[DH_key][0] = seq_num
            #            break

            # A triggered message from SOURCE -> SERVER, response to it via LED(GREEN) on the path
            # if I am not server, forward it according to routing table
            # if I am the server, send Data ACK back to source node
            if (msg_type == MESSAGE_TYPE.DATA_IN or msg_type == MESSAGE_TYPE.DATA_OUT):
                destination_node = int(data[2])
                timestamp_string = data[3]
                timestamp_float = float(data[4])
                if (SERVER == HOST):  # if I am the server, recorde the timestamp, send to laptop, send ACK back to source node
                    for route_list in ROUTETable:
                        if (route_list[-1] == destination_node):  # find the routing path
                            path_node = int(route_list[1])
                            path_address = address_generator(path_node)
                            reply_sensor_ack(path_address, destination_node, timestamp_float)
                            node_color = "#" + str(STATUS.BLUE) + "[node " + str(destination_node) + "]"
                            message = ''
                            if (msg_type == MESSAGE_TYPE.DATA_IN):
                                print_screen(screen, CONTROL.UPDATE, "Object is in the range of node " + node_color)
                                message = str(MESSAGE_TYPE.DATA_IN)
                            elif (msg_type == MESSAGE_TYPE.DATA_OUT):
                                print_screen(screen, CONTROL.UPDATE, "Object stops moving or steps out of the range of node " + node_color)
                                message = str(MESSAGE_TYPE.DATA_OUT)

                            # server will also resend the message to laptop, then blink the green LED
                            message = message + ' ' + str(SERVER) + ' ' + str(destination_node) + ' ' + timestamp_string + ' ' + str(timestamp_float)
                            socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            socket_s.settimeout(UPDATE_TIMEOUT)
                            socket_s.sendto(message, (LAPTOP_ADD, PORT))

                            distance = len(route_list) - 1
                            tBlinkBlue = threading.Thread(target = blink_blue, args = (distance,))  # blink Blue LED when server sends ACK
                            tBlinkBlue.start()
                            break
                else:  # if I am not the server, forward it to the server according to routing table
                    source_node = destination_node
                    for route_list in ROUTETable:
                        if (route_list[-1] == SERVER):
                            path_node = int(route_list[1])
                            path_address = address_generator(path_node)
                            send_sensor_event(path_address, source_node, timestamp_string, timestamp_float, msg_type)

                            distance = len(route_list) - 1
                            tBlinkGreen = threading.Thread(target = blink_green, args = (distance,))  # blink Green LED when server sends ACK
                            tBlinkGreen.start()
                            break;

            # DataACK from SERVER -> SOURCE(DESTINATION), in here the LED(BLUE) will blink to it if local is destination
            # if I am not the destination, forward the ack to source node according to routing table
            # if I am the destination, terminate the transmission, blink LED
            if (msg_type == MESSAGE_TYPE.DATAACK):
                destination_node = int(data[2])
                timestamp_float = float(data[3])
                if (destination_node == HOST):  # if I am the destination
                    if (time.time() - timestamp_float <= UPDATE_INTERVAL):  # ACK is not late
                        print_screen(screen, CONTROL.UPDATE, "A triggered message ACK received from server: " + "#" + str(STATUS.BLUE) + "[node " + str(SERVER) + "]")
                    else:
                        print_screen(screen, CONTROL.WARNING, "#" + str(STATUS.RED) + "[An ACK to sensor message is delayed]")

                    tBlinkBlue = threading.Thread(target = blink_blue)  # blink Blue LED when sender receives the ACK
                    tBlinkBlue.start()
                else:  # if I am not the destination, forward the message to destination according to routing table
                    for route_list in ROUTETable:
                        if (route_list[-1] == destination_node):
                            path_node = int(route_list[1])
                            path_address = address_generator(path_node)
                            reply_sensor_ack(path_address, destination_node, timestamp_float)

        except socket.error:
            pass
    # end of while
# end of handle_communication


def terminate(thread):
    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


# this function will do sending updates
def send_update(dh_address):
    chain = itertools.chain(*ROUTETable)  # flat the routing table into an one dimension list
    message = list(chain)
    message = [str(x) for x in message]
    message = ' '.join(message)  # make the flatted routing table into a string
    message = str(MESSAGE_TYPE.UPDATE) + ' ' + message

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))

# this function will do sending hello
def send_hello(dh_address, sequenceNum):
    message = str(MESSAGE_TYPE.HELLO)
    message = message + ' ' + str(HOST) + ' ' + str(sequenceNum)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(HELLO_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))


# this function will do replying hello
def reply_ack(dh_address, sequenceNum):
    message = str(MESSAGE_TYPE.ACK)
    message = message + ' ' + str(HOST) + ' ' + str(sequenceNum)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(HELLO_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))


# this function will do sending server information
def send_server_info(dh_address):
    message = str(MESSAGE_TYPE.SERVER)
    message = message + ' ' + str(HOST) + ' ' + str(SERVER)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (dh_address, PORT))


# this function will do replying server
def reply_server(path_address, source_node):
    message = str(MESSAGE_TYPE.SERVERACK)
    message = message + ' ' + str(HOST) + ' ' + str(source_node)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (path_address, PORT))


# this function will generate triggered message to server, including timestamp, SOURCE -> SERVER
def send_sensor_event(path_address, source_node, timestamp_string, timestamp_float, type):
    message = ''
    if (type == MESSAGE_TYPE.DATA_IN):
        message = str(MESSAGE_TYPE.DATA_IN)
        message = message + ' ' + str(HOST) + ' ' + str(source_node) + ' ' + timestamp_string + ' ' + str(timestamp_float)
    elif (type == MESSAGE_TYPE.DATA_OUT):
        message = str(MESSAGE_TYPE.DATA_OUT)
        message = message + ' ' + str(HOST) + ' ' + str(source_node) + ' ' + timestamp_string + ' ' + str(timestamp_float)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (path_address, PORT))


# this function will do replying the triggered message, SERVER -> DESTINATION
def reply_sensor_ack(path_address, destination_node, timestamp_float):
    message = str(MESSAGE_TYPE.DATAACK)
    message = message + ' ' + str(HOST) + ' ' + str(destination_node) + ' ' + str(timestamp_float)

    # Send UDP datagram
    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_s.settimeout(UPDATE_TIMEOUT)
    socket_s.sendto(message, (path_address, PORT))


# this function will do updating local table and destination based on the received table
def handle_route_update(received_table):
    global ROUTETable, DSTList

    for update_list in received_table:
        new_destination = int(update_list[-1])
        if (new_destination in DSTList or new_destination == HOST):  # updated destination is in current destination list
            continue
        else:  # updated destination is not in current destination list, add to DSTList and ROUTETable
            new_route_list = update_list
            new_route_list.insert(0, HOST)
            new_distance = len(new_route_list) - 1
            ROUTETable.append(new_route_list)  # update the routing table
            DSTList.update({new_destination:new_distance})  # update the destination list


def event_call_back(channel):
    global EVENT_DETECTED
    EVENT_DETECTED = 1


def handle_sensor_event(screen, start):
    global EVENT_DETECTED
    time.sleep(2)
    while True:
        if (EVENT_DETECTED):  # waiting for event detection signal
            if GPIO.input(PIR_PIN):  # signal from 0 -> 1, node being triggered
                time0t1 = datetime.datetime.now()
                timestamp_string = str(time0t1.replace(microsecond = 0))
                timestamp_string = re.sub(r' ', '@', timestamp_string)
                timestamp_float = time.time()
                node_color = "#" + str(STATUS.YELLOW) + "[" + str(HOST) + "]"
                time_color = "#" + str(STATUS.YELLOW) + "[" + str(time0t1.replace(microsecond=0)) + "]"
                string = "Object is within detection range of node " + node_color + " since " + time_color
                print_screen(screen, CONTROL.UPDATE, string)

                if (SERVER and SERVER != HOST):  # if local node knows the server, send triggered message with timestamp to server
                    for route_list in ROUTETable:  # find the routing path
                        if (route_list[-1] == SERVER):
                            path_node = int(route_list[1])
                            path_address = address_generator(path_node)
                            send_sensor_event(path_address, HOST, timestamp_string, timestamp_float, MESSAGE_TYPE.DATA_IN)
                            distance = len(route_list) - 1
                            tBlinkGreen = threading.Thread(target = blink_green, args = (distance, ))  # blink the Green LED
                            tBlinkGreen.start()
                            EVENT_DETECTED = 0
                            break

                elif (SERVER == HOST):  # if local node is the server, send the message to laptop directly
                    message = str(MESSAGE_TYPE.DATA_IN) + ' ' + str(SERVER) + ' ' + str(SERVER) + ' ' + timestamp_string + ' ' + str(timestamp_float)
                    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    socket_s.settimeout(UPDATE_TIMEOUT)
                    socket_s.sendto(message, (LAPTOP_ADD, PORT))
                    EVENT_DETECTED = 0

            else:  # signal form 1 -> 0, object is leaving or keeping still
                time1t0 = datetime.datetime.now()
                timestamp_string = str(time1t0.replace(microsecond=0))
                timestamp_string = re.sub(r' ', '@', timestamp_string)
                timestamp_float = time.time()
                node_color = "#" + str(STATUS.YELLOW) + "[" + str(HOST) + "]"
                time_color = "#" + str(STATUS.YELLOW) + "[" + str(time1t0.replace(microsecond = 0)) + "]"
                string = "Object stops moving or step out of the detection range of node " + node_color + " since " + time_color
                print_screen(screen, CONTROL.UPDATE, string)

                if (SERVER and SERVER != HOST):  # if local node knows the server, notify server that the object is no longer sensed
                    for route_list in ROUTETable:
                        if (route_list[-1] == SERVER):
                            path_node = int(route_list[1])
                            path_address = address_generator(path_node)
                            send_sensor_event(path_address, HOST, timestamp_string, timestamp_float, MESSAGE_TYPE.DATA_OUT)
                            distance = len(route_list) - 1
                            tBlinkGreen = threading.Thread(target = blink_green, args = (distance, ))  # blink the Green LED
                            tBlinkGreen.start()
                            EVENT_DETECTED = 0
                            break

                elif (SERVER == HOST):  # if local node is the server
                    message = str(MESSAGE_TYPE.DATA_OUT) + ' ' + str(SERVER) + ' ' + str(SERVER) + ' ' + timestamp_string + ' ' + str(timestamp_float)
                    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    socket_s.settimeout(UPDATE_TIMEOUT)
                    socket_s.sendto(message, (LAPTOP_ADD, PORT))
                    EVENT_DETECTED = 0
        # end of big if
        time.sleep(2)
    # end of big while


# this function will blink blue LED in order to react to ACK of triggered message
def blink_blue():
    GPIO.output(BLUE_PIN, True)
    time.sleep(LED_DELAY)
    GPIO.output(BLUE_PIN, False)


# this function will blink red LED in order to react to DH lost & packet lost (no ACK)
def blink_red():
    GPIO.output(RED_PIN, True)
    time.sleep(LED_DELAY)
    GPIO.output(RED_PIN, False)


# this function will blink green LED in order to react to triggered message, the number of LED is based on distance
def blink_green(distance):
    for i in range(distance):
        GPIO.output(GREEN_PIN, True)
        time.sleep(LED_DELAY)
        GPIO.output(GREEN_PIN, False)
        time.sleep(LED_DELAY)


if __name__ == "__main__":
    init()
