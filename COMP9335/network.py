import random
import math
import time


##########################################################
# Node:
#
# Node.get_address()
# Node.add_link(link)
# Node.add_packet(packet)
# Node.reset()
#
# Node.collect_packet()
# Node.process_packet(time)
#
# Node.receive(packet)
# Node.transmit(time)
# Node.forward(packet)
# Node.process(packet, link, time)
#
# Process:
# 1. packet arrives
#       -> <none>
# 2. put into list "packets", waiting for processing
#       -> collect_packet()
# 3. if destination is local node, put into list "receive_queue"
#       -> process_packet() -> process() -> receive()
# 3. if destination is remote node, using Link.send() to send the packet
#       -> process_packet() -> process() -> forward()
# 4. after that, check list "transmit_queue" for local generated packets
#       -> process_packet() -> transmit()
#
##########################################################
class Node:
    def __init__(self, location, address = None):
        self.location = location # location is a tuple, for example: (x, y)
        self.links = []          # links that connect to this node
        self.packets = []        # packets to be processed
        self.transmit_queue = [] # store the packets that to be transmitted from this node
        self.receive_queue = []  # store the packets that received by this node
        self.properties = {}
        self.network = None
        if (address is None):
            self.address = location
        else:
            self.address = address

    def __repr__(self):
        return ('Node <%s>' % str(self.address))

    # reset a node's state
    def reset(self):
        for l in self.links:
            l.reset_node()
        self.transmit_queue = []
        self.receive_queue = []
        self.queue_length_sum = 0
        self.queue_length_max = 0
        self.properties.clear()

    def get_address(self):
        return self.address

    # store the links that connect to this node
    def add_link(self, link):
        self.links.append(link)

    # add a packet to node's transmit_queue
    def add_packet(self, packet):
        index = 0
        for packet_q in self.transmit_queue:
            if (packet.start < packet_q.start):
                self.transmit_queue.insert(index, packet)
            else:
                index += 1
        else:
            self.transmit_queue.append(packet) # if the queue is empty

    # node collects packets from all links, and puts packets into list "packets"
    def collect_packet(self):
        collected = []
        for link in self.links:
            collected.append(link.receive_packet(self))
        self.packets = collected

    # node processes the collected packets from list "packets"
    # and pass them to method Node.process(packet, link, time)
    def process_packet(self, time):
        for packet in self.packets:
            if (packet is not None):
                self.process(packet[1], packet[0], time)
        self.packets = []
        self.transmit(time)
        pending = 0
        for link in self.links:
            pending += link.queue_length(self)
        self.queue_length_sum += pending
        self.queue_length_max = max(self.queue_length_max, pending)
        value = pending + len(self.transmit_queue)
        return value

    # node processes the packets
    # if it is an incoming packet, using method Node.receive(packet, link), putting the packet into receive_queue
    # if it is an outgoing packet, using method Node.forward(packet) to send it
    # being called in method "process_packet(time)"
    def process(self, packet, link, time):
        if (packet.destination == self.address):
            packet.finish = time
            self.receive(packet, link)
        else:
            packet.add_hop(self, time)
            self.forward(packet)

    # node transmits the packets in transmit_queue
    # being called in method "process_packet(time)"
    def transmit(self, time):
        while (len(self.transmit_queue) > 0):
            if (self.transmit_queue[0].start <= time):
                self.process(self.transmit_queue.pop(0), None, time)
            else:
                break

    # node puts the packets into receive_queue
    # being called in method "process(packet, link, time)"
    def receive(self, packet, link):
        self.receive_queue.append(packet)

    # OVERRIDE
    # Default Behavior:
    # node picks a random link and uses Link.send(packet) to forward a packet
    # being called in method "process(packet, link, time)"
    def forward(self, packet):
        link = random.choice(self.links)
        link.send(self, packet)


##########################################################
# Link:
#
# Link.queue_length(node)
# Link.reset()
#
# Link.receive_packet(node)
# Link.send_packet(node, packet)
#
##########################################################
class Link:
    def __init__(self, node1, node2):
        self.node1 = node1  # first node of a link
        self.node2 = node2  # second node of a link
        self.queue_1_2 = [] # packets to be transmitted from node1 to node2
        self.queue_2_1 = [] # packets to be transmitted from node2 to node1
        self.cost = 1       # default cost is 1
        self.network = None
        node1.add_link(self)
        node2.add_link(self)
        self.broken = False

    def __repr__(self):
        self.queue_1_2 = []
        self.queue_2_1 = []

    # return the length of queue_1_2 or queue_2_1 (the undelivered packets)
    def queue_length(self, node):
        if (node == self.node1):
            return len(self.queue_1_2)
        elif (node == self.node2):
            return len(self.queue_2_1)
        else:
            raise Exception, 'wrong in Link.queue_length'

    # reset the link state
    def reset(self):
        self.queue_1_2 = []
        self.queue_2_1 = []

    # return the queued packet to node1 or node2
    def receive_packet(self, node):
        if (node == self.node1):
            if (len(self.queue_2_1) > 0):
                return (self, self.queue_2_1.pop(0))
        elif (node == self.node2):
            if (len(self.queue_1_2)):
                return (self, self.queue_1_2.pop(0))
        else:
            raise Exception, 'wrong in Link.receive_packet'

    # put packets to queue_1_2 or queue_2_1 based on node
    def send_packet(self, node, packet):
        if self.broken:
            return
        if (node == self.node1):
            self.queue_1_2.append(packet)
        elif (node == self.node2):
            self.queue_2_1.append(packet)
        else:
            raise Exception, 'wrong in Link.send_packet'


##########################################################
# Packet:
#
# Packet.add_hop(node, time)
#
##########################################################
class Packet:
    def __init__(self, source, destination, type, start, **props):
        self.source = source           # address of the source node where the packet originate from
        self.destination = destination # address of the destination node where the packet should arrive to
        self.type = type
        self.start = start             # the time when the packet was transmitted
        self.finish = None             # the time when the packet was received
        self.network = None
        self.route = []                # list of the nodes in the path (an path entry of the packet)
        self.properties = props.copy()

    def __repr__(self):
        return ('Packet <from %s to %s> | type %s' % (self.source, self.destination, self.type))

    # add the passed node into the route
    def add_hop(self, node, time):
        self.route.append((node, time))


##########################################################
# Network:
#
# Network.new_node(location, address = None)
# Network.set_nodes(number)
# Network.find_node(x, y)
# Network.add_node(x, y, address = None)
# Network.map_node(f, default = 0)
#
# Network.new_link(node1, node2)
# Network.add_link(x1, y1, x2, y2)
#
# Network.new_packet(source, destination, type, start, **properties)
# Network.copy_packet(packet)
#
# Network.get_distance(node1, node2)
# Network.step(count = 1)
#
# dictionary "nodes_d" store the sub-dictionaries based on key (axis x):
# { x1:{y1:node1, y2:node2, y3:node3}, x2:{y1:node4}, x3:{y1:node5, y2:node6}, ...}
#
##########################################################
class Network:
    def __init__(self, x, y, time):
        self.nodes_d = {}   # a dictionary stores nodes based on axis x & y
        self.addresses = {} # {address1:node1, address2:node2, address3:node3 ...}
        self.nodes = []
        self.links = []     # store the links of network, once a link is created, it will be added to this list
        self.time = 0
        self.pending = 0
        self.packets = []   # store the packets of network
        self.packet_number = 0
        self.node_number = 0
        self.simtime = time
        self.playstep = 1.0
        self.max_x = x
        self.max_y = y

    def reset(self):
        for node in self.nodes:
            node.reset()
        self.time = 0
        self.pending = 0
        self.packets = []
        self.packet_number = 0
        self.pending = 1        # ensure at least one step

    def new_node(self, location, address = None):
        return Node(location, address = address)

    def set_nodes(self, number):
        self.node_number = number

    # locate a node with axis x and y
    def find_node(self, x, y):
        y_nodes_d = self.nodes_d.get(x, None) # get sub-dictionary of nodes under axis (key) x from dictionary "nodes_d"
        if (y_nodes_d is not None):
            return y_nodes_d.get(y, None) # get the node under axis (key) y from the sub-dictionary
        return None

    # add a node to network
    # dict.get(key, default=None), the "default" is the value to be returned in case key does not exist
    def add_node(self, x, y, address = None):
        node = self.find_node(x, y)
        if (node is None):
            node = self.new_node((x, y), address = address) # if there is no such a node, then create a new one
            node.network = self
            if (address is not None):
                self.addresses[address] = node # if new node's address is not empty, add to dictionary "addresses"
            self.nodes.append(node) # append the new node into list "nodes"
            y_nodes_d = self.nodes_d.get(x, {}) # get sub-dictionary of nodes under axis (key) x from dictionary "nodes_d"
            y_nodes_d[y] = node # put the new node's entry into the sub-dictionary based on axis y
            self.nodes_d[x] = y_nodes_d # put the changed sub-dictionary of nodes under axis x into dictionary again
            self.max_x = max(self.max_x, x) # calculate the network size
            self.max_y = max(self.max_y, y)
        return node

    # get all nodes from the whole network from top->bottom, left-to-right
    # return the list of all nodes in this sequence
    def map_node(self, f, default = 0):
        result = []
        for row in xrange(self.max_y + 1):
            for column in xrange(self.max_x + 1):
                node = self.find_node(row, column)
                if (node):
                    result.append(default) # if the node exists, put into list "result"
        return result

    def new_link(self, node1, node2):
        return Link(node1, node2)

    # add a link between two nodes with given axis x1, y1 and x2, y2
    # find the two nodes firstly based on axises
    # then set up new link
    def add_link(self, x1, y1, x2, y2):
        node1 = self.find_node(x1, y1)
        node2 = self.find_node(x2, y2)
        if (node1 is not None and node2 is not None):
            link = self.new_link(node1, node2)
            link.network = self
            self.links.append(link) # store the new link into list "links"

    # create new packet based on given information
    def new_packet(self, source, destination, type, start, **properties):
        packet = Packet(source, destination, type, start, **properties)
        packet.network = self
        self.packets.append(packet)
        self.packet_number += 1
        return packet

    # create (copy) new packet based on an old packet's information
    def copy_packet(self, packet):
        new_packet = self.new_packet(packet.source, packet.destination, packet.type, self.time, **packet.properties)
        return new_packet

    # calculate distance between two nodes based on their axises (the tuple "location" in Node class)
    def get_distance(self, node1, node2):
        x = node1[0] - node2[0]
        y = node1[1] - node2[1]
        distance = abs(x) + abs(y)
        return distance

    # make the network one step at a time
    # each node processes one packet from each of its incoming links
    def step(self, count = 1):
        stop_time = self.time + count
        while (self.time < stop_time and self.pending > 0):
            for node in self.nodes:
                node.collect_packet()
            self.pending = 0

            for node in self.nodes:
                self.pending += node.process_packet(self, time)
            self.time += 1
        return self.pending


##########################################################
# Link with cost
##########################################################
class Cost_Link(Link):
    def __init(self, node1, node2):
        Link.__init__(self, node1, node2)
        self.nsize = 0
        location1 = node1.location
        location2 = node2.location
        distance_x = (location1[0] - location2[0]) * (location1[0] - location2[0])
        distance_y = (location1[1] - location2[1]) * (location1[1] - location2[1])
        self.cost = math.sqrt(distance_x + distance_y)
        if (int(self.cost) == self.cost):
            self.costrepr = str(self.cost)
        else:
            self.costrepr = "sqrt(" + str(distance_x + distance_y) + ")"
