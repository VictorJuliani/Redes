#!/usr/bin/python
# -*- coding: utf-8 -*-

import binascii

# HEADER:
# segnum %d\n
# acknum %d\n
# checksum %s\n
# end %d\n
# err %d\n
HEADER = 'segnum %d\nacknum %d\nchecksum %s\nend %d\nerr %d\ncon %d\n\n'

class Packet:
	def __init__ (self, data, seg = 0, ack = 0, end = 0, err = 0, con = 0):
		self.data = data
		self.seg = seg
		self.ack = ack
		self.checksum = self.get_CRC32(data)
		self.end = end
		self.err = err
		self.con = con

	def __cmp__(self, other):
		if other == None:
			return -1
    	return cmp(self.seg, other.seg)
				
	# build packet string
	def wrap(self):
		packet = HEADER % (self.seg, self.ack, self.checksum, self.end, self.err, self.con) # build header
		packet += self.data # add body
		return packet

	def unwrap(self):
		header_end = self.data.find('\n\n')
		header = self.data[0:header_end].split('\n')

		self.data = self.data[(header_end+2):]
		self.seg = int(header[0].split(' ')[1])
		self.ack = int(header[1].split(' ')[1])
		self.checksum = header[2].split(' ')[1]
		self.end = int(header[3].split(' ')[1])
		self.err = int(header[4].split(' ')[1])
		self.con = int(header[5].split(' ')[1])

	def validChecksum(self):
		return self.checksum == self.get_CRC32(self.data)

	def get_CRC32(self, data):
		buf = (binascii.crc32(data) & 0xFFFFFFFF)
		return "%08X" % buf
