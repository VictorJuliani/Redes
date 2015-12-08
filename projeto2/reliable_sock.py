#!/usr/bin/python
# -*- coding: utf-8 -*-

from Queue import PriorityQueue as PQueue
from Queue import PriorityQueue
from packet import Packet
import binascii, random, threading

WINDOW_SIZE = 10 # packets
ACK_TIMEOUT = 1 # seconds
ATTEMPT = 10 # how many times should we try ending con until force closing?

class RSock:
	def __init__ (self, sock, addr, cwnd, ploss, pcorr):
		self.init = False
		self.end = False
		self.requesting = False
		self.sock = sock
		self.addr = addr
		self.ploss = ploss
		self.pcorr = pcorr
		self.cwnd = cwnd

		if self.cwnd <= 0:
			self.cwnd = WINDOW_SIZE

		self.startCwnd = self.cwnd
		self.lastBadAck = 0
		self.dupAck = 0
		self.ssthresh = 0

		self.attempt = 0
		self.timer = None

		self.lock = threading.Lock()

		# PQueue will sort packets by segnum, so when inserting in queue, packets will be like:
		# Acks - segnum = 0
		# Failed packets (for their segnum is securely < unset packets)
		# Unsent packets
		# So ordering is guaranteed and ACKs should be sent immediately
		self.buff = PQueue() # packets to send
		self.waiting = PQueue(cwnd) # packets wating for ACK

		self.seg = 0 # current packet
		self.ack = 0 # last valid ack
		self.nextSeg = random.randint(1,1000) # next expected packet

	def start(self):
		while not self.end:
			packet = self.buff.get(True) # block until another packet is added
			if self.timer == None:
				self.playTimer()	
			# only regular packets should be recent. 
			# acks require the other side of the socket to be sent again, so we don't need to put on waiting queue

			if packet.seg > 0 and packet.seg < self.ack: # don't send acked packets again...
				self.buff.task_done()
				continue

			if packet.ack == 0 and (self.requesting or packet.con == 0):
				self.lock.acquire(True) # wait for timeout function if needed
				self.lock.release() # release it BEFORE put function or it will deadlock
				self.waiting.put(packet) # block after timer!
				print "Sending seg " + str(packet.seg) + " to " + str(self.addr) # don't log ack/con for they are logged somewhere else		

			# inform Queue we're done with the packet we got
			self.buff.task_done()
			
			if random.randint(1, 100) < self.ploss:
				print "Simulating delayed packet"
				continue # simulate lost packet
	
			self.sock.sendto(packet.wrap(), self.addr)

			if packet.end:
				print "Sending connection end"

			if (packet.end and packet.ack) or self.attempt >= ATTEMPT: # should this avoid dced socket to be maintained
				self.endCon()

	def endCon(self):
		if self.attempt >= ATTEMPT:
			print "Forcing close on socket due to response lack"
		else:
			print "Ending connection to " + str(self.addr)
		self.end = True	

	def playTimer(self):
		if self.timer != None:
			self.timer.cancel() # stop current timer

		self.timer = threading.Timer(ACK_TIMEOUT, self.timeout, args=[True])
		self.timer.start()

	def timeout(self, slowStart):
		if not self.end and not self.waiting.empty():
			print "Timed out! Enqueuing window again..."

		self.lock.acquire(True) # block other thread
		self.attempt += 1 # should this avoid dced socket to be maintained

		# expected ack didn't arrive... send window again!
		
		while not self.waiting.empty():
			packet = self.waiting.get()
			if packet.seg >= self.ack: # no need to resend acked packets...
				self.buff.put(packet)
			self.waiting.task_done()
		
		# TCP RENO
		if slowStart:
			self.cwnd = self.startCwnd
			self.ssthresh = 0 # slow-start
			self.updateWindow()

		self.lock.release()

		if not self.end:
			self.playTimer()

	# TCP RENO
	def increaseWindow(self):
		self.lock.acquire(True)
		if self.ssthresh == 0 or self.ssthresh > self.cwnd: # slow start
			self.cwnd *= 2 # duplicate window size
		else:
			self.cwnd += 1 # congestion avoid
		self.updateWindow()
		self.lock.release()

	def decreaseWindow(self):
		self.lock.acquire(True)

		# fast retransmit
		if self.timer != None:
			self.timer.cancel() # stop current timer
		self.timeout(False) # do window retransmition

		self.cwnd /= 2
		self.ssthresh = self.cwnd
		self.updateWindow()
		self.lock.release()

	def updateWindow(self):
		tmp = PQueue(self.cwnd)

		for i in range(min(self.waiting.qsize(), self.cwnd)) # move packets from waiting to tmp until tmp is full or waiting is empty
			packet = self.waiting.get(False)
			if packet.seg >= self.ack: # no need to resend acked packets...
				tmp.put(packet)
			self.waiting.task_done()

		# shouldn't happen due to fast retransmit
		while not self.waiting.empty(): # add remaining packets to buff
			packet = self.waiting.get()
			if packet.seg >= self.ack: # no need to resend acked packets...
				self.buff.put(packet)
			self.waiting.task_done()

		self.waiting = tmp # this is required for it's not possible to change the Queue's maxsize :(


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
		
	def ackPacket(self, endAck = 0):
		self.buff.put(Packet('', 0, self.nextSeg, endAck))
	
	def receivePacket(self, data):
		packet = Packet(data)
		packet.unwrap()

		self.attempts = 0

		if not packet.validChecksum() or random.randint(1, 100) < self.pcorr: # do not receive broken packets or simulate a broken packet
			print "Bad checksum received on seg: " + str(packet.seg) + " ack: " + str(packet.ack)
			return None

		if packet.con > 0:		
			self.seg = packet.con # set seg with nextSeg received in con field
			self.ack = packet.con
			self.init = True
			if not self.requesting: # this socket received the connection request, then ack it
				print "Connection request from " + str(self.addr)
				self.buff.put(Packet('', con = self.nextSeg)) # ack with nextSeg expected on con field
				return packet
			else:
				print "Connection established!"
		elif not self.init:
			return None
		elif (packet.ack > 0): # ack packet
			self.lock.acquire(True)

			if packet.ack > self.ack:
				self.dupAck = 0 # reset dup ack counting
				self.lastBadAck = 0
				self.ack += (packet.ack - self.ack)

				self.increaseWindow()

				self.playTimer() # ack received, start timer again
		 		print "Received expected ack " + str(packet.ack) + " on connection " + str(self.addr)

				if packet.end: # ack for end packet received
					self.endCon()
			elif packet.ack == self.lastBadAck:
				self.dupAck += 1
				if (self.dupAck == 3):
					print "Duplicate ACKs received. Doing fast retransmit and resizing window."
					self.decreaseWindow()
			else:
				self.lastBadAck = packet.ack
				self.dupAck = 1

			self.lock.release()
		elif packet.seg < self.nextSeg:
			self.ackPacket() # old packet received again, ACK might be lost.. send it again
			print "Duplicated packet " + str(packet.seg) + ". Sending ack again and ignoring"
		elif packet.seg > self.nextSeg:
			self.ackPacket()
		elif self.nextSeg == packet.seg: # expected seg!
			self.nextSeg += 1
			self.ackPacket(packet.end)
			print "Acking packet " + str(packet.seg)
			return packet
		
		return None
