import random
import sys
import math
from network import Node as NODE
from network import Network as NETWORK
from network import Link as LINK
from network import Packet as PACKET
from router import Router as ROUTER

class DV_Node(ROUTER):
    INFINITY = 16 # all hail RIP

    def send_advertisement(self, time):
        advert = self.new_advertisement()
        for link in self.links:
            packet = self.NETWORK.new_packet(self.address, self.get_peer(link), 'ADVERT', time, color = 'red', ad = adv)
            link.send_packet(self, packet)

    def make_dv_advertisement(self):

        return

    def link_failed(self, link):

        return

    def integrate(self, from_node, adv):

        pass

    def process_advertisement(self, packet, link, time):
        self.integrate(packet.source, packet.properties['ad'])