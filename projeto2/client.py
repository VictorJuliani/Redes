#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
from shared import HEADER, HEADER_ACK, get_CRC32
import sys

def main(argv):
	try:
		port = int(argv[1])
		host = argv[2]
		filename = argv[3]
	except IndexError:
		print 'Usage: python client.py port host filename'
		sys.exit(-1)

	# create client socket
	client = socket(AF_INET, SOCK_DGRAM)
	# send filename to server
	client.sendto(filename, (host, port))  
	print "Connecting to " + str(host) + ":" + str(port)
	print "Requesting file " + filename

	data = {}

	# loop until all packages have been received
	while 1:
		# receives the package and stores in 'reply'.
		# 'reply_find' stores the mark that divides the
		# header and the data
		# 'reply_data' stores the data.
		reply, addr = client.recvfrom(1024)	
		print "Received " + str(len(reply)) + " bytes from server"

		reply_find = reply.find('\n\n')
		reply_data = reply[(reply_find+2):]

		# 'header' stores the package header
		header = reply[0:reply_find].split('\n')

		# 'checksum' stores the checksum value from the header.
		# same thing with 'end'.
		checksum = header[2].split(' ')[1]
		end = int(header[3].split(' ')[1])
		
		# check if checksum value is right	  
		if (checksum != get_CRC32(reply_data)):
			continue
		
		# 'segnum' from header
		# 'ack' from header
		segnum = int(header[0].split(' ')[1])
		ack = int(header[1].split(' ')[1])
				
		# check if package has greater 'segnum' than the last one acknowledged	
		if (segnum > ack):
			client.sendto((HEADER_ACK % (segnum)), (host, port)) # TODO add checksum here too!!!
			print "Acking server for segnum " + str(segnum)

		# check if its the last package
		if (end == 1):
			break
		else: # stores the data in the dictionary with 'segnum' as key
			data[segnum] = reply_data

	# gathers all the data stored in the dictionary and stores it in 'full_data'
	full_data = ''
	for i in sorted(data):
		full_data += data[i]
	
	print full_data
	
if __name__ == '__main__':
	main(sys.argv)
