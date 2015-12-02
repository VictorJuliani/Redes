#!/usr/bin/python
# -*- coding: utf-8 -*-

import random, sys

class Connection:
	def __init__ (self, filename, addr):
		self.addr = addr
		self.fp = open(filename, 'r')
	  	self.data = fp.read()
	  	self.seg = random.randint(1,1000)
	  	self.ack = 0

		# how many chunks
	  	self.size = int(ceil(len(text)/PACKET_SIZE))

	def notifyAck(self, ackpkt):
		ackno = int(ackpkt.split(' ')[1])

	  	if (ackno not in self.acks) # save ack received
	  		acks.append(ackno)

	  	# ACKs may come out of order, so check if next ack is in list of received acks
	  	# if it is, increase ack and remove from list
	  	# else, wait for it
	  	bool hasAck = true
	  	while hasAck && len(acks) > 0:
	  		if ((ack + 1) in acks):
		  		acks.remove(ack + 1);
	  			ack += 1
	  		else
	  			hasAck = false
