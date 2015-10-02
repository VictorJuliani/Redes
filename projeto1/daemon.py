from socket import *
from os import subprocess
import re

commands = {1: "ps", 2: "df", 3: "uptime", 4: "finger"}

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))
while 1:
	message, clientAddress = serverSocket.recvfrom(2048)

	# Protocol: REQUEST X PARAMS
	index = message[8:9] # get X
	cmd = commands[index] # get commands[X]
	params = message[10:] # get params

	# clear | > < ; characters from params
	params = re.sub('[\\|\\>\\<\\;]', "", x)

	res = "RESPONSE " + index " " + subprocess.Popen(cmd + " " + params, stdout=subprocess.PIPE).stdout.read()

	serverSocket.sendto(res, clientAddress)
