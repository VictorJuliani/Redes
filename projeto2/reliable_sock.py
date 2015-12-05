#!/usr/bin/python
# -*- coding: utf-8 -*-

from Queue import Queue
from packet import Packet
import binascii, random, threading

WINDOW_SIZE = 10 # packets
ACK_TIMEOUT = 30 # seconds TODO

class RSock:
	def __init__ (self, sock, addr):
		self.init = False
		self.end = False
		self.sock = sock
		self.addr = addr
		self.buff = Queue() # packets to send
		self.fail = Queue() # packets timed out to resend
		self.waiting = Queue(WINDOW_SIZE) # packets wating for ACK TODO on timeout add to fail queue

		self.seg = 0 # current packet
		self.ack = 0 # window base point
		self.nextSeg = random.randint(1,1000) # next expected packet

		self.lock = threading.Condition()

	def start(self):
		while not self.end:
			packet = self.nextPacket()
			waiting.put(packet) # add packet to waiting queue. it will block if waiting queue is full: all packets are sent & wait for acking
			wrap = packet.wrap()
			
			print "Sending " + str(len(wrap)) + " bytes to " + str(self.addr)
			self.sock.sendto(wrap, self.addr)

			# TODO end packets/end acks CAN FAIL TOO. Use timeout to set end = True when end packet is sent
			if packet.end:
				print "Ending connection to " + str(self.addr)
				self.end = True

	def nextPacket(self):
		if not self.fail.empty():
			return self.fail.get(False) # not empty, so won't block...

		return self.buff.get(True) # block until another packet is added

	def enqueuePacket(self, data):
		packet = Packet(data)
		if self.init:
			packet.seg = self.seg
			self.seg += 1
		else:
			packet.ack = self.nextSeg # con packet: seg = 0; ack = nextSeg

		self.addAndWake(packet)

	def end(self):
		packet = Packet('', self.seg, 0, 1)
		self.seg += 1
		self.addAndWake(packet)

	def err(self):
		packet = Packet('', self.seg, 0, 0, 1)
		self.seg += 1
		self.addAndWake(packet)
		
	def ackPacket(self, ack, endAck):
		self.addAndWake(Packet('', 0, ack, endAck))

	def addAndWake(self, packet):
		self.buff.put(packet)
		# self.wake()

	def wake(self):
		try:
			self.lock.notify()
		except RuntimeError:
			pass # wasn't locked...
	
	def receivePacket(self, data):
		packet = Packet(data)
		packet.unwrap()

		if not packet.validChecksum(): # do not receive broken packets
			print "Bad checksum received on seg: " + packet.seg + " ack: " + packet.ack
			return None

		if not self.init:
			self.init = True
			if packet.seg == 0: # con request
				print "Connection request from " : + str(self.addr)
				self.seg = packet.ack # set seg with nextSeg received in ack field
				self.ack = packet.ack # intitialize ack with nextSeg
				self.addAndWake(Packet('', self.nextSeg, 0, packet.end)) # ack with nextSeg expected on seg field
			else: # con ack
				self.seg = packet.seg # set seg with nextSeg of client
				self.ack = packet.seg # intitialize ack with nextSeg
		elif (packet.ack > 0 and self.ack == packet.ack): # expected ack!
			self.ack += 1
			print "Received ack " + str(ackno) + " on connection " + str(self.addr)

			if not waiting.empty():
				waited = self.waiting.get(False) # don't block...
				if waited.seg != packet.ack:
					print "Removed wrong packet of waiting list. Ack: " + packet.ack + " Expected seg: " + waited.seg # TODO FOR DEBUG ONLY! REMOVE
			else: # TODO FOR DEBUG ONLY! REMOVE
				print "Failed removing acked packet from waiting list!!!"
		elif self.nextSeg < packet.seg:
			self.ackPacket(packet.seg, packet.end) # old packet received again, ACK might be lost.. send it again
		elif self.nextSeg == packet.seg: # expected seg!
			self.nextSeg += 1
			self.ackPacket(packet.seg, packet.end)
			return packet
		else:
			print "Bad packet received! Seg: " + packet.seg + " expected: " + self.nextSeg + " ack: " + packet.ack
		
		return None
