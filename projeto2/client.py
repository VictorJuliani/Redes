#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
from packet import Packet
from reliable_sock import RSock
import sys, thread

def main(argv):
	try:
		port = int(argv[1])
		host = argv[2]
		filename = argv[3]
		# TODO PL & PC (prob. loss & prob. corr.)
	except IndexError:
		print 'Usage: python client.py port host filename'
		sys.exit(-1)

	# create client socket
	client = socket(AF_INET, SOCK_DGRAM)

	addr = (host, port)

	thread.start_new_thread(recvFile, (client,))
	sock = RSock(client, addr)
	sock.enqueuePacket(filename)
	print "Connecting to " + str(addr) + " to ask for file " + filename
	sock.start()

def recvFile(client):
	data = []
	# loop until all packages have been received
	while True:
		# receives the package and stores in 'reply'.
		reply, addr = client.recvfrom(1024)	
		print "Received " + str(len(reply)) + " bytes from server"
		packet = sock.receivePacket(reply)

		if packet == None:
			continue

		# check if its the last package
		if (packet.end == 1):
			break
		else: # store packet data in data list
			data.append(packet.data)

	# gathers all the data stored in the dictionary and stores it in 'full_data'
	full_data = ''
	for i in data:
		full_data += data

	# TODO create file
	
	print full_data
	
if __name__ == '__main__':
	main(sys.argv)
