import random
import sys
import math
from network import Node as NODE
from network import Network as NETWORK
from network import Link as LINK
from network import Packet as PACKET


##########################################################
# Router
# Three tables (dictionary) are maintained:
#
# neighbors (the neighbor table):
#   {link1:(timestamp1, source address1, cost1), link2:(timestamp2, source address2, cost2), ...}
#
# routes (the routing table):
#   {address1:link1, adress2:link2, address3:link3, ...}
#
# spcost
#
##########################################################
class Router(NODE):
    HELLO_INTERVAL = 10
    ADVERT_INTERVAL = 50

    def __init__(self, location, address=None):
        NODE.__init__(self, location, address = address)
        self.neighbours = {}
        self.routes = {}
        self.spcost = {}
        self.routes[self.address] = 'self'
        self.spcost[self.address] = 0

    def reset(self):
        NODE.reset(self)
        self.spcost[self.address] = 0

    # get the link according to a given neighbor (address)
    def get_link(self, neighbor):
        if (self.address == neighbor):
            return None
        for link in self.links: # return the link with any side is the given "neighbor"
            if (link.node2.address == neighbor or link.node1.address == neighbor):
                return link
        return None

    # get the opposite side of the link
    # if local node is node1, then return node2's address
    # if local node is node2, then return node1's address
    def get_peer(self, link):
        if (link.node1.address == self.address):
            return link.node2.address
        if (link.node2.address == self.address):
            return link.node1.address

    # routing table (dictionary "routes") stores links, will be used to match packet
    # once the links is found, use Link.send(node, packet) to forward packet
    def forward(self, packet):
        link = self.routes.get(packet, destination, None)
        if (link is None):
            print ('No route for ', packet, 'at node ', self)
        else:
            link.send(self, packet)

    # if local node receives a "HELLO" packet, add the tuple (time, source, cost) into dictionary neighbor table "neighbours"
    # if local node receives a "ADVERT" packet, pass the packet to method Router.process_advertisement()
    # else, pass the packet to method Node.process
    def process(self, packet, link, time):
        if (packet.type == 'HELLO'):
            self.neighbours[link] = (time, packet.source, link.cost)
        elif (packet.type == 'ADVERT'):
            self.process_advertisement(packet, link, time)
        else:
            NODE.process(self, packet, link, time)

    # OVERRIDE
    def process_advertisement(self, packet, link, time):
        return

    # 1. loop link in all Node.links (Router is extended from Node)
    # 2. creating new packet with "HELLO" via method network.new_packet() (network.py is imported))
    # 3. sending the packet via method Link.send(packet)
    def send_hello(self, time):
        for link in self.links:
            packet = self.NETWORK.new_packet(self.address, self.peer(link), 'HELLO', time, color = 'green')
            link.send(self, packet)
        return

    # 1. loop link in neighbor table's keys (which is dictionary "neighbors"'s keys)
    # 2. if the value (time, source, cost) of the key's (link) timestamp is smaller than the old time, which means the link is expired
    # 3. if the link is expired, remove the entry from dictionary "neighbors" (key - value)
    # 4. then pass the expired link to Router.link_failed(link)
    def clear_hello(self, time):
        old = time - 2 * self.HELLO_INTERVAL
        for link in self.neighbours.keys():
            if (self.neighbours[link][0] <= old):
                del self.neighbors[link]
                self.link_failed(link)

    # OVERRIDE
    def link_failed(self, link):
        return

    # clean the route related to a specific link
    # if the routing table's value (link) of a specific key (destination) is equal to that link, add the destination to a temp list
    # then delete the key - value entries from dictionary "routes" and "spcost" based on the temp list
    def clear_route(self, link):
        clear_list = []
        for destination in self.routes:
            if (self.routes[dest] == link):
                clear_list.append(destination)
        for destination in clear_list:
            print (self.address, ' clearing route to ', destination)
            del self.routes[destination]
            del self.spcost[destination]

    # router will send HELLO / ADVERT based on fixed intervals
    # router will clear hello based on HELLO interval
    def transmit(self, time):
        if ((time % self.HELLO_INTERVAL) == 0):
            self.send_hello(time)
            self.clear_hello(time)
        if ((time % self.ADVERT_INTERVAL) == 0):
            self.send_advertisement(time)
        return

#class Router_Cost(NETWORK):
#    def __init__(self, simtime, nodes, links):
#        NETWORK.__init__(self, simtime)
#        for n, r, c in nodes:
#            self.add_node(r, c, address = n)
#        for a1, a2 in links:
#            node1 = self.addresses[a1]
#            node2 = self.addresses[a2]
#            self.add_link(node1.location[0], node1.locaton[1], node2.location[0], node2.location[1])

