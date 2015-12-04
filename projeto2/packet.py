#!/usr/bin/python
# -*- coding: utf-8 -*-

# HEADER:
# segnum %d\n
# acknum %d\n
# checksum %s\n
# end %d\n
# err %d\n
HEADER = 'segnum %d\nacknum %d\nchecksum %s\nend %d\nerr %d\n\n'

class Packet:
	def __init__ (self, data, seg = 0, ack = 0, end = 0, err = 0):
		self.data = data
		self.seg = seg
		self.ack = ack
		self.checksum = get_CRC32(data)
		self.end = end
		self.err = err
				
	# build packet string
	def wrap(self):
		packet = HEADER % (self.seg, self.ack, get_CRC32(), self.end, self.err) # build header
		packet += data # add body
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

	def validChecksum(self):
		return self.checksum == get_CRC32(self.data)

	def get_CRC32(self):
		buf = (binascii.crc32(self.data) & 0xFFFFFFFF)
		return "%08X" % buf
