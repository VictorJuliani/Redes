#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
from math import ceil
import sys, os

# Add header with a piece of data
def make_packet(data, seqnum, acknum, checksum):
  pkt = ''
  pkt += str(seqnum)+' '+str(acknum)+' '+str(checksum)+' '+data
  return pkt
  

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
  seqnum = 0
  checksum = 0
  acknum = 0

  while 1:
    filename, addr = server.recvfrom(1024)
    
    fp = open(filename, 'r')
    text = fp.read()
    # A wild HARD CODE appears
    pkt = []
    pktnum = int(ceil(len(text)/10))
    for i in range(pktnum):
      start = i * pktnum 
      end = (i+1) * pktnum
      print start, end
      pkt.append(text[start:end])
    
    for i in range(len(pkt)):
      packet= make_packet(pkt[i], seqnum, acknum, checksum)
      seqnum += 1
      server.sendto(packet, addr)
    server.sendto('end', addr)
    seqnum = 0

  server.close()

if __name__ == "__main__":
  main(sys.argv)
