#!/usr/bin/python
# -*- coding: utf-8 -*-

from Queue import PriorityQueue as PQueue
from Queue import PriorityQueue
from packet import Packet
import binascii, random, threading

WINDOW_SIZE = 10 # packets
ACK_TIMEOUT = 30 # seconds
END_ATTEMPTS = 3 # how many times should we try ending con until force closing?

class RSock:
	def __init__ (self, sock, addr, ploss, pcorr):
		self.init = False
		self.end = False
		self.requesting = False
		self.sock = sock
		self.addr = addr
		self.ploss = ploss
		self.pcorr = pcorr

		self.endAttempt = 0
		self.timer = None

		# PQueue will sort packets by segnum, so when inserting in queue, packets will be like:
		# Acks - segnum = 0
		# Failed packets (for their segnum is securely < unset packets)
		# Unsent packets
		# So ordering is guaranteed and ACKs should be sent immediately
		self.buff = PQueue() # packets to send
		self.waiting = PQueue(WINDOW_SIZE) # packets wating for ACK

		self.seg = 0 # current packet
		self.ack = 0 # window base point
		self.nextSeg = random.randint(1,1000) # next expected packet

	def start(self):
		while not self.end:
			packet = self.buff.get(True) # block until another packet is added 
			# only regular packets should be recent. 
			# acks require the other side of the socket to be sent again, so we don't need to put on waiting queue
			if packet.ack == 0 and packet.con == 0:
				self.waiting.put(packet) # waiting queue will block when full: all packets are sent & wait for acking
				if self.timer == None:
					self.playTimer()		
				print "Sending seg " + str(packet.seg) + " to " + str(self.addr) # don't log ack/con for they are logged somewhere else		

			wrap = packet.wrap()

			# inform Queue we're done with the packet we got
			self.buff.task_done()

			if random.randint(1, 100) < self.ploss:
				continue # simulate lost packet
			
			self.sock.sendto(wrap, self.addr)

			if packet.end:
				if packet.ack or self.endAttempt >= END_ATTEMPTS: # end if we are acking end packet
					self.endCon()
				else:
					self.endAttempt += 1

	def endCon(self):
		print "Ending connection to " + str(self.addr)
		self.end = True	

	def playTimer(self):
		if self.timer != None:
			self.timer.cancel() # stop current timer

		if self.waiting.empty(): # nothing to wait for, start timer on start function when a new packet is sent then
			self.timer = None
			return

		self.timer = threading.Timer(ACK_TIMEOUT, self.timeout)
		self.timer.start()

	def timeout(self):
		# expected ack didn't arrive... send window again!
		print "Timed out! Enqueuing window again..."
		while not self.waiting.empty():
			self.buff.put(self.waiting.get())

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

		if not packet.validChecksum() or random.randint(1, 100) < self.pcorr: # do not receive broken packets or simulate a broken packet
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

			if packet.end:
				self.endCon()

			if not self.waiting.empty():
				waited = self.waiting.get() # don't block...
				if waited.seg != packet.ack:
					print "Removed wrong packet of waiting list. Expected seg: " + str(waited.seg) # TODO FOR DEBUG ONLY! REMOVE
			else: # TODO FOR DEBUG ONLY! REMOVE
				print "Failed removing acked packet from waiting list!!!"

			self.playTimer() # ack received, start timer again
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
