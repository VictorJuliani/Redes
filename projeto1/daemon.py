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
	#TODO: LELEO (this is wrong?)
	index = message[8:1] # get X
	cmd = commands[index] # get commands[X]
	params = message[10:] # get params

	# TODO: params = re.sub(regex, replace, params)

	res = "RESPONSE " + index " " + subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout.read()

	serverSocket.sendto(res, clientAddress)
