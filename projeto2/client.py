#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
import sys


def main(argv):
  port = ''
  host = ''
  filename = ''

  if(len(argv) < 4):
    print 'usage: client.py port hostname filename'
    sys.exit(2)
  else:
    port = int(argv[1])
    host = argv[2]
    filename = argv[3]
  
  try:
    client = socket(AF_INET, SOCK_DGRAM)
  except:
    print 'Failed to create UDP Socket!'

  while 1:
    request = filename
    client.sendto(request, (host, port))

    reply, addr = client.recvfrom(1024)

    if(reply):
      print reply
      if(reply == 'end'):
        break

  client.close()

if __name__ == "__main__":
  main(sys.argv)
