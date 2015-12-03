
#!/usr/bin/python
# -*- coding: utf-8 -*-

import binascii

# HEADER:
# segnum %d\n
# acknum %d\n
# checksum %s\n
# end %d\n\n
HEADER = 'segnum %d\nacknum %d\nchecksum %s\nend %d\n\n'
HEADER_ACK = 'ack %d'

def get_CRC32(data):
	buf = (binascii.crc32(data) & 0xFFFFFFFF)
	return "%08X" % buf
