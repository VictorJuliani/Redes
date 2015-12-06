#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
from packet import Packet
from reliable_sock import RSock
import sys, random
from threading import Thread

def main(argv):
	try:
		port = int(argv[1])
		host = argv[2]
		filename = argv[3]

		if len(argv) > 3:
			ploss = int(argv[4])
		else:
			ploss = random.randint(1, 40)

		if len(argv) > 4:
			pcorr = int(argv[5])
		else:
			pcorr = random.randint(1, 40)
	except IndexError:
		print 'Usage: python client.py port host filename [prob. loss] [prob. corr]'
		sys.exit(-1)

	# create client socket
	client = socket(AF_INET, SOCK_DGRAM)

	sock = RSock(client, (host, port), ploss, pcorr)
	sock.enqueuePacket(filename)
	print "Connecting to " + str(sock.addr) + " to ask for file " + filename
	t = Thread(target=recvFile, args=(filename, client, sock))
	t.start()
	sock.start()
	t.join()

def recvFile(filename, client, sock):
	data = []
	# loop until all packages have been received
	while True:
		# receives the package and stores in 'reply'.
		reply, addr = client.recvfrom(1024)	
		packet = sock.receivePacket(reply)

		if packet == None:
			continue

		if (packet.err > 0): # file not found
			filename = raw_input("Server doesn't have this file! Choose another one: ")
			sock.enqueuePacket(filename)
			continue
		if (packet.end > 0): # check if its the last package
			print "EOF received, printing file:"
			break
		else: # store packet data in data list
			print "Appending " + str(len(packet.data)) + " bytes received from server"
			data.append(packet.data)

	# gathers all the data stored in the dictionary and stores it in 'full_data'
	full_data = ''
	for i in data:
		full_data += i

	f = open(filename, 'w+') # create or overwrite file
	f.write(full_data)
	f.close()
	
	print full_data
	
if __name__ == '__main__':
	main(sys.argv)
