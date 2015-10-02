#!/usr/bin/python

# Import modules for CGI handling
import cgi, cgitb
from socket import *

def clientInstance(address, machine):
	cmds_list = []
	responses = []
	serverPort = 12000
	clientSocket = socket(socket.AF_INET,socket.SOCK_DGRAM)

	# for each marked command, make a request
	for key in commands:
		if form.getvalue("m"+str(machine)+"-"+commands[key]):
			# just get parameter if checkbox is checked
			parameter = form.getvalue("m"+str(machine)+"+"+commands[key])
			clientSocket.sendto("REQUEST " + str(key) + " "+parameter,(address, serverPort)) # TODO add PARAMS

			# Protocol: RESPONSE X RESULT
			resMessage = clientSocket.recvfrom(2048)[0]
			cmds_list.append(key)
			responses.append(resMessage[11:]) # cut RESPONSE_X_

	clientSocket.close()

	return responses, cmds_list

# Create instance of FieldStorage
form = cgi.FieldStorage()

commands = {1: "ps", 2: "df", 3: "uptime", 4: "finger"}

f = open('response.html', 'r')
html = f.read()
f.close()

for i in range(3):
	res, cmds = clientInstance("ADDR" + i, i)
	for j in range(len(cmds)):
		html.replace("machine"+str(i), "<h4>"+commands[cmds[j]]+"</h4><p>"+res[j]+"</p>")

print html
