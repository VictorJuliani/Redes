#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import socket, AF_INET, SOCK_DGRAM
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

  reply, addr = client.recvfrom(1024)

  print reply


if __name__ == '__main__':
  main(sys.argv)
