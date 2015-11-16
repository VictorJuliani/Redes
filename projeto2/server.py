#!/usr/bin/python

from socket import socket, AF_INET, SOCK_DGRAM
import sys

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
  
    if not filename:
      break
  
    server.sendto(filename + ' done!', addr)
    
  server.close()

if __name__ == "__main__":
  main(sys.argv)
