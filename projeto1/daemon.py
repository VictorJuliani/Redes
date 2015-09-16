from socket import *
from os import subprocess

commands = {1: "ps", 2: "df", 3: "uptime", 4: "finger"}

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))
while 1:
	message, clientAddress = serverSocket.recvfrom(2048)
	cmds = message.split(" ")
	
	res = "RESPONSE "

	for i in range(1, len(cmds))
		res += subprocess.Popen(commands[i], stdout=subprocess.PIPE).stdout.read() + "//\n"

	serverSocket.sendto(res, clientAddress)
