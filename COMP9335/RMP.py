############################################################################
#
# RIP-like Multi-hop Protocol (RMP)
# For: COMP(49)335 Wireless Mesh & Sensor Network, UNSW
# Project Title: Time Synchronisation for Activity Monitoring
#
# RMP is a light-weight dynamic routing protocol for sensor network, used in
# the research project Time Synchronisation for Activity Monitoring. Each node in
# the protocol will finally has a topology of the whole network while in the
# convergence status. The metric in RMP is based on hop number, with server
# (called designated node) flooding mechanism, triggered update, and a periodical
# hello behaviour between neighbours acting as heart-beat detection for keep-alive
#
#############################################################################

import re
import time
import socket
import itertools
import ctypes
import curses
import curses.ascii
import threading
import RPi.GPIO as GPIO     #import Pi general-purpose input/output (GPIO) library
import datetime
from string import printable


"""Class Node will provide base infrastructures to a local node
"""
class Node(object):
    def __init__(self):
        self.TOTAL_NODES = 0
        self.SERVER = 0
        self.LAPTOP_ADD = "192.168.1.106"
        self.DHList = {}      # neighbour list
        self.ROUTETable = []  # routing table, contains routing list
        self.DSTList = {}     # destination list
        self.TOTAL_NODES = 0  # total number of nodes in the network
        self.SERVER = 0       # server tag
        self.SERVER_CONVERGENCE = 0
        self.HOST = 0
        self.HOST_ADDRESS = ""
        self.CONVERGENCE = 0
        self.SERVER_CONVERGENCE = 0
        self.EVENT_DETECTED = 0


    """Reset & Clean all states
    """
    def reset(self):
        self.TOTAL_NODES = 0
        self.SERVER = 0
        self.LAPTOP_ADD = ""
        self.DHList = {}
        self.ROUTETable = []
        self.DSTList = {}
        self.TOTAL_NODES = 0
        self.SERVER = 0
        self.HOST = 0
        self.HOST_ADDRESS = ""
        self.CONVERGENCE = 0
        self.SERVER_CONVERGENCE = 0
        self.EVENT_DETECTED = 0

    """Define the Enumeration type
    """
    def enum(self, **enums):
        return type('Enum', (), enums)


    """Setup the static values, including enumeration of the system
    """
    def setup_states(self):
        global STATUS, PEER_STATUS, CONTROL, MESSAGE_TYPE, PRINTABLE
        global PORT, UPDATE_INTERVAL, UPDATE_TIMEOUT, HELLO_INTERVAL, HELLO_TIMEOUT, HELLO_LOST, SERVER_INTERVAL
        global SUCCESSIVE_LOST, SEQ, BUFFER
        global GREEN_PIN, RED_PIN, BLUE_PIN, LED_DELAY, PIR_PIN, VERSION

        STATUS = self.enum(NORMAL = 1, WARNING = 2, COMMAND = 3, RED = 4, GREEN = 5, ERROR = 6, YELLOW = 7, BLUE = 8, RESULT = 9)
        PEER_STATUS = self.enum(OK = 1, INVALID = 2, DEAD = 3)
        CONTROL = self.enum(NORMAL = 1, WARNING = 2, UPDATE = 3, HELLO = 4, ERROR = 5, RESULT = 6)
        MESSAGE_TYPE = self.enum(UPDATE = 1, HELLO = 2, ACK = 3, SERVERACK = 4, DATAACK = 5, SERVER = 6, DATA_IN = 7, DATA_OUT = 8)
        PRINTABLE = map(ord, printable)

        PORT = 55056  # for sending / listening table updates
        UPDATE_INTERVAL = 5.0
        UPDATE_TIMEOUT = 15.0
        HELLO_INTERVAL = 5.0
        HELLO_TIMEOUT = 2.0
        HELLO_LOST = 4
        SERVER_INTERVAL = 5.0
        SUCCESSIVE_LOST = 3
        SEQ = 65535
        BUFFER = 1024
        GREEN_PIN = 25
        RED_PIN = 21
        BLUE_PIN = 23
        LED_DELAY = 0.5
        PIR_PIN = 16
        VERSION = "RMP alpha, version 0.9"


    """Set up the pins
    """
    def setup_pins(self):
        global GREEN_PIN, RED_PIN, BLUE_PIN, LED_DELAY, PIR_PIN, STATUS, VERSION

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GREEN_PIN, GPIO.OUT)  # setup GPIO output channel
        GPIO.setup(RED_PIN, GPIO.OUT)    # setup GPIO output channel
        GPIO.setup(BLUE_PIN, GPIO.OUT)   # setup GPIO output channel
        GPIO.setup(PIR_PIN, GPIO.IN)     # setup GPIO 16 as INPUT
        GPIO.add_event_detect(PIR_PIN, GPIO.BOTH, callback = event_call_back, bouncetime = 300)


    """Start the program
    """
    def init(self):
        self.setup_pins()
        self.setup_states()
        curses.wrapper(self.initiate)  # The main function will runs in a new screen which can support customised commands


    """Initiate the system, user has to configure the local node for the initiation
    """
    def initiate(self, screen):
        global history, window_size, height
        global STATUS, PEER_STATUS, CONTROL, MESSAGE_TYPE, PRINTABLE
        global VERSION

        Y, X = screen.getmaxyx()
        history = []
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
        self.print_screen(screen, CONTROL.NORMAL, "Please configure local node under the following scheme to ")
        self.print_screen(screen, CONTROL.NORMAL, "initiate the protocol:")
        self.print_screen(screen, CONTROL.NORMAL, "1. Input the total number of nodes in the network: ")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[network (total_number)]]")
        self.print_screen(screen, CONTROL.NORMAL, "2. Input the local identifier (LI) and direct hops (DH): ")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[node (LI) (DH ...)]]")
        self.print_screen(screen, CONTROL.NORMAL, "3. Designate local node as server, this will flood server info")
        self.print_screen(screen, CONTROL.NORMAL, "to all the other nodes, or use command [#" + str(STATUS.COMMAND) + "[done]] to skip:")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[server]]")

        network_configured = 0
        node_configured = 0
        display_type = 0
        done = 0

        # initialise the protocol
        while (not network_configured or not node_configured or not done):
            command = stdin_to_command(screen, height, display_type, self.HOST)
            command_color = "#" + str(STATUS.COMMAND) + "[" + command + "]"
            command_error = "#" + str(STATUS.YELLOW) + "[" + command + "]"
            if (network_configured and node_configured and done):
                display_type = 1
                break
            elif (command.startswith("node") or command.startswith("network") or command.startswith("server") or command.startswith("done")):
                if (command.startswith("network")):  # record the total number of nodes
                    try:
                        parameter = int(command.split()[1])
                        self.print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                        self.TOTAL_NODES = parameter
                        network_configured = 1
                    except:
                        self.print_screen(screen, CONTROL.ERROR, "Invalid parameter(s) in command: " + command_error)
                        continue

                elif (command.startswith("node")):  # record the information of DHs
                    try:
                        parameter = command.split()
                        self.HOST = int(parameter[1])
                        self.HOST_ADDRESS = self.address_generator(self.HOST)
                        for num in parameter[2:]:
                            DH = int(num)
                            self.DHList[DH] = [0, 0]  # DHList: [A, B, C], A is DH identifier, B is received sequence number, C is successive lost number
                            self.ROUTETable.append([self.HOST, DH])
                            self.DSTList[DH] = 1  # DSTList: [A, B], A is DH identifier, B is distance to A
                        self.print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                        node_configured = 1
                    except:
                        self.print_screen(screen, CONTROL.ERROR, "Invalid parameter(s) in command: " + command_error)
                        continue

                elif (command == "server" and node_configured == 1):  # local node is the server
                    self.print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                    self.SERVER = int(self.HOST)
                    done = 1

                elif (command == "server" and node_configured == 0):
                    self.print_screen (screen, CONTROL.ERROR, "Node must be configured firstly before being designated as a server.")

                elif (command == "done"):
                    done = 1
                    self.print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)

            elif (command == ''):
                self.print_screen(screen, CONTROL.NORMAL, "")
            else:
                self.print_screen (screen, CONTROL.ERROR, "Command unknown: " + command_error)

            self.roll_up_screen(screen)
            screen.refresh()
        # end of while

        self.print_screen(screen, CONTROL.NORMAL, "")
        self.print_screen(screen, CONTROL.NORMAL, "")
        self.print_screen(screen, CONTROL.NORMAL, "")
        self.print_screen(screen, CONTROL.NORMAL, "Protocol initialised (" + VERSION + ")")
        self.print_screen(screen, CONTROL.NORMAL, "Sensor module starting ...")
        self.print_screen(screen, CONTROL.NORMAL, "Local identifier: " + "#" + str(STATUS.BLUE) + "[" + str(self.HOST) + "]")
        self.print_screen(screen, CONTROL.NORMAL, "Local ip address: " + "#" + str(STATUS.BLUE) + "[" + self.HOST_ADDRESS + "]")
        self.print_screen(screen, CONTROL.NORMAL, "")
    # end of initiate


    """Refresh the window
    """
    def print_screen(self, screen, control, message):
        global history
        height = len(history)
        Y, X = screen.getyx()  # save current position
        self.print_single_line(screen, height, control, message)
        history.append([control, message])

        self.roll_up_screen(screen)
        screen.move(Y, X)  # restore the position
        screen.refresh()


    """Print the single line to the window based on CONTROL code
    """
    def print_single_line(self, screen, height, control, message):
        global STATUS, PEER_STATUS, CONTROL, MESSAGE_TYPE, PRINTABLE

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


    """Roll up the screen if the screen has been fully occupied
    """
    def roll_up_screen(self, screen):
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
                self.print_single_line(screen, index, line[0], line[1])


    """Get the address of local node
    """
    def address_generator(self, host):
        #prefix = "10.11.11."
        prefix = "192.168.1."
        host_address = prefix + str(host)
        #host_address = socket.gethostbyname(socket.gethostname())
        return host_address


"""Class Router will provide Hello, Update, Server, Event monitor, Info Flood mechanisms to the network
"""
class Router(Node):
    def __init__(self):
        Node.__init__(self)


    """Call super's method
    """
    def reset(self):
        Node.reset(self)


    """Call super's method, and start run the method "operation"
    """
    def init(self):
        Node.init(self)
        curses.wrapper(self.operation)  # The main function will runs in a new screen which can support customised commands


    """Core method, will start the thread of routing, and the thread of event monitor,
       and provide "show" functions to the user for displaying information of the network
    """
    def operation(self, screen):
        global history, window_size, height
        global STATUS, PEER_STATUS, CONTROL, MESSAGE_TYPE, PRINTABLE
        global VERSION
        display_type = 1

        # start threads now
        tHandleUdpAll = threading.Thread(target = self.handle_communication, args = (screen, 1))  # a bug in here, _curses.urses has no window
        tHandleUdpAll.start()
        self.print_screen(screen, CONTROL.NORMAL, "Communication module started")
        tHandleSensorEvent = threading.Thread(target = self.handle_sensor_event, args = (screen, 1))
        tHandleSensorEvent.start()
        self.print_screen(screen, CONTROL.NORMAL, "Sensor module started")
        self.print_screen(screen, CONTROL.NORMAL, "Protocol operating, " + VERSION)
        self.print_screen(screen, CONTROL.NORMAL, "Tips:")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show routingtable]] will display the current routing table.")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show neighbour]] will display the current neighbour list.")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show destination]] will display the current known destinations.")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show metric]] will display the metric of every destination.")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show server]] will display the current server node.")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show info]] will display system information like ip address.")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[server]] will designate a new server node.")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[quit]] will terminate the program.")
        self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[help]] will re-display tips above.")

        # user can input command now
        while True:
            command = stdin_to_command(screen, height, display_type, self.HOST)
            command_color = "#" + str(STATUS.COMMAND) + "[" + command + "]"
            command_error = "#" + str(STATUS.YELLOW) + "[" + command + "]"

            # Quit command
            if (command == "quit"):
                if (tHandleSensorEvent.isAlive()):
                    self.terminate(tHandleSensorEvent)
                if (tHandleUdpAll.isAlive()):
                    self.terminate(tHandleUdpAll)
                self.print_screen(screen, CONTROL.NORMAL, "Local node is leaving network now.")
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
                    self.print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                    if (parameter == "routingtable"):
                        if (len(self.ROUTETable) == 0):
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Routing table is empty]")
                        else:
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Current routing table:]")
                            for r_list in self.ROUTETable:
                                result = '# %s #' % ' - '.join(map(str, r_list))
                                self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                    elif (parameter == "neighbour"):
                        if (len(self.DHList) == 0):
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Neighbour list is empty]")
                        else:
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[List of Direct Hop(s):]")
                            for DH_key in self.DHList:
                                result = "DH label: " + str(DH_key)
                                self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                    elif (parameter == "destination"):
                        if (len(self.DSTList) == 0):
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Destination list is empty]")
                        else:
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Known destination(s):]")
                            for DST_key in self.DSTList:
                                result = "# " + str(DST_key)
                                self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                    elif (parameter == "metric"):
                        if (len(self.DSTList) == 0):
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Destination list is empty]")
                        else:
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[Destination  Metric]")
                            for DST_key in self.DSTList:
                                result = '     ' + str(DST_key) + '          ' + str(self.DSTList[DST_key])
                                self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                    elif (parameter == "server"):
                        if (not self.SERVER):
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[No designated node]")
                        elif (self.SERVER == self.HOST):
                            result = "Designated node is local node: " + str(self.SERVER)
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")
                        else:
                            result = "Designated node is: node " + str(self.SERVER)
                            self.print_screen(screen, CONTROL.RESULT, "#" + str(STATUS.GREEN) + "[" + result + "]")

                    elif (parameter == "info"):
                        self.print_screen(screen, CONTROL.NORMAL, VERSION)
                        self.print_screen(screen, CONTROL.NORMAL, "Local identifier: " + "#" + str(STATUS.BLUE) + "[" + str(self.HOST) + "]")
                        self.print_screen(screen, CONTROL.NORMAL, "Local ip address: " + "#" + str(STATUS.BLUE) + "[" + self.HOST_ADDRESS + "]")

                    else:
                        command_error = "#" + str(STATUS.YELLOW) + "[" + parameter + "]"
                        self.print_screen (screen, CONTROL.ERROR, "Unknown \"show\" parameter(s): " + command_error)

                except:
                    self.print_screen (screen, CONTROL.ERROR, "Invalid parameter(s): " + command_error)
                    continue

            elif (command == "server" and self.SERVER == self.HOST):
                self.print_screen (screen, CONTROL.ERROR, "Local node is already designated as server.")
            elif (command == "server"):
                self.print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                self.SERVER_CONVERGENCE = 0
                self.SERVER = int(self.HOST)

            elif (command == "help"):
                self.print_screen(screen, CONTROL.NORMAL, "Command: " + command_color)
                self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show routingtable]] will display the current routing table.")
                self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show neighbour]] will display the current neighbour list.")
                self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show destination]] will display the current known destinations.")
                self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show metric]] will display the metric of every destination.")
                self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show server]] will display the current server node.")
                self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[show info]] will display system information like ip address.")
                self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[server]] will designate a new server node.")
                self.print_screen(screen, CONTROL.NORMAL, "[#" + str(STATUS.COMMAND) + "[quit]] will terminate the program.")

            elif (command == ''):
                self.print_screen(screen, CONTROL.NORMAL, "")

            else:
                self.print_screen (screen, CONTROL.ERROR, "Command unknown: " + command_error)

            self.roll_up_screen(screen)
            screen.refresh()


    """Core method of routing, will analyse received packets and call relating methods for processing them
    """
    def handle_communication(self, screen, start):
        global STATUS, PEER_STATUS, CONTROL, MESSAGE_TYPE, PRINTABLE
        global PORT, UPDATE_INTERVAL, UPDATE_TIMEOUT, HELLO_INTERVAL, HELLO_TIMEOUT, HELLO_LOST, SERVER_INTERVAL
        global SUCCESSIVE_LOST, SEQ, BUFFER

        # a listen socket, listening on port 5678 (UDP)
        socket_l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_l.settimeout(UPDATE_TIMEOUT)
        self.print_screen(screen, CONTROL.NORMAL, "Host: " + self.HOST_ADDRESS);
        socket_l.bind((self.HOST_ADDRESS, PORT))
        sent_time = 0
        sent_time2 = 0
        #sent_time3 = 0
        #sequenceNum = 0
        server_reply = []

        while True:
            if (((time.time() - sent_time2) >= SERVER_INTERVAL) and self.SERVER == self.HOST and (not self.SERVER_CONVERGENCE)):  # I am the server, fload the SERVER message
                for DH_key in self.DHList:
                    dh_address = self.address_generator(DH_key)
                    self.send_server_info(dh_address)
                sent_time2 = time.time()

            #if (((time.time() - sent_time3) >= HELLO_INTERVAL) and CONVERGENCE):  # After convergence, send HELLO
            #    for DH_key in DHList:
            #        dh_address = address_generator(DH_key)
            #        send_hello(dh_address, sequenceNum)
            #    sequenceNum = (sequenceNum + 1) % SEQ
            #    sent_time3 = time.time()

            if (((time.time() - sent_time) >= UPDATE_INTERVAL) and (not self.CONVERGENCE)):  # Before convergence, send UPDATE
                for DH_key in self.DHList:
                    dh_address = self.address_generator(DH_key)
                    self.send_update(dh_address)
                sent_time = time.time()
                if (len(self.DSTList) == (self.TOTAL_NODES - 1)):  # if the nodes number is the length of destination list, then in convergence
                    self.CONVERGENCE = 1

            # calculate the successive lost ACK from a DH, then check whether it is larger then the limitation of SUCCESSIVE_LOST
            #for DH_key in DHList:
            #    DHList[DH_key][1] = 0
            #    if (sequenceNum < DH[1]):
            #        DHList[DH_key][1] = (SEQ - DHList[DH_key][0]) + sequenceNum
            #    else:
            #        DHList[DH_key][1] = sequenceNum - DHList[DH_key][0]

                # if a DH is lost, then delete every information from database, and CONVERGENCE status becomes false
            #    if (DHList[DH_key][1] >= SUCCESSIVE_LOST):
            #        print_screen(screen, CONTROL.WARNING, "DH node: " + "#" + str(STATUS.RED) + "[" + str(DH_key) + "]" + " is lost")
            #        tBlinkRed = threading.Thread(target = blink_red)
            #        tBlinkRed.start()

            #        CONVERGENCE = 0
            #        lostDH = int(DH_key)
            #        del DHList[DH_key]
            #        for routing_list in ROUTETable:
            #            for identifier in routing_list:
            #                if (int(identifier) == lostDH) :
            #                    ROUTETable.remove(routing_list)
            #                    break

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
                    self.handle_server(screen, data, direct_source_node)

                # if receive a reply from SOURCE -> LOCAL -> SERVER
                # forward it to the server according to routing table
                # this will not change the source node information
                if (msg_type == MESSAGE_TYPE.SERVERACK):
                    server_reply = self.handle_server_ack(screen, data, server_reply)

                # update message, if in convergence then drop it
                # if not in convergence, handle the update
                # recover the update information into a two dimension list
                # then pass it to another function
                if (msg_type == MESSAGE_TYPE.UPDATE and (not self.CONVERGENCE)):
                    del data[0]
                    self.print_screen(screen, CONTROL.UPDATE, "A routing table update received from: " + "#" + str(STATUS.BLUE) + "[node " + str(direct_source_node) + "]")
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
                    self.handle_route_update(received_table)

                # HELLO message, get sequence number from HELLO
                # send ACK with the sequence number back
                #if (msg_type == MESSAGE_TYPE.HELLO):
                #    print_screen(screen, CONTROL.UPDATE, "A hello from: " + "#" + str(STATUS.BLUE) + "[node " + str(direct_source_node) + "]")
                #    seq_num = int(data[2])
                #    dh_address = address_generator(direct_source_node)
                #    reply_ack(dh_address, seq_num)

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
                    self.handle_data(screen, data, msg_type)

                # DataACK from SERVER -> SOURCE(DESTINATION), in here the LED(BLUE) will blink to it if local is destination
                # if I am not the destination, forward the ack to source node according to routing table
                # if I am the destination, terminate the transmission, blink LED
                if (msg_type == MESSAGE_TYPE.DATAACK):
                    self.handle_data_ack(screen, data)

            except socket.error:
                pass
        # end of while
    # end of handle_communication


    def handle_hello(self, data):
        test = 1


    def handle_server(self, screen, data, direct_source_node):
        global CONTROL, STATUS

        if (self.SERVER == 0):
            self.SERVER = int(data[2])  # record the server
            self.SERVER_CONVERGENCE = 1
            self.print_screen(screen, CONTROL.UPDATE, "Local node is now aware of Designated Node: " + "#" + str(STATUS.BLUE) + "[node " + str(self.SERVER) + "]")
        for route_list in self.ROUTETable:  # reply to server, search the routing table, SOURCE -> SERVER
            if (route_list[-1] == self.SERVER):
                path_node = int(route_list[1])
                path_address = self.address_generator(path_node)
                self.reply_server(path_address, self.HOST)
                break
        for DH_key in self.DHList:  # then flood the server message to other DHs
            if (direct_source_node != DH_key):  # split horizon
                dh_address = self.address_generator(DH_key)
                self.send_server_info(dh_address)


    def handle_server_ack(self, screen, data, server_reply):
        global CONTROL

        source_node = int(data[2])
        if (self.SERVER == self.HOST):  # if I am the server, record the source node
            if (not (source_node in server_reply)):
                server_reply.append(source_node)
            if (len(server_reply) == self.TOTAL_NODES - 1):  # all nodes know server identifier
                self.SERVER_CONVERGENCE = 1
                self.print_screen(screen, CONTROL.UPDATE, "Designated Node info is fully synchronised among the network now")
        else:  # I am not the server, forward it to server according to routing table
            if (self.SERVER):  # only when local node knows the server
                for route_list in self.ROUTETable:
                    if (route_list[-1] == self.SERVER):
                        path_node = int(route_list[1])
                        path_address = self.address_generator(path_node)
                        self.reply_server(path_address, source_node)
                        break
        return server_reply


    def handle_data(self, screen, data, msg_type):
        global MESSAGE_TYPE, CONTROL, STATUS

        destination_node = int(data[2])
        timestamp_string = data[3]
        timestamp_float = float(data[4])
        if (self.SERVER == self.HOST):  # if I am the server, recorde the timestamp, send to laptop, send ACK back to source node
            for route_list in self.ROUTETable:
                if (route_list[-1] == destination_node):  # find the routing path
                    path_node = int(route_list[1])
                    path_address = self.address_generator(path_node)
                    self.reply_sensor_ack(path_address, destination_node, timestamp_float)
                    node_color = "#" + str(STATUS.BLUE) + "[node " + str(destination_node) + "]"
                    message = ''
                    if (msg_type == MESSAGE_TYPE.DATA_IN):
                        self.print_screen(screen, CONTROL.UPDATE, "Object is in the range of node " + node_color)
                        message = str(MESSAGE_TYPE.DATA_IN)
                    elif (msg_type == MESSAGE_TYPE.DATA_OUT):
                        self.print_screen(screen, CONTROL.UPDATE, "Object stops moving or steps out of the range of node " + node_color)
                        message = str(MESSAGE_TYPE.DATA_OUT)

                    # server will also resend the message to laptop, then blink the green LED
                    message = message + ' ' + str(self.SERVER) + ' ' + str(destination_node) + ' ' + timestamp_string + ' ' + str(timestamp_float)
                    socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    socket_s.settimeout(UPDATE_TIMEOUT)
                    socket_s.sendto(message, (self.LAPTOP_ADD, PORT))

                    distance = len(route_list) - 1
                    tBlinkBlue = threading.Thread(target = self.blink_blue)  # blink Blue LED when server sends ACK
                    tBlinkBlue.start()
                    break
        else:  # if I am not the server, forward it to the server according to routing table
            source_node = destination_node
            for route_list in self.ROUTETable:
                if (route_list[-1] == self.SERVER):
                    path_node = int(route_list[1])
                    path_address = self.address_generator(path_node)
                    self.send_sensor_event(path_address, source_node, timestamp_string, timestamp_float, msg_type)

                    distance = len(route_list) - 1
                    tBlinkGreen = threading.Thread(target = self.blink_green, args = (distance,))  # blink Green LED when server sends ACK
                    tBlinkGreen.start()
                    break;


    def handle_data_ack(self, screen, data):
        global CONTROL, STATUS

        destination_node = int(data[2])
        timestamp_float = float(data[3])
        if (destination_node == self.HOST):  # if I am the destination
            if (time.time() - timestamp_float <= UPDATE_INTERVAL):  # ACK is not late
                self.print_screen(screen, CONTROL.UPDATE, "A triggered message ACK received from server: " + "#" + str(STATUS.BLUE) + "[node " + str(self.SERVER) + "]")
            else:
                self.print_screen(screen, CONTROL.WARNING, "#" + str(STATUS.RED) + "[An ACK to sensor message is delayed]")

            tBlinkBlue = threading.Thread(target = self.blink_blue)  # blink Blue LED when sender receives the ACK
            tBlinkBlue.start()
        else:  # if I am not the destination, forward the message to destination according to routing table
            for route_list in self.ROUTETable:
                if (route_list[-1] == destination_node):
                    path_node = int(route_list[1])
                    path_address = self.address_generator(path_node)
                    self.reply_sensor_ack(path_address, destination_node, timestamp_float)


    """will do updating local table and destination based on the received table
    """
    def handle_route_update(self, received_table):
        for update_list in received_table:
            new_destination = int(update_list[-1])
            if (new_destination in self.DSTList or new_destination == self.HOST):  # updated destination is in current destination list
                continue
            else:  # updated destination is not in current destination list, add to DSTList and ROUTETable
                new_route_list = update_list
                new_route_list.insert(0, self.HOST)
                new_distance = len(new_route_list) - 1
                self.ROUTETable.append(new_route_list)  # update the routing table
                self.DSTList.update({new_destination:new_distance})  # update the destination list


    """will do sending updates
    """
    def send_update(self, dh_address):
        global MESSAGE_TYPE, PORT

        chain = itertools.chain(*self.ROUTETable)  # flat the routing table into an one dimension list
        message = list(chain)
        message = [str(x) for x in message]
        message = ' '.join(message)  # make the flatted routing table into a string
        message = str(MESSAGE_TYPE.UPDATE) + ' ' + message

        # Send UDP datagram
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.settimeout(UPDATE_TIMEOUT)
        socket_s.sendto(message, (dh_address, PORT))


    """will do sending hello
    """
    def send_hello(self, dh_address, sequenceNum):
        global MESSAGE_TYPE, PORT

        message = str(MESSAGE_TYPE.HELLO)
        message = message + ' ' + str(self.HOST) + ' ' + str(sequenceNum)
        # Send UDP datagram
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.settimeout(HELLO_TIMEOUT)
        socket_s.sendto(message, (dh_address, PORT))


    """will do replying hello
    """
    def reply_ack(self, dh_address, sequenceNum):
        global MESSAGE_TYPE, PORT

        message = str(MESSAGE_TYPE.ACK)
        message = message + ' ' + str(self.HOST) + ' ' + str(sequenceNum)
        # Send UDP datagram
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.settimeout(HELLO_TIMEOUT)
        socket_s.sendto(message, (dh_address, PORT))


    """this function will do sending server information
    """
    def send_server_info(self, dh_address):
        global MESSAGE_TYPE, PORT

        message = str(MESSAGE_TYPE.SERVER)
        message = message + ' ' + str(self.HOST) + ' ' + str(self.SERVER)
        # Send UDP datagram
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.settimeout(UPDATE_TIMEOUT)
        socket_s.sendto(message, (dh_address, PORT))


    """will do replying server
    """
    def reply_server(self, path_address, source_node):
        global MESSAGE_TYPE, PORT

        message = str(MESSAGE_TYPE.SERVERACK)
        message = message + ' ' + str(self.HOST) + ' ' + str(source_node)
        # Send UDP datagram
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.settimeout(UPDATE_TIMEOUT)
        socket_s.sendto(message, (path_address, PORT))


    """will generate triggered message to server, including timestamp, SOURCE -> SERVER
    """
    def send_sensor_event(self, path_address, source_node, timestamp_string, timestamp_float, type):
        global MESSAGE_TYPE, PORT

        message = ''
        if (type == MESSAGE_TYPE.DATA_IN):
            message = str(MESSAGE_TYPE.DATA_IN)
            message = message + ' ' + str(self.HOST) + ' ' + str(source_node) + ' ' + timestamp_string + ' ' + str(timestamp_float)
        elif (type == MESSAGE_TYPE.DATA_OUT):
            message = str(MESSAGE_TYPE.DATA_OUT)
            message = message + ' ' + str(self.HOST) + ' ' + str(source_node) + ' ' + timestamp_string + ' ' + str(timestamp_float)
        # Send UDP datagram
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.settimeout(UPDATE_TIMEOUT)
        socket_s.sendto(message, (path_address, PORT))


    """will do replying the triggered message, SERVER -> DESTINATION
    """
    def reply_sensor_ack(self, path_address, destination_node, timestamp_float):
        global MESSAGE_TYPE, PORT

        message = str(MESSAGE_TYPE.DATAACK)
        message = message + ' ' + str(self.HOST) + ' ' + str(destination_node) + ' ' + str(timestamp_float)
        # Send UDP datagram
        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_s.settimeout(UPDATE_TIMEOUT)
        socket_s.sendto(message, (path_address, PORT))


    def event_call_back(self, channel):
        self.EVENT_DETECTED = 1


    """Core method of event monitor, will monitor the changes of the voltage on specific PINs, and
       send event data packets to the designated node
    """
    def handle_sensor_event(self, screen, start):
        global STATUS, PEER_STATUS, CONTROL, MESSAGE_TYPE, PRINTABLE

        time.sleep(1)
        while True:
            if (self.EVENT_DETECTED):  # waiting for event detection signal
                if GPIO.input(PIR_PIN):  # signal from 0 -> 1, node being triggered
                    time0t1 = datetime.datetime.now()
                    timestamp_string = str(time0t1.replace(microsecond = 0))
                    timestamp_string = re.sub(r' ', '@', timestamp_string)
                    timestamp_float = time.time()
                    node_color = "#" + str(STATUS.YELLOW) + "[" + str(self.HOST) + "]"
                    time_color = "#" + str(STATUS.YELLOW) + "[" + str(time0t1.replace(microsecond=0)) + "]"
                    string = "Object is within detection range of node " + node_color + " since " + time_color
                    self.print_screen(screen, CONTROL.UPDATE, string)

                    if (self.SERVER and self.SERVER != self.HOST):  # if local node knows the server, send triggered message with timestamp to server
                        for route_list in self.ROUTETable:  # find the routing path
                            if (route_list[-1] == self.SERVER):
                                path_node = int(route_list[1])
                                path_address = self.address_generator(path_node)
                                self.send_sensor_event(path_address, self.HOST, timestamp_string, timestamp_float, MESSAGE_TYPE.DATA_IN)
                                distance = len(route_list) - 1
                                tBlinkGreen = threading.Thread(target = self.blink_green, args = (distance, ))  # blink the Green LED
                                tBlinkGreen.start()
                                self.EVENT_DETECTED = 0
                                break

                    elif (self.SERVER == self.HOST):  # if local node is the server, send the message to laptop directly
                        message = str(MESSAGE_TYPE.DATA_IN) + ' ' + str(self.SERVER) + ' ' + str(self.SERVER) + ' ' + timestamp_string + ' ' + str(timestamp_float)
                        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        socket_s.settimeout(UPDATE_TIMEOUT)
                        socket_s.sendto(message, (self.LAPTOP_ADD, PORT))
                        tBlinkGreen = threading.Thread(target = self.blink_green, args = (1, ))  # blink the Green LED
                        tBlinkGreen.start()
                        self.EVENT_DETECTED = 0

                else:  # signal form 1 -> 0, object is leaving or keeping still
                    time1t0 = datetime.datetime.now()
                    timestamp_string = str(time1t0.replace(microsecond=0))
                    timestamp_string = re.sub(r' ', '@', timestamp_string)
                    timestamp_float = time.time()
                    node_color = "#" + str(STATUS.YELLOW) + "[" + str(self.HOST) + "]"
                    time_color = "#" + str(STATUS.YELLOW) + "[" + str(time1t0.replace(microsecond = 0)) + "]"
                    string = "Object stops moving or step out of the detection range of node " + node_color + " since " + time_color
                    self.print_screen(screen, CONTROL.UPDATE, string)

                    if (self.SERVER and self.SERVER != self.HOST):  # if local node knows the server, notify server that the object is no longer sensed
                        for route_list in self.ROUTETable:
                            if (route_list[-1] == self.SERVER):
                                path_node = int(route_list[1])
                                path_address = self.address_generator(path_node)
                                self.send_sensor_event(path_address, self.HOST, timestamp_string, timestamp_float, MESSAGE_TYPE.DATA_OUT)
                                distance = len(route_list) - 1
                                tBlinkGreen = threading.Thread(target = self.blink_green, args = (distance, ))  # blink the Green LED
                                tBlinkGreen.start()
                                self.EVENT_DETECTED = 0
                                break

                    elif (self.SERVER == self.HOST):  # if local node is the server
                        message = str(MESSAGE_TYPE.DATA_OUT) + ' ' + str(self.SERVER) + ' ' + str(self.SERVER) + ' ' + timestamp_string + ' ' + str(timestamp_float)
                        socket_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        socket_s.settimeout(UPDATE_TIMEOUT)
                        socket_s.sendto(message, (self.LAPTOP_ADD, PORT))
                        tBlinkGreen = threading.Thread(target = self.blink_green, args = (1, ))  # blink the Green LED
                        tBlinkGreen.start()
                        self.EVENT_DETECTED = 0
            # end of big if
            time.sleep(0.5)
        # end of big while


    """For gracefully terminate the threads
    """
    def terminate(self, thread):
        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
        if res == 0:
            raise ValueError("nonexistent thread id")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")


    """will blink blue LED in order to react to ACK of triggered message
    """
    def blink_blue(self):
        GPIO.output(BLUE_PIN, True)
        time.sleep(LED_DELAY)
        GPIO.output(BLUE_PIN, False)


    """will blink red LED in order to react to DH lost & packet lost (no ACK)
    """
    def blink_red(self):
        GPIO.output(RED_PIN, True)
        time.sleep(LED_DELAY)
        GPIO.output(RED_PIN, False)


    """will blink green LED in order to react to triggered message, the number of LED is based on distance
    """
    def blink_green(self, distance):
        for i in range(distance):
            GPIO.output(GREEN_PIN, True)
            time.sleep(LED_DELAY)
            GPIO.output(GREEN_PIN, False)
            time.sleep(LED_DELAY)


"""Read the STDIN, and make it at the bottom
"""
def stdin_to_command(screen, height, type, HOST):
    screen.move(height, 0)
    screen.clrtoeol()
    if (type == 0):  # provides two interface: before and after the protocol initialisation
        screen.addstr("[RMP Interface]> ")
    elif (type == 1):
        screen.addstr(height, 0, "[RMP node " + str(HOST) + "]# ")

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


if __name__ == '__main__':
    local = Router()
    local.init()
