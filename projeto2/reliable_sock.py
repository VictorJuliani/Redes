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
		self.acks = Queue()

		# TODO sort waiting queue by seg! on ack != seg, add packet back to the queue

		self.seg = 0 # current packet
		self.ack = 0 # window base point
		self.nextSeg = random.randint(1,1000) # next expected packet

		# self.lock = threading.Condition()

	def start(self):
		while not self.end:
			src = 0
			if not self.acks.empty():
				src = 1
				packet = self.acks.get(False)
			elif not self.fail.empty():
				src = 2
				packet = self.fail.get(False) # not empty, so won't block...
			else: # no failed packets or acks to send...
				self.buff.get(True) # block until another packet is added

			packet = self.nextPacket()
			if src != 1: # don't block on acks...
				self.waiting.put(packet) # add packet to waiting queue. it will block if waiting queue is full: all packets are sent & wait for acking
			wrap = packet.wrap()
			
			print "Sending seg " + str(packet.seg) + " to " + str(self.addr)
			self.sock.sendto(wrap, self.addr)

			# inform Queue we're done with the element we got
			if src == 0:
				self.buff.task_done()
			elif src == 1:
				self.acks.task_done()
			else:
				self.fail.task_done()

			# TODO end packets/end acks CAN FAIL TOO. Use timeout to set end = True when end packet is sent
			if packet.end:
				#print "Ending connection to " + str(self.addr)
				self.end = True

	def enqueuePacket(self, data):
		packet = Packet(data)
		if self.init:
			packet.seg = self.seg
			self.seg += 1
		else:
			packet.ack = self.nextSeg # con packet: seg = 0; ack = nextSeg

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
		self.acks.put(Packet('', 0, ack, endAck))

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

		if not self.init:
			self.init = True
			if packet.seg == 0: # con request
				print "Connection request from " + str(self.addr)
				self.seg = packet.ack # set seg with nextSeg received in ack field
				self.ack = packet.ack # intitialize ack with nextSeg
				self.acks.put(Packet('', self.nextSeg, 0, packet.end)) # ack with nextSeg expected on seg field
				return packet
			else: # con ack
				self.seg = packet.seg # set seg with nextSeg of client
				self.ack = packet.seg # intitialize ack with nextSeg
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
		elif self.nextSeg == packet.seg: # expected seg!
			self.nextSeg += 1
			self.ackPacket(packet.seg, packet.end)
			print "Acking packet " + str(packet.seg)
			return packet
		else:
			print "Bad packet received! Seg: " + str(packet.seg) + " expected: " + str(self.nextSeg) + " ack: " + str(packet.ack)
		
		return None
