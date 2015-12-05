#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
from reliable_sock import RSock
from packet import Packet
import thread
import sys
import os.path

PACKET_SIZE = 10.0 # bytes

def newCon(data, addr):
	sock = RSock(server, addr)
	packet = sock.receivePacket(data)

	if packet == None: # bad packet...
		return

	fileRequest(packet, sock)

	clients[addr] = sock
	sock.start()

def fileRequest(packet, sock):
	if not os.path.isfile(packet.data):
		sock.err() # send error packet...
	else:
		filename = packet.data
		fp = open(filename, 'r')
		filedata = fp.read()
		size = int(math.ceil(len(filedata)/PACKET_SIZE)) # how many chunks

		for i in range(size):
			start = int(i * PACKET_SIZE)
			end = int((i+1) * PACKET_SIZE)
			sock.enqueuePacket(self.filedata[start:end])

		print "File request " + filename + " from " + str(addr)
		sock.end() # enqueue end packet after all file packets

# init
try:
	port = int(sys.argv[1])
	# TODO PL & PC (prob. loss & prob. corr.)
except IndexError:
	print 'Usage: python server.py port'
	sys.exit(-1)

host = ''

server = socket(AF_INET, SOCK_DGRAM)
server.bind((host, port))

clients = {}

while True:
	data, addr = server.recvfrom(1024)

	if addr not in clients: # is it a new connection?
		thread.start_new_thread(newCon, (data, addr)) # start connection in a new thread
	else:
		packet = clients[addr].receivePacket(data) # notify client of received packet and handle it
		if packet != None:
			if packet.end == 1: # endAck
				del clients[addr] # file sent! clear connection
			else:
				fileRequest(packet, clients[addr]) # another file request
