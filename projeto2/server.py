#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
from connection import Connection, PACKET_SIZE
from reliable_sock import RSock
import thread
import sys
import os.path

def newCon(packet, addr):
	filename = packet.data
	if packet.seg == 0 and os.path.isfile(filename): # new connection!
		sock = RSock(server, addr)
		sock.init = True # connection received, so it's initialized
		clients[addr] = Connection(filename, sock)

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
		packet = Packet(data)
		packet.unwrap()
		thread.start_new_thread(newCon, (packet, addr)) # start connection in a new thread
	else:
		packet = clients[addr].sock.receivePacket(data) # notify client of received packet and handle it
		if packet != None and packet.end == 1: # endAck
			del clients[addr] # file sent! clear connection
