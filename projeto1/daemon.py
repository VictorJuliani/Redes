from socket import *
import so
import subprocess
import re

commands = {1: "ps", 2: "df", 3: "uptime", 4: "finger"}

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))
while 1:
	message, clientAddress = serverSocket.recvfrom(2048)

	# Protocol: REQUEST X PARAMS
	index = message[8:9] # get X
	cmd = commands[int(index)] # get commands[X]
	params = message[10:] # get params

	# clear | > < ; characters from params
	params = re.sub('[\\|\\>\\<\\;]', "", params)

	res = "RESPONSE " + index + " " + subprocess.check_output([cmd, params])

	serverSocket.sendto(res, clientAddress)
