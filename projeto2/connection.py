#!/usr/bin/python
# -*- coding: utf-8 -*-

import random, sys, math

PACKET_SIZE = 10.0 # bytes

class Connection:
	def __init__ (self, filename, sock):
		print "New connection from " + str(sock.addr) + " requesting " + filename
		fp = open(filename, 'r')
		self.data = fp.read()
		self.sock = sock
		self.size = int(math.ceil(len(self.data)/PACKET_SIZE)) # how many chunks

		for i in range(size):
			start = int(i * PACKET_SIZE)
			end = int((i+1) * PACKET_SIZE)
			sock.enqueuePacket(self.data[start:end])

		sock.end()