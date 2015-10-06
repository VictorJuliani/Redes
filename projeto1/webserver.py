#!/Python27/python

# Import modules for CGI handling
import cgi, cgitb
from socket import *

ips = ['192.168.22.128']

def clientInstance(address, machine):
	cmds_list = []
	responses = []
	serverPort = 12000
	clientSocket = socket(AF_INET, SOCK_DGRAM)

	# for each marked command, make a request
	for key in commands:
		if form.getvalue("m"+str(machine)+"-"+commands[key]): # if value is checked
			#print form.getvalue("m"+str(machine)+"-"+commands[key])
			parameter = form.getvalue("m"+str(machine)+"+"+commands[key])
			if parameter == None:
				parameter = ''
			clientSocket.sendto("REQUEST " + str(key) + " " + parameter, (address, serverPort))

			# Protocol: RESPONSE X RESULT
			resMessage = clientSocket.recvfrom(8192)[0]
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

for i in range(len(ips)):
	res, cmds = clientInstance(ips[i], i+1)
	resMachine = ""
	for j in range(len(cmds)):
		resMachine += "<h4>"+commands[cmds[j]]+"</h4><p>"+res[j].replace("\n", "<br>")+"</p>"

	html = html.replace("machine"+str(i+1), resMachine)

for i in range(3):
	html = html.replace("machine" + str(i+1), "")

print "Content-type:text/html"
print
print html
