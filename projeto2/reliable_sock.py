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
		self.waiting = Queue() # packets wating for ACK TODO on timeout add to fail queue

		self.seg = random.randint(1,1000) # current packet
		self.ack = self.seg # window base point
		self.nextSeg = 0 # next expected packet

		self.lock = threading.Condition()

	def start(self):
		while not self.end:
			packet = self.nextPacket()

			if packet.seg > (self.ack + WINDOW_SIZE):
				self.lock.acquire()
				self.lock.wait() # block send for this packet is out of window			
				self.lock.release()

			waiting.put(packet) # add packet to waiting queue
			wrap = packet.wrap()
			
			print "Sending " + str(len(wrap)) + " bytes to " + str(self.addr)
			self.sock.sendto(wrap, self.addr)

			# TODO end packets/end acks CAN FAIL TOO. Use timeout to set end = True when end packet is sent
			if packet.end:
				print "Ending connection to " + str(self.addr)
				self.end = True

	def nextPacket(self):
		if not self.fail.empty():
			return self.fail.get(True) # not empty, so won't block...

		return self.buff.get(True) # block until another packet is added

	def enqueuePacket(self, data):
		seg = 0
		if self.init:
			self.seg += 1
			seg = self.seg

		self.addAndWake(Packet(data, seg, 0))

	def end(self):
		self.seg += 1
		self.addAndWake(Packet('', self.seg, 0, 1))
		
	def ackPacket(self, ack, endAck):
		self.addAndWake(Packet(data, 0, ack, endAck))

	def addAndWake(self, packet):
		self.buff.put(packet)
		self.wake()

	def wake(self)
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

		# ack of filename or other acks
		if (not self.init and packet.ack == 0) or (packet.ack > 0 and packet.ack == self.ack + 1): # expected ack!
			self.init = True
			self.ack += 1
			print "Received ack " + str(ackno) + " on connection " + str(self.addr)

			try:
				waited = self.waiting.get()
				if waited.seg != packet.ack:
					print "Removed wrong packet of waiting list. Ack: " + packet.ack + " Expected seg: " + waited.seg
			except Empty:
				print "Failed removing acked packet from waiting list!!!"

			self.wake()	
			return packet
		elif self.nextSeg < packet.seg:
			self.ackPacket(packet.seg, packet.end) # old packet received again, ACK might be lost.. send it again
		elif self.nextSeg == packet.seg: # expected seg!
			self.nextSeg += 1
			self.ackPacket(packet.seg, packet.end)
			return packet
		else:
			print "Bad packet received! Seg: " + packet.seg + " expected: " + self.nextSeg + " ack: " + packet.ack
		
		return None
