#!/usr/bin/python

# Import modules for CGI handling 
import cgi, cgitb
from socket import *

def clientInstance(address, machine):
	msg = "REQUEST "
	cmds_list = []	
	for key in commands:
		if form.getvalue("m"+str(machine)+"-"+commands[key]):
			cmds_list.append(key)			
			msg += str(key)+" "

	serverPort = 12000
	clientSocket = socket(socket.AF_INET,socket.SOCK_DGRAM)
	clientSocket.sendto(msg,(address, serverPort))

	resMessage = clientSocket.recvfrom(2048)[0]
	resMessage = resMessage[9:]
	responses = resMessage.split("//\n")

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
