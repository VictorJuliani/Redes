#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
from math import floor
import sys, os

# Add header with a piece of data
def make_packet(data):
  packet = 'header '+data
  return packet
  

def main(argv):
  port = ''
  host = ''

  if(len(argv) < 2):
    print 'usage: server.py port'
    exit(2)
  else:
    port = int(argv[1])
      
  try:
    server = socket(AF_INET, SOCK_DGRAM)
  except:
    print 'Failed to create socket'

  server.bind((host, port))

  while 1:
    filename, addr = server.recvfrom(1024)
    
    fp = open(filename, 'r')
    text = fp.read()
    pkt = []
    aux = ''
    for i in range(len(text)):
      aux += text[i]
      if (i%10 == 0 and i != 0):
        pkt.append(aux)
        aux = ''
    
    for i in range(len(pkt)):
      packet = make_packet(pkt[i])
      server.sendto(packet, addr)
    server.sendto('end', addr)

  server.close()

if __name__ == "__main__":
  main(sys.argv)
