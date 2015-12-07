# Projeto 2 - Redes dec Computadores 2015/2

* Victor Juliani - 551929
* Leonardo Lopes - 552003
* Marcelo Otaviano - 573124
* Arthur Munhoz - 379409

# Descrição da Implementação

### Formato do Cabeçalho:

(*packet:12*).
``` python
HEADER = 'segnum %d\nacknum %d\nchecksum %s\nend %d\nerr %d\ncon %d\n\n'
```
* Segnum: Número de sequência do pacote.
* Acknum: Se maior que 0, o pacote é um ack e seu valor indica sobre qual pacote se refere.
* Checksum: Valor do checksum do conteúdo do pacote.
* End: Se diferente de 0, o pacote representa o fim da transferência e consequentemente o fim da conexão.
* Err: Se diferente de 0, indica que o arquivo não foi encontrado no servidor.
* Con: Se maior que zero, indica que é um pacote de conexão e seu valor representa o número de sequência (Segnum) esperado.

### Tipos de Mensagens Utilizadas:

Pacote enviado para iniciar a conexão (*reliable_sock:110-111*).
``` python
self.requesting = True
packet.con = self.nextSeg # con packet: seg = 0; ack = 0; con = nextSeg
```
Pacote que representa o ack de conexão (*reliable_sock:143-144*).
``` python			
print "Connection request from " + str(self.addr)
self.buff.put(Packet('', end = packet.end, con = self.nextSeg)) # ack with nextSeg expected on con field
```
Pacote de dados.(*reliable_sock:100-101*).
``` python
packet.seg = self.seg
self.seg += 1
```
Pacote de ack (*reliable_sock:125-126*).
``` python
def ackPacket(self, ack, endAck):
		self.buff.put(Packet('', 0, ack, endAck))
```
Pacote que indica o fim da transferência de dados (*reliable_sock:115-118*).
``` python
def endPacket(self):
		packet = Packet('', self.seg, end=1)
		self.seg += 1
		self.buff.put(packet)
```

Pacote que indica erro na transferência de dados (*reliable_sock:120-123*).
``` python
def errPacket(self):
		packet = Packet('', self.seg, err=1)
		self.seg += 1
		self.buff.put(packet)
```

### Valor do Timeout, Tamanho Padrão de Janela, Tamanho do Pacote, e Limite de Tentativas de Envio Sem Resposta:

(*reliable_sock:9-11*)
``` python
WINDOW_SIZE = 10 # packets
ACK_TIMEOUT = 1 # seconds
END_ATTEMPTS = 3 # how many times should we try ending con until force closing?
```
(*server:9*).
``` python
PACKET_SIZE = 10.0 # bytes
```

### Descrição do Protocolo Utilizado:
Com base no protocolo Go-Back-N, implementamos uma janela de envio de pacotes responsável por enviar no máximo o tamanho padrão definido em *WINDOW_SIZE* ou passado por parâmetro na inicialização de cada script. Uma vez que o limite da janela é atingido, a *thread* de envio é bloqueada até que o *ACK* esperado seja recebido, causando o deslocamento da janela, ou o *timeout* seja disparado, re-enviando os pacotes em espera.


### A implementação:
#### O servidor
O servidor executa uma única *thread* para o recebimento de pacotes. Ao receber um pacote, verifica se a origem do mesmo já é conhecida e, se for, encaminha o pacote ao *reliable_sock* correspondente ao endereço. Caso contrário, inicía uma nova *thread* para o endereço recebido.
(*server:69-82*).
``` python
clients = {}

while True:
	data, addr = server.recvfrom(1024)

	if addr not in clients: # is it a new connection?
		thread.start_new_thread(newCon, (data, addr)) # start connection in a new thread
	else:
		packet = clients[addr].receivePacket(data) # notify client of received packet and handle it
		if packet != None:
			if packet.end == 1: # endAck
				del clients[addr] # file sent! clear connection
			else:
				fileRequest(packet, clients[addr]) # another file request
```

A inicialização da conexão é feita pela chamada da função *newCon*, que inicializa um *reliable_sock* e verifica se o pacote recebido contém o nome de um arquivo válido.
(*server:11-21*).
``` python
def newCon(data, addr):
	sock = RSock(server, addr, ploss, pcorr)
	packet = sock.receivePacket(data)

	if packet == None: # bad packet...
		return

	fileRequest(packet, sock)

	clients[addr] = sock
	sock.start()
```

A verificação de existência é feita pela função *fileRequest*. Se o arquivo for inválido, um pacote *err* é enviado de volta ao cliente. Caso contrário, o arquivo é dividido em vários pacotes e os mesmos são adicionados à fila de envio. Finalmente, um pacote *end* é colocado ao final da fila.
(*server.py:23-39*).
``` python
def fileRequest(packet, sock):
	if not os.path.isfile(packet.data):
		sock.errPacket() # send error packet...
	else:
		filename = packet.data
		fp = open(filename, 'r')
		filedata = fp.read()
		fp.close()
		size = int(math.ceil(len(filedata)/PACKET_SIZE)) # how many chunks

		print "File request " + filename + " from " + str(addr)
		for i in range(size):
			start = int(i * PACKET_SIZE)
			end = int((i+1) * PACKET_SIZE)
			sock.enqueuePacket(filedata[start:end])

		sock.endPacket() # enqueue end packet after all file packets
```

#### O cliente
O servidor executa uma única *thread* para o recebimento de pacotes. Ao receber uma entrada, passa a mesma para seu *reliable_sock*, para que seja processada. Caso o pacote recebido seja válido, o *sock* o retornará, caso contrário, retornará **None**. Com o pacote processado, o cliente agora verifica se o mesmo é um pacote de erro, fim da transmissão ou de dados. No primeiro caso, o arquivo requerido não foi encontrado, portanto, requere um novo nome ao usuário e o faz o pedido pedido ao servidor. No segundo caso, o arquivo foi totalmente transferido, assim, o cliente junta todos os blocos recebidos, imprime o resultado na tela e também gera um arquivo com o mesmo. Por fim, o pacote é apenas uma fração do arquivo, então é somada aos blocos recebidos e a *thread* aguarda um novo pacote.
(*client:45-71*).

``` python
def recvFile(filename, client, sock):
	data = ''
	# loop until all packages have been received
	while True:
		# receives the package and stores in 'reply'.
		reply, addr = client.recvfrom(1024)	
		packet = sock.receivePacket(reply)

		if packet == None:
			continue

		if (packet.err > 0): # file not found
			filename = raw_input("Server doesn't have this file! Choose another one: ")
			sock.enqueuePacket(filename)
			continue
		if (packet.end > 0): # check if its the last package
			print "EOF received, printing file:"
			break
		else: # store packet data in data list
			print "Appending " + str(len(packet.data)) + " bytes received from server"
			data += packet.data

	f = open(filename, 'w+') # create or overwrite file
	f.write(data)
	f.close()
	
	print data

```

#### O pacote
Este arquivo é responsável por facilitar o manuseio das informações de cabeçalho de cada pacote, a compilação para uma string e a decomposição de um pacote recebido (string completa) em um objeto *Packet*.
(*packet:15-22*).
``` python
def __init__ (self, data, seg = 0, ack = 0, end = 0, err = 0, con = 0):
		self.data = data
		self.seg = seg
		self.ack = ack
		self.checksum = self.get_CRC32(data)
		self.end = end
		self.err = err
		self.con = con
```

#### O socket confiável
O *reliable_sock* é implementado de forma genérica, de modo que seja usado tanto pelo cliente quanto pelo servidor. Dessa forma, uma comunicação bidirecional pode acontecer entre eles e apenas as particularidades de um cliente e um servidor precisam ser implementadas à parte, ou seja, não há necessidade de repetir a lógica do *socket* entre ambos.

O *sock* é composto por alguns estados: *init(ialized)*, end e requesting.

O *init* controla se o socket está inicializado e, caso não esteja, um pacote com o cabeçalho *con* é enviado.
O *end* controla se o socket está finalizado e, caso seja, interrompe a *thread* de envio de pacotes.
O *requesting* indica se o socket requisitou ou foi requisitado pela conexão. Serve para indicar se ao receber um pacote de *con*, deve interpretá-lo como *ACK* ou responder com um *ACK*.
(*reliable_sock:15-17*).
``` python
self.init = False
self.end = False
self.requesting = False
```

Para diferenciar pacotes enviados de pacotes em espera, o *sock* possui 2 *Queues* (filas) ordenadas por prioridade. A prioridade dos pacotes é obtida de acordo com o *segnum* de cada uma, dessa forma, há sempre a ordenação:
* ACKs
* Pacotes para reenvio
* Pacotes não enviados

Essa ordem é obtida pois os *ACKs* possuem *segnum*=0 e pacotes enviados seguramente tem *segnum* inferior a pacotes não enviados.
(*reliable_sock:32-38*).
``` python
		# PQueue will sort packets by segnum, so when inserting in queue, packets will be like:
		# Acks - segnum = 0
		# Failed packets (for their segnum is securely < unset packets)
		# Unsent packets
		# So ordering is guaranteed and ACKs should be sent immediately
		self.buff = PQueue() # packets to send
		self.waiting = PQueue(cwnd) # packets wating for ACK
```

A execução do *sock* é regulada por 2 *threads*. A primeira é um *loop* responsável por enviar os pacotes da fila (até que o fim da janela seja atingido) e a segunda representa um *timer* para acusar *timeouts* nos pacotes enviados e forçar seu reenvio.

O *timer* está sempre em execução até que a flag *end* seja habilitada. Uma vez que um *timeout* é chamado, os pacotes da *queue waiting* são movidos para a *queue buff* para reenvio e o *timer* é reiniciado. Há de se ressaltar que pacotes cujo *segnum* é inferior ao *ACK* esperado são descartados, pois a janela já foi movimentada, ou seja, o *ACK* para os mesmos já foi recebido. Um *lock* é necessário nesse passo para que a *thread* de envio aguarde essa transferência entre filas, caso contrário, os pacotes transferidos para a *queue buff* possivelmente serão inseridos de novo na *queue waiting*, causando um loop infinito de transferência entre as *queues*.
(*reliable_sock:80-102*).
``` python
		def playTimer(self):
		if self.timer != None:
			self.timer.cancel() # stop current timer

		self.timer = threading.Timer(ACK_TIMEOUT, self.timeout)
		self.timer.start()

	def timeout(self):
		if not self.end and not self.waiting.empty():
			print "Timed out! Enqueuing window again..."
		self.lock.acquire(True) # block other thread
		self.attempt += 1 # should this avoid dced socket to be maintained

		# expected ack didn't arrive... send window again!
		
		while not self.waiting.empty():
			packet = self.waiting.get()
			if packet.seg >= self.ack: # no need to resend acked packets...
				self.buff.put(packet)
			self.waiting.task_done()
		self.lock.release()
		if not self.end:
			self.playTimer()
```
A *thread* de envio, por sua vez, é executada quando o cliente ou servidor chamam o método *start* no *sock*. Esse método executa um *loop* até que a flag *end* seja ativada. Primeiro, um pacote é retirado da *queue buff* para que seja enviado, mas caso não haja pacote disponível, a execução é bloqueada pela própria *queue* até que haja algum pacote. Em seguida, o *timer* é disparado caso ainda não esteja em execução.

Apenas pacotes de dados devem ser reenviados, então há uma verificação do pacote e, caso possa requerer reenvio, a *thread* bloqueia o *lock* e desbloqueia logo em seguida para então adicionar o pacote na *queue waiting*. O passo de bloqueio-desbloqueio é essencial para que caso o procedimento de *timeout* esteja em execução, a *thread* de envio aguarde a transferência entre *queues*. A janela de envio é controlada pela *queue waiting*, pois a mesma é inicializada com um tamanho máximo e, quando o mesmo é atingido, a *queue* bloqueia a *thread* até que os pacotes sejam retirados da fila (pelo *timeout* ou por *ACKs*). Dessa forma, *ACKs* não ficam sujeitos à janela e nem causam seu bloqueio.

Enfim, a *thread* faz o envio efetivo do pacote, mas não sem antes considerar uma possível simulação de falha no envio. Caso decida simular uma falha, o envio não acontece.

Finalmente, a *thread* verifica se o pacote enviado é do tipo *end* e *ack*, ou seja, confirmação de término de envio ou se o limite de tentativas de envio sem resposta foi atingido e habilita a flag *end* do *sock*. Esse limite de envio se faz necessário quando o cliente consegue receber todos os pacotes até o *end* (e portanto, termina!), mas algum de seus *acks* não chega ao outro lado do *sock*, causando reenvios infinitos dos pacotes já recebidos. Para evitar essa situação, o *sock* contabiliza os *timeouts* e encerra após o valor definido em *ATTEMPT*. Se um pacote for recebido pelo *sock*, a contagem é zerada, pois indica que há conexão.
(*reliable_sock:44-71*).
``` python
	def start(self):
		while not self.end:
			packet = self.buff.get(True) # block until another packet is added
			if self.timer == None:
				self.playTimer()	
			# only regular packets should be recent. 
			# acks require the other side of the socket to be sent again, so we don't need to put on waiting queue

			if packet.ack == 0 and (self.requesting or packet.con == 0):
				self.lock.acquire(True) # wait for timeout function if needed
				self.lock.release() # release it BEFORE put function or it will deadlock
				self.waiting.put(packet) # block after timer!
				print "Sending seg " + str(packet.seg) + " to " + str(self.addr) # don't log ack/con for they are logged somewhere 				else		

			# inform Queue we're done with the packet we got
			self.buff.task_done()
			
			if random.randint(1, 100) < self.ploss:
				print "Simulating delayed packet"
				continue # simulate lost packet
	
			self.sock.sendto(packet.wrap(), self.addr)

			if packet.end:
				print "Sending connection end"

			if (packet.end and packet.ack) or self.attempt >= ATTEMPT: # should this avoid dced socket to be maintained
				self.endCon()
```

O recebimento de pacotes é controlado pela *thread* do servidor, não estando sujeita ao bloqueio de envio. A primeira tarefa executada é a verificação do *checksum* ou simulação de um pacote corrompido.

Se o pacote é (considerado) válido, então há a diferenciação do tratamento de acordo com seu cabeçalho:
1. Um pacote com o cabeçalho *con* marca o *sock* como inicializado e, caso o *sock* não seja aquele que requisitou a conexão, um *ACK* é enviado.
2. Um pacote com o cabeçalho *ack* bloqueia o *lock* para evitar discarte indevido de pacotes no *timeout* e, caso seja o *ACK* esperado, move a janela e reinicia o *timer*. Se a flag *end* do pacote estiver habilitada, então a flag *end* do *sock* também é, pois o pacote simboliza a confirmação do pacote de término.
3. Um pacote com o *segnum* inferior ao *segnum* esperado significa que o outro lado do *sock* não recebeu o *ACK* do pacote em questão e portanto o reenviou. Assim o pacote recebido é ignorado e o *ACK* é reenviado.
4. Um pacote com *segnum* igual ao *segnum* esperado causa um incremento no *segnum* esperado, pois o pacote é aquele que deve ser recebido e o envio do *ACK* do pacote.
5. Os demais pacotes são ignorados, por exemplo, pacotes cujo *segnum* é maior do que o esperado, ou seja, chegaram fora de ordem.

Finalmente, o pacote (ou None) é retornado para a *thread* que chamou a função: o servidor ou o cliente.
(*reliable_sock:128-1708*).
``` python
	def receivePacket(self, data):
		packet = Packet(data)
		packet.unwrap()

		self.attempts = 0

		if not packet.validChecksum() or random.randint(1, 100) < self.pcorr: # do not receive broken packets or simulate a broken packet
			print "Bad checksum received on seg: " + str(packet.seg) + " ack: " + str(packet.ack)
			return None

		if packet.con > 0:		
			self.seg = packet.con # set seg with nextSeg received in con field
			self.ack = packet.con
			self.init = True
			if not self.requesting: # this socket received the connection request, then ack it
				print "Connection request from " + str(self.addr)
				self.buff.put(Packet('', end = packet.end, con = self.nextSeg)) # ack with nextSeg expected on con field
				return packet
			else:
				print "Connection established!"
		elif (packet.ack > 0): # ack packet
			self.lock.acquire(True)

			if packet.ack == self.ack: # expected ack!
				self.ack += 1
				self.playTimer() # ack received, start timer again
		 		print "Received expected ack " + str(packet.ack) + " on connection " + str(self.addr)

				if packet.end: # ack for end packet received
					self.endCon()
			self.lock.release()
		elif packet.seg < self.nextSeg:
			self.ackPacket(packet.seg, packet.end) # old packet received again, ACK might be lost.. send it again
			print "Duplicated packet " + str(packet.seg) + ". Sending ack again and ignoring"
		elif self.nextSeg == packet.seg: # expected seg!
			self.nextSeg += 1
			self.ackPacket(packet.seg, packet.end)
			print "Acking packet " + str(packet.seg)
			return packet
		#else:
		#	print "Bad packet received! Seg: " + str(packet.seg) + " expected: " + str(self.nextSeg) + " ack: " + str(packet.ack)
		
		return None
```

<br>
### Testes realizados

		Nas imagens abaixo apresentamos algumas das execuções correspondentes aos testes feitos. Nelas podemos observar pacotes duplicados, erros de checksum, pacotes atrasados quando passados os respectivos parâmetros.

* Teste realizado sem pacotes perdidos ou corrompidos (ploss: 0; % pcorr: 0): <br>

		Client:

	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/cliente-10-0-0.jpg)

		Server:

	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/server-10-0-0.jpg) <br> <br> 


* Teste realizado com porcentagem de pacotes corrompidos de 20%: <br>

		Client:

	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/client-10-0-20.jpg)

		Server:

	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/server-10-0-20.jpg)

	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/server-10-0-20-1.jpg) <br> <br>

* Teste realizado com porcentagem de pacotes perdidos de 20%: <br>

		Client:

	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/client-10-20-0.jpg)<br>

		Server:

	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/server-10-0-20.jpg) 
	
	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/server-10-0-20-1.jpg)  <br> <br>

* Teste realizado com porcentagem de pacotes perdidos de 15% e corrompidos 15%: <br>

		Client:
	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/client-10-15-15.jpg)

		Server:
	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/server-10-15-15.jpg)

	![alt text](https://raw.githubusercontent.com/VictorJuliani/Redes/master/projeto2/Pictures/server-10-15-15-1.jpg) <br> <br>


### Dificuldades encontradas

		A primeira dificuldade foi perceber que a melhor forma de projetar a confiabilidade seria através de um modelo genérico (*reliable_sock*) para o servidor e para o cliente. Implementamos no início toda a lógica de controle nos scripts de server e cliente. Isso foi solucionado criando o *reliable_sock* para a comunicação.
		A segunda dificuldade foi projetar o bloqueio da *thread* de envio. Havia a dúvida entre o uso de um *deque* (fila não bloqueante) e a *Queue*. Depois de algumas inversões entre elas, foi optado pelo uso da *Queue* por nao necessitar de *locks* adicionais no momento em que foi possível executar a conexão, transferência de dados e *ACKs* e finalização da conexão coom sucesso sem o uso de um *timeout* ou de falhas de envio ou corrupção.
		Finalmente, mas não menos trabalhoso (pelo contrário!) a implementação das falhas e do *timeout* levantou uma série de falhas no *sock*, especialmente no que se refere ao bloqueio das execuções das *threads* para evitar loops infinitos ou *deadlocks*. Através de *debugs* para identificar onde os *deadlocks* e inconsistências aconteciam , o script foi ajustado gradualmente até que chegasse ao ponto atual: funcionando! O *sock* do emissor nunca fica enviando pacotes para um cliente já desconectado e ambos os *socks* não ficam travados em nenhum ponto da execução. Um *timeout* curto foi usado para acelerar os testes.

