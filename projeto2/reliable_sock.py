#!/usr/bin/python
# -*- coding: utf-8 -*-

from Queue import PriorityQueue as PQueue
from Queue import PriorityQueue
from packet import Packet
import binascii, random, threading

WINDOW_SIZE = 10 # packets
ACK_TIMEOUT = 30 # seconds TODO

class RSock:
	def __init__ (self, sock, addr):
		self.init = False
		self.end = False
		self.requesting = False
		self.sock = sock
		self.addr = addr

		# PQueue will sort packets by segnum, so when inserting in queue, packets will be like:
		# Acks - segnum = 0
		# Failed packets (for their segnum is securely < unset packets)
		# Unsent packets
		# So ordering is guaranteed and ACKs should be sent immediately
		self.buff = PQueue() # packets to send
		self.waiting = PQueue(WINDOW_SIZE) # packets wating for ACK TODO on timeout add to fail queue

		self.seg = 0 # current packet
		self.ack = 0 # window base point
		self.nextSeg = random.randint(1,1000) # next expected packet

		# self.lock = threading.Condition()

	def start(self):
		while not self.end:
			packet = self.buff.get(True) # block until another packet is added 
			# only regular packets should be recent. 
			# acks require the other side of the socket to be sent again, so we don't need to put on waiting queue
			if packet.ack == 0 and packet.con == 0:
				self.waiting.put(packet) # waiting queue will block when full: all packets are sent & wait for acking			
				print "Sending seg " + str(packet.seg) + " to " + str(self.addr) # don't log ack/con for they are logged somewhere else		
	
			wrap = packet.wrap()
			
			self.sock.sendto(wrap, self.addr)

			# inform Queue we're done with the element we got
			self.buff.task_done()

			# TODO end packets/end acks CAN FAIL TOO. Use timeout to set end = True when end packet is sent
			if packet.end:
				print "Ending connection to " + str(self.addr)
				self.end = True

	def enqueuePacket(self, data):
		packet = Packet(data)
		if self.init:
			packet.seg = self.seg
			self.seg += 1
		else:
			self.requesting = True
			packet.con = self.nextSeg # con packet: seg = 0; ack = 0; con = nextSeg

		self.buff.put(packet)

	def endPacket(self):
		packet = Packet('', self.seg, end=1)
		self.seg += 1
		self.buff.put(packet)

	def errPacket(self):
		packet = Packet('', self.seg, err=1)
		self.seg += 1
		self.buff.put(packet)
		
	def ackPacket(self, ack, endAck):
		self.buff.put(Packet('', 0, ack, endAck))

	def wake(self):
		try:
			self.lock.notify()
		except RuntimeError:
			pass # wasn't locked...
	
	def receivePacket(self, data):
		packet = Packet(data)
		packet.unwrap()

		if not packet.validChecksum(): # do not receive broken packets
			print "Bad checksum received on seg: " + str(packet.seg) + " ack: " + str(packet.ack)
			return None

		if packet.con > 0:		
			self.seg = packet.con # set seg with nextSeg received in con field
			self.ack = packet.con # intitialize ack with nextSeg
			self.init = True
			if not self.requesting: # this socket received the connection request, then ack it
				print "Connection request from " + str(self.addr)
				self.buff.put(Packet('', end = packet.end, con = self.nextSeg)) # ack with nextSeg expected on con field
				return packet
		elif (packet.ack > 0 and self.ack == packet.ack): # expected ack!
			self.ack += 1
			print "Received expected ack " + str(packet.ack) + " on connection " + str(self.addr)

			if not self.waiting.empty():
				waited = self.waiting.get(False) # don't block...
				if waited.seg != packet.ack:
					print "Removed wrong packet of waiting list. Expected seg: " + str(waited.seg) # TODO FOR DEBUG ONLY! REMOVE
			else: # TODO FOR DEBUG ONLY! REMOVE
				print "Failed removing acked packet from waiting list!!!"
		elif self.nextSeg < packet.seg:
			self.ackPacket(packet.seg, packet.end) # old packet received again, ACK might be lost.. send it again
			print "Duplicated packet... Sending ack again and ignoring"
		elif self.nextSeg == packet.seg: # expected seg!
			self.nextSeg += 1
			self.ackPacket(packet.seg, packet.end)
			print "Acking packet " + str(packet.seg)
			return packet
		else:
			print "Bad packet received! Seg: " + str(packet.seg) + " expected: " + str(self.nextSeg) + " ack: " + str(packet.ack)
		
		return None
