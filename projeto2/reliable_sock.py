#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import deque
from packet import Packet
import binascii

PACKET_SIZE = 10.0 # bytes
WINDOW_SIZE = 10 # packets
ACK_TIMEOUT = 30 # seconds TODO

class RSock:
	def __init__ (self, sock, addr):
		self.init = False
		self.end = False
		self.sock = sock
		self.addr = addr
		self.buff = deque()

		self.seg = random.randint(1,1000) # current packet
		self.ack = self.seg # window base point
		self.nextSeg = 0 # next expected packet

		self.lock = Lock()

		wndCursor = 0 # current sending packet inside window
		while not end:
			lock.acquire()
			if len(buff) == 0:
				lock.wait()

			packet = buff[wndCursor] # do not pop for packets may not be acked and required a try-again
			wndCursor += 1

			if packet.seg > (base + WINDOW_SIZE):
				wndCursor = 0 # reached end of window, start count again
				lock.wait() # block send for this packet is out of window
			
			lock.release()

			wrap = packet.wrap()
			
			print "Sending " + str(len(wrap)) + " bytes to " + str(self.addr)
			self.sock.sendto(wrap, self.addr)

			# TODO end packets/end acks CAN FAIL TOO. Use timeout to set end = True when end packet is sent
			if packet.end:
				print "Ending connection to " + str(self.addr)
				end = True

	def enqueuePacket(self, data):
		seg = 0
		if self.init:
			self.seg += 1
			seg = self.seg

		addAndWake(Packet(data, seg, 0))

	def end(self):
		self.seg += 1
		addAndWake(Packet('', self.seg, 0, 1))
		
	def ackPacket(self, ack, endAck):
		addAndWake(Packet(data, 0, ack, endAck))

	def addAndWake(self, packet):
		self.buff.put(packet)
		wake()
		try:
			self.notify()
		except RuntimeError:
			pass # wasn't locked...	

	def receivePacket(self, data):
		packet = Packet(data)
		packet.unwrap()

		if !packet.validChecksum(): # do not receive broken packets
			print "Bad checksum received on seg: " + packet.seg + " ack: " + packet.ack
			return None

		# ack of filename or other acks
		if (not init and packet.ack == 0) or (packet.ack > 0 and packet.ack == self.ack + 1): # expected ack!
			init = True
			self.ack += 1
			buff.popLeft() # remove acked packet from queue
			print "Received ack " + str(ackno) + " on connection " + str(self.addr)
			wake()	
			return packet
		elif self.nextSeg == packet.seg: # expected seg!
			self.nextSeg += 1
			ackPacket(packet.seg, packet.end) # ACK packet received
			return packet
		else:
			print "Bad packet received! Seg: " + packet.seg + " expected: " + self.nextSeg + " ack: " + packet.ack
		
		return None