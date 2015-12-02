#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
import thread
import time
import sys


def reliable(filename, address):
  fp = open(filename, 'r')
  data = fp.read()
  packet = 'segnum %d\nacknum %d\n' % (0, 0)
  packet += data
  server.sendto(packet, address)


# init
try:
  port = int(sys.argv[1])
except IndexError:
  print 'Usage: python server.py port'
  sys.exit(-1)

host = ''

server = socket(AF_INET, SOCK_DGRAM)

server.bind((host, port))

while 1:
  filename, addr = server.recvfrom(1024)
  thread.start_new_thread(reliable, (filename, addr))
