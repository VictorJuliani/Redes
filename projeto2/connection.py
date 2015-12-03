#!/usr/bin/python
# -*- coding: utf-8 -*-

import random, sys, math

PACKET_SIZE = 800.0 # bytes

class Connection:
	def __init__ (self, filename, addr):
		print "New connection from " + str(addr) + " requesting " + filename
		fp = open(filename, 'r')
		self.data = fp.read()
		self.addr = addr
		self.seg = random.randint(1,1000)
		self.ack = self.seg
		self.cursor = 0 # cursor to interate over file section
		self.acks = [] # array to store out of order received acks

		# how many chunks
		self.size = int(math.ceil(len(self.data)/PACKET_SIZE))
		self.lastAck = self.ack + self.size # last ack expected before end

	def notifyAck(self, ackpkt):
		ackno = int(ackpkt.split(' ')[1])
		print "Received ack " + str(ackno) + " on connection " + str(self.addr)

		if (ackno not in self.acks): # save ack received
			self.acks.append(ackno)

		# ACKs may come out of order, so check if next ack is in list of received acks
		# if it is, increase ack and remove from list
		# else, wait for it
		hasAck = True
		while (hasAck and len(self.acks) > 0):
			if ((self.ack + 1) in self.acks):
				self.acks.remove(self.ack + 1)
				self.ack += 1
				self.cursor += 1
			else:
				hasAck = False
