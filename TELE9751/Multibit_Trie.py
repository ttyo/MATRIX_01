#!/usr/bin/python
############################################################################
#
# Dynamic Multibit Trie for IP Lookup
# For: TELE9751 Switching Systems Architecture, UNSW
#
# A multibit-trie for IP lookup, simulates a typical routing table in real
# device, which contains entries based on received "routing entries", and
# updates itself when new incoming entries come in. It will take a .pcap
# file as an simulation for input, to calculate jitter based on lookup time
# of each entry.
#
#############################################################################

__author__ = "Chengjia Xu 5025306"
__license__ = "GPL"
__version__ = "0.9"
__email__ = ["chengjia.xu@student.unsw.edu.au"]

import re
import sys
import pprint
import dpkt
import socket
import threading
import time

class Node(object):
    def __init__(self, main_stride, branch_stride):
        self.main_s = main_stride
        self.branch_s = branch_stride
        self.default_route = None
        self.prefix = []
        self.output = {}
        self.swap = {}
        self.swap2 = {}

    def insert(self, pre, out, sub_out=None, flag=0):

        """
        if pre is None, or flag is not 1, initialise current node

        if incoming pre shorter than current prefix, just change output
        e.g. pre = '1101', p = '11011'

        if incoming pre longer than current prefix, create new node
        e.g. pre = '1101101', p = '11011', so new_pre = '01' is for new sub node
        """
        if (pre is None or flag) and len(self.prefix) == 0:
            if pre is None:
                self.default_route = out
            for i in xrange(2**self.main_s):  # initialise root/sub node
                binary = "{0:b}".format(i)
                while len(binary) is not self.main_s:
                    binary = '0' + binary
                self.prefix.append(binary)
                self.output[binary] = out

        if pre is not None and len(pre) <= self.main_s:
            for p in self.prefix:
                if p.find(pre, 0, len(pre)) == 0:
                    if not flag:
                        self.output[p] = out
                    else:
                        self.output[p] = sub_out

        elif pre is not None and len(pre) > self.main_s:
            for p in self.prefix:
                if pre.find(p, 0, len(p)) == 0:
                    if p not in self.swap:
                        self.swap[p] = self.output[p]  # store original output
                    if type(self.output[p]) is not Node:
                        self.output[p] = Node(self.branch_s, self.branch_s)  # sub-node's stride is 2,2
                    regex = r'^' + re.escape(p)
                    new_pre = re.sub(regex, '', pre)
                    if not flag:
                        self.output[p].insert(new_pre, self.swap[p], sub_out=out, flag=1)
                    else:
                        self.output[p].insert(new_pre, self.swap[p], sub_out=sub_out, flag=1)
                    break

    def search_output(self, dst, default_output):
        for p in self.prefix:
            if len(dst) <= self.main_s:
                if p.find(dst, 0, len(dst)) == 0:
                    return self.output[p]
            else:
                if dst.find(p, 0, len(p)) == 0:
                    if type(self.output[p]) is Node:
                        regex = r'^' + re.escape(p)
                        new_pre = re.sub(regex, '', dst)
                        return self.output[p].search_output(new_pre, default_output)
                    else:
                        return self.output[p]

    def update_trie(self, sleep=2):
        prefix_l, output_l, default_output = handle_file('update_input.txt')

        for i,pre in enumerate(prefix_l):
            time.sleep(sleep)
            start_time = time.clock()  # record the start time for calculating jitter
            out = output_l[i]
            self.update_node(pre, out)
            time_cost = format(time.clock() - start_time, '.6f')
            if sleep == 2:
                print "\n###################################"
            print "# %-19s %-9s#" % ('[TIME OF ENTRY UPDATE]', time_cost)
            if pre is None:
                print "# [Updated Prefix] %-15s#" % ('__all')
            else:
                print "# [Updated Prefix] %-15s#" % (pre)
            print "# [New output] %-15s    #" % (out)
            if sleep == 2:
                print "###################################"
                print "%-19s %-40s %-15s %-13s %-10s" % ('DESTINATION IP', 'IP IN BINARY', 'OUTPUT PORT', 'LOOKUP TIME', 'Delta TIME')

    def update_node(self, pre, out):
        for p in self.prefix:
            if pre is None:                        # case 0: a new default route
                self.update_default(self.default_route, out)
                self.default_route = out
            elif len(pre) <= self.main_s:
                if p.find(pre, 0, len(pre)) == 0:  # case 1: pre is in p (len(pre) <= stride)
                    self.output[p] = out
            else:
                if pre.find(p, 0, len(p)) == 0:    # case 2: p is in pre
                    regex = r'^' + re.escape(p)
                    new_pre = re.sub(regex, '', pre)
                    if type(self.output[p]) is Node:  # sub case 1: if a node, keep search in it
                        self.output[p].update_node(new_pre, out)
                    else:                             # sub case 2: if a port, then create new node, equals to insert(pre, out) to current address
                        if p not in self.swap2:
                            self.swap2[p] = self.output[p]  # store original output
                        self.output[p] = Node(self.branch_s, self.branch_s)  # sub-node's stride is 2,2
                        self.output[p].insert(new_pre, self.swap2[p], sub_out=out, flag=1)

    def update_default(self, default, new_default):
        for p in self.prefix:
            if self.output[p] == default:
                self.output[p] = new_default
            elif type(self.output[p]) is Node:
                self.output[p].update_default(default, new_default)

    def print_trie(self):
        pprint.pprint(self.output)
        print
        for p in self.output:
            if type(self.output[p]) is Node:
                self.output[p].print_trie()


"""
Processing sample routing table file

input file 'prefix_input.txt' contains semi-routing table entries, contains IP prefixes and masks, along with
output ports. An entry looks like this: 10000000.11000000.00000000.00000000 11111111.11000000.00000000.00000000 p14,
representing '128.192.0.0/10' or '128.192.0.0 255.192.0.0', and it should be routed via port 'p14'
"""
def handle_file(path, sort=False):
    F = open(path, 'r')
    database_content = F.readlines()
    F.close()

    database = {}
    default_output = None
    prefix_l = []
    output_l = []
    for i,line in enumerate(database_content):
        line = line.split()[0:3]
        database_content[i] = line
    for ip_mask in database_content:
        ip = re.sub(r'\.', '', ip_mask[0])
        mask = re.sub(r'\.', '', ip_mask[1])
        port = ip_mask[2]
        ip_prefix = ip[0:len(re.findall(r'1', mask))]
        if len(ip_prefix) == 0:
            ip_prefix = '__all'
        database[ip_prefix] = port

    if sort:
        for k in sorted(database, key=len):
            if k == '__all':
                default_output = database[k]
                continue
            prefix_l.append(k)
            output_l.append(database[k])
        prefix_l.insert(0, None)
        output_l.insert(0, default_output)
    else:
        for k in database:
            if k == '__all':
                default_output = database[k]
                continue
            prefix_l.append(k)
            output_l.append(database[k])
        if default_output is not None:
            prefix_l.insert(0, None)
            output_l.insert(0, default_output)

    return prefix_l, output_l, default_output


def main():
    debug_mod = False
    if len(sys.argv) == 3 or len(sys.argv) == 4:
        if len(sys.argv) == 4:
            debug_mod = True
        try:
            main_s = int(sys.argv[1])
            sub_s = int(sys.argv[2])
        except:
            print "\nThe script takes exactly two integer parameters, or with a third optional 'test' keyword for test mod:"
            print "python Multibit_Trie.py [main stride] [sub stride] [test]"
            exit()
    else:
        print "\nThe script takes exactly two integer parameters, or with an optional 'test' keyword for test mod:"
        print "python Multibit_Trie.py [main stride] [sub stride] [test]"
        exit()


    # Processing sample routing entries
    #
    # this part converts the content of the files into the form of prefix, based on the length of mask. For example, entry
    # '10000000.11000000.00000000.00000000 11111111.11000000.00000000.00000000 p14' will be converted into dictionary
    # type: '1000000011':'p14'. Then they are split into two lists (one for prefix, one for port) for further processing
    prefix_l, output_l, default_output = handle_file('./prefix_input.txt', sort=True)

    # Construct the trie based on routing entries
    #
    # Class 'Node' provides two parameters: main stride and sub stride. A multibit trie will be created based on provided
    # parameters. In the test, trie in stride 4, 2 is used for test
    trie = Node(main_s, sub_s)
    for i,pre in enumerate(prefix_l):
        out = output_l[i]
        trie.insert(pre, out)

    # Handling pcap file
    #
    # pcap file is the capture result of wireshark. The file will be parsed for reading the destination address of
    # packets in the file, to simulate the input of IP packets
    if not debug_mod:
        thread_update_trie = threading.Thread(target=trie.update_trie)
        thread_update_trie.start()

        pcapfile = './lookup.pcap'
        ip_counter = 0
        total_time = 0.0
        total_jitter = 0.0
        last_time = 0.0
        first = True
        print "\n%-19s %-40s %-15s %-13s %-10s" % ('DESTINATION IP', 'IP IN BINARY', 'OUTPUT PORT', 'LOOKUP TIME', 'Delta TIME')
        for ts,pkt in dpkt.pcap.Reader(open(pcapfile, 'r')):
            time.sleep(0.033)
            if ip_counter == 800:
                break
            eth = dpkt.ethernet.Ethernet(pkt)
            if eth.type != dpkt.ethernet.ETH_TYPE_IP:
               continue

            dst_ip = socket.inet_ntoa(eth.data.dst)
            dst_bin = ''.join(bin(int(x) + 256)[3:] for x in dst_ip.split('.'))
            dst_bin_dot = '.'.join(re.findall('........', dst_bin))

            ip_counter += 1
            start_time = time.clock()
            output = trie.search_output(dst_bin, default_output)
            time_cost = format(time.clock() - start_time, '.6f')
            total_time += float(time_cost)
            if first:
                jitter = '0.000000'
                first = False
            else:
                jitter = format(abs(float(time_cost) - last_time), '.6f')
            total_jitter += abs(float(time_cost) - last_time)
            last_time = float(time_cost)
            print "%-19s %-40s %-15s %-13s %-10s" % (dst_ip, dst_bin_dot, output, time_cost, jitter)

        print "\nJitter Level:    Acceptability:\n\
   <   1 ms      Excellent\n\
   <   5 ms      Extremely Good\n\
   <  20 ms      Very Good\n\
   <  50 ms      Good\n\
   <  80 ms      Good to Fair\n\
   < 100 ms      Fair"
        print "\nAverage Jitter Result:"
        print format(total_jitter / ip_counter, '.10f')
        print "\nAverage Lookup Time:"
        print format(total_time / ip_counter, '.10f')

    elif debug_mod:
        print "\n###################################################"
        print "#                     TEST MOD                    #"
        print "###################################################\n"

        # print the trie structure
        print "################# Trie Structure ##################"
        trie.print_trie()
        print
        print "Entering test mod, please input valid IP address manually to verify the output."
        print "type 'exit' to quit, 'update' to do route update manually, for comparing with old & new tries:\n"
        while 1:
            ip_right = True
            dst_ip = raw_input('Enter an valid IP address> ')
            ip_part = dst_ip.split('.')
            if dst_ip == 'exit':
                break
            if dst_ip == 'update':
                print
                trie.update_trie(sleep=0.2)
                print "############### New Trie Structure ################"
                trie.print_trie()
                print "############### New Trie Structure ################\n"
                ip_right = False
            elif len(dst_ip) == 0:
                ip_right = False
            elif len(ip_part) != 4:
                print '\nInvalid IP address\n'
                ip_right = False
            else:
                for digit in ip_part:
                    if int(digit) > 255:
                        print '\nInvalid IP address\n'
                        ip_right = False

            if ip_right:
                dst_bin = ''.join(bin(int(x) + 256)[3:] for x in dst_ip.split('.'))
                dst_bin_dot = '.'.join(re.findall('........', dst_bin))
                start_time = time.clock()
                output = trie.search_output(dst_bin, default_output)
                time_cost = format(time.clock() - start_time, '.6f')
                print "\n%-19s %-40s %-15s %-13s" % ('DESTINATION IP', 'IP IN BINARY', 'OUTPUT PORT', 'LOOKUP TIME')
                print "%-19s %-40s %-15s %-13s\n" % (dst_ip, dst_bin_dot, output, time_cost)


if __name__ == '__main__':
    main()
