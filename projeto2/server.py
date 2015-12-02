#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
from shared import HEADER, HEADER_ACK, get_CRC32
from connection import Connection
import thread
import time
import sys
import os.path

PACKET_SIZE = 800 #bytes
WINDOW_SIZE = 10 # packets
ACK_TIMEOUT = 30 # seconds

# filename - file to send
# address - target
def reliable(filename, address):
  	con = Connection(filename, address)
  	clients[address] = con
  	data = con.data

  	while (con.ack < con.size):
  		sendWindow(con)

  	con.seg += 1
  	while (con.ack) < con.seg):
		sendPacket(con, '', 1) # notify client of end
		ackWait(con, con.seg)

	del clients[address] # file sent! clear connection

# con - the Connection object
def sendWindow(con):
	startAck = con.ack
 	size = min(WINDOW_SIZE, (con.size - con.ack))
 	# start sending from last acked packet and go WINDOW_SIZE or remaining packets further
  	for i in range(startAck, size):
	    con.seg += 1
	    start = i * con.size		
	    end = (i+1) * con.size
	    sendPacket(con, data[start:end], 0)

	# wait for acks
	ackWait(con, (startAck + size - 1))

def ackWait(con, targetAck):	
	# TODO use a timeout for failure in packet receiving will result in endless loop!
	while con.ack < targetAck):
		continue

# con - the Connection object
# data - content of packet
# end - is last packet?
def sendPacket(con, data, end):
  	packet = HEADER % (con.seg, con.ack, get_CRC32(data), end) # build header
  	packet += data # add body
  	server.sendto(packet, con.addr)
  	# TODO add msg logging

# init
try:
  	port = int(sys.argv[1])
except IndexError:
  	print 'Usage: python server.py port'
  	sys.exit(-1)

host = ''

server = socket(AF_INET, SOCK_DGRAM)
server.bind((host, port))

clients = {}

while 1:
  	pkt, addr = server.recvfrom(1024)
  	# TODO add msg logging
  	if addr in clients
  		clients[addr].notifyAck(pkt) # notify client that an ack is received and handle it
  	elif os.path.isfile(pkt):
  		thread.start_new_thread(reliable, (pkt, addr)) # new client requesting file!
  	# TODO else answer error (use HEADER!!)
