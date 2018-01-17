/*
 * Description:
 * 1. (TCP) Peers join actions
 * 		a) peer 13 wants to join DHT, and it only knows about peer 1
 * 		b) peer 13 sends message to peer 1, asking who will be my predecessor and successor?
 * 		c) then the message from peer 13 will be forwarded through the DHT, until it reaches peer 12
 * 		d) peer 12 realises it will be peer 13's predecessor and its current successor, peer 15, will become 
 * 			its successor
 * 		e) then peer 12 sends this predecessor and successor information to peer 14
 * 		f) now peer 13 can join the DHT by making peer 15 its successor, and by notifying peer 12 that it should
 * 			be its immediate successor to peer 14
 * 
 * 2. Peer tracking is based on port number, not IP address, and using a automatically PING mechanism to determine
 * 		whether the two successors of a peer are still alive
 * 
 * 3. DHT set-up command: 
 * 		xterm -hold -title "peer 12" -e "java cdht_ex 12 15 1"
 * 			12: the identity of the peer to be initialised (the identity of peer range is [0, 255])
 * 			15 & 1: identity of the two successive peers
 * 
 * 4. (UDP) The PING mechanism
 * 		a) After initialisation, peer starts pinging its two successors automatically.
 * 		b) When a peer receives a message, it will display an output on the terminal (assume is peer 10 receives 
 * 			it from peer 5):
 * 				"A ping request message was received from Peer 5."
 * 		c) And peer 10 will send a echoReply message back to peer 5, then peer 5 will display like this:
 * 				"A ping response message was received from Peer 10."
 * 		Notice 1: PING frequency is decided my me, but should not send them too often
 * 		Notice 2: PING is based on UDP, and peer i would listen on UDP port 50000 + i for echoRequest.
 * 
 * 5. (TCP) File transaction details
 * 		a) File name is defined as abcd, each letter mapped to an integer in the range [0, 9]
 * 		b) The HASH of a file is the remainder when file name is divided by 256 (e.g, a file name is "2012", so
 * 			the HASH of the file is 2012 % 256 = 220
 * 		c) File location is depend on the HASH result n, stored in the peer that is the closest successor of n
 * 		d) Request & Response message are sent when file transaction occurs. Peer A needs a file, it will sends a 
 * 			Request to its successors.
 * 				"File request message for 2012 has been sent to my successor."
 * 		e) This message will be passed through the DHT until it reaches the peer which has the file (peer B)
 * 				"File 2012 is not stored here."
 *				"File request message has been forwarded to my successor."
 * 		f) Then the peer B (Responding peer) will send a Respond message back to peer A
 *				"File 2012 is here."
 *				"A response message, destined for peer 8, has been sent."
 *		g) Peer A will display a message too after receive the response from peer B
 *				"Received a response message from peer 1, which has the file 2012."
 * 		Notice: Peer i would listen on TCP port 50000 + i for Request message
 * 
 *  6. (TCP) Peer gracefully leaves DHT
 * 		a) the graceful leaving is done by standard input "quit", then the peer should send a departure message 
 * 			to its predecessors (assume peer 10 is leaving, and peer 8 & 5 are predecessors)
 * 		b) Then peer 10 will also inform peer 8 and 5, that the successors of itself (peer 12 & 15)
 * 		c) After peer 8 & 5 have received the departure message, they should output the line to the terminal:
 * 				"Peer 10 will depart from the network."
 * 		d) Then peer 8 & 5 will update their successors, using peer 8 as example, learning from peer 10's leaving 
 * 			message, it will then make peer 12 its first successor and peer 15 its second successor, and display 
 * 			following text:
 * 				"My first successor is now peer 12."
 * 				"My second successor is now peer 15."
 * 		e) Peer 5 does the similar things
 * 		f) After they finish setting up new successors, peer 8 & 5 will start PINGing their successors automatically
 * 		g) When the convergence of DHT, the File transaction mechanism will also changed (e.g, file 0266, whose 
 * 			HASH is 10, should be on peer 12, rather than peer 10)
 * 		Notice 1: Peer i would listen on TCP port 50000 + i for Request message
 * 		Notice 2: After peer A has sent the departure message to two predecessors, it should make sure that 
 * 			predecessors have received the message before terminating the DHT program
 * 		Notice 3: After the leaving of peer 10, the new successors are deduced from the leaving message, no from 
 * 			the learning mechanism (e.g peer 8 knows peer 12 & 15 directly from the leaving message of peer 10, 
 * 			from PING)
 * 		
 *  7. (TCP) Peer suddenly leaves DHT (EXTENDED)
 * 		a) Using peer 5 as example, after peer 5's crash, its predecessors (peer 3 & 4) will soon detect the 
 * 			failure of itself (the discovering time depending on the frequency of PING), and they should display 
 * 			the text:
 * 				"Peer 5 is no longer alive."
 * 		b) Peer 4 will change it second successor as first successor (because peer 5's failure)
 * 				"My first successor is now peer 8."
 * 		c) Peer 4 then sends a message to peer 8 to ask for peer 8's first successor, AKA peer 4's second successor. 
 * 			Peer 8 will reply to peer 4 its first successor (peer 12, as peer 10 left DHT gracefully before), and 
 * 			peer 4 should display such text:
 * 				"My second successor is now peer 12."
 * 		d) Peer 3 does the similar things
 * 		e) After they finish setting up new successors, peer 3 & 4 will start PINGing their successors automatically
 * 		Notice: Peer i would listen on TCP port 50000 + i for the successor asking message
 * 
 *  8. Other notable details
 *  	a) A sequence number field should be included in the PING message
 *  	b) Three important parameters should be considered:
 *  		The NUMBER of consecutive failures in responding PING request
 * 			The FREQUENCY of PING message
 * 			The WAITINGTIME (AKA TIMEOUT) in keeping waiting until a PING failure
 */

import java.io.*;
import java.net.*;
import java.util.*;


public class cdht_ex { //class cdht_ex will run DHT, along with the other 4 threads
	public static int peerN;
	public static int successor1 = 0;
	public static int successor2 = 0;
	
	public static void main (String[] args) throws SocketException { //args[0] is peer number, args[1]&[2] are successors
		peerN = Integer.parseInt(args[0]);
		successor1 = Integer.parseInt(args[1]);
		successor2 = Integer.parseInt(args[2]);
		DatagramSocket udpServerSocket = new DatagramSocket(50000 + peerN);
		//DatagramSocket udpClientSocket = new DatagramSocket();
		udpServerSocket.setSoTimeout(8000);
		ServerSocket tcpServerSocket = null;
		try {
			tcpServerSocket = new ServerSocket(50000 + peerN);
		} catch (IOException e) {}
		
		DHT newDHT = new DHT(peerN, successor1, successor2, udpServerSocket, tcpServerSocket);
		newDHT.start();
	}
}

/*********************************************************************************
 * 										*
 *  					DHT				 	*
 *  										*
 *  										*
 *********************************************************************************/
//class DHT will run 4 threads: UDP_PING_Server, UDP_PING_Client, TCP_Server, TCP_Client
class DHT extends Thread{
	boolean pingTrigger = true; //used for PING timer
	int pingfreqTime = 2000;
	boolean confirm1 = false;
	boolean confirm2 = false;
	boolean confirm3 = false;
	boolean confirm4 = false;
	
	boolean SYSTEM_RUN = true;
	public int peerN;
	public int successor1 = -1; //successor1 is the first successor, while the successor2 is the second
	public int successor2 = -1;
	public static int predecessor1 = -1;
	public static int predecessor2 = -1;
	int successorLost1 = 0;
	int successorLost2 = 0;
	DatagramSocket udpServerSocket; //for client sending packet only
	ServerSocket tcpServerSocket;
	//DatagramSocket udpClientSocket; //for receiving packet from server/client
	boolean firstNode = false; //predecessors are all larger than itself
	boolean secondNode = false; //predecessor2 is larger than it itself
	boolean lastNode = false; //successors are all smaller than itself
	boolean penultimateNode = false; //successor2 is smaller than it self
	boolean successorFull = true;
	boolean predecessorFull = false;
	boolean stateFull = false;
	int successorCounter = 2;
	
	public DHT (int peerN, int successor1, int successor2, DatagramSocket udpServerSocket, ServerSocket tcpServerSocket) {
		this.peerN = peerN;
		this.successor1 = successor1;
		this.successor2 = successor2;
		this.udpServerSocket = udpServerSocket;
		//this.udpClientSocket = udpClientSocket;
		this.tcpServerSocket = tcpServerSocket;
	}

	public void run () {
		//PingTimer timer = new PingTimer();
		UDP_PING_Server pingServer = new UDP_PING_Server();
		UDP_PING_Client pingClient = new UDP_PING_Client();
		TCP_Server tcpServer = new TCP_Server();
		TCP_Client tcpClient = new TCP_Client();
		
		//timer.start();
		pingServer.start(); //pingServer will initialise the predecessors
		pingClient.start();
		tcpServer.start(); //pingClient will use predecessors
		tcpClient.start();
	}	

	/*********************************************************************************
	 * 										*
	 *  				     PING SERVER				*
	 *  										*
	 *  										*
	 *********************************************************************************/
	class UDP_PING_Server extends Thread {
		int incomingP = -1;
		int incomingN = -1;
		String request = new String("request");
		String response = new String("response");
		String operationCode = new String();
		//server waits for the echoRequests from clients, and sends echoReply to the client
		//server's responsibility is simple: keep listening to the port, and reply to the response
		public void run () {
			//server does an infinite loop in waiting echoRequest from clients
			while (!confirm1 || !confirm2 || !confirm3 || !confirm4) {
				InetAddress serverAddress = null;
				try {
					serverAddress = InetAddress.getLocalHost();
				} catch (UnknownHostException e2) {}
				InetAddress clientAddress = null;
				String serverMessage = null;
				//create a DatagramPacket "echoListen" to hold incoming UDP packet, until the host receives a UDP packet, and print the received data
				DatagramPacket serverListen = new DatagramPacket(new byte[1024], 1024);
				try {
					udpServerSocket.receive (serverListen);
					clientAddress = serverListen.getAddress();
					incomingP = serverListen.getPort();
					incomingN = incomingP - 50000;
		         	String incomingSeq = messageAnalyser(serverListen, incomingN);
		         	if (operationCode.equals(request)) { //print the request message and reply to client
			         	System.out.println ("A ping request message was received from Peer " + incomingN + ".");
						predecessorAnalyser (incomingN);
			         	serverMessage = incomingSeq + ":" + response + ":end";
						byte[] serverData = serverMessage.getBytes();
						//construct a new DatagramPacket "echoReply" for replying to client
						DatagramPacket echoReply = new DatagramPacket(serverData, serverData.length, clientAddress, incomingP);
						try {
							udpServerSocket.send(echoReply);
						} catch (IOException e) {}
					}
					if (operationCode.equals(response)) {
						System.out.println ("A ping response message was received from Peer " + incomingN + ".");
						if (incomingN == successor1) {
							successorLost1 = 0;
							++ successorLost2;
						}
						else if (incomingN == successor2) {
							successorLost2 = 0;
							++ successorLost1;
						}
					}
				} catch (Exception e) {}
				//when packet lost happens, check the successive lost number
				//the situation that successor1 is died
				//in the example, I am peer 8, and peer 10 is died
				//I need to make peer 12 as my first successor, and ask peer 12 for its first successor (peer 15)
				//to be my new second successor
				// to determine a lost peer, the successorlost is "5"
				if (successorLost1 == 6) {
					successorFull = false; //node has only one successor now
					System.out.println("Peer " + successor1 + " is no longer alive.");
					successor1 = successor2;
					System.out.println("My first successor is now peer " + successor1 + ".");
					//initialising TCP connection
					Socket peerfindingSocket = null;
					try {
						peerfindingSocket = new Socket (serverAddress, successor1 + 50000);
					} catch (IOException e1) {}
					DataOutputStream outToServer = null;
					try {
						outToServer = new DataOutputStream (peerfindingSocket.getOutputStream());
					} catch (IOException e1) {}
					//send this message to the new successor1, require the successor1 of the new successor1 to be the new successor2
					String sentSentence1 = "requiresuccessor1" +
							":" + Integer.toString(peerN) + 
							":" + Integer.toString(predecessor1) + 
							":end";
					try {
						outToServer.writeBytes(sentSentence1);
					} catch (IOException e1) {}
					try {
						peerfindingSocket.close();
					} catch (IOException e1) {}
					successorLost1 = 0;
				} // end of if
			} // end of big while
		} // end of run
		
		// this method returns the client sent sequence number, and read the operation code
		public String messageAnalyser (DatagramPacket echoRequest, int peerN) throws Exception {
			byte[] echoReplyData = echoRequest.getData();
			//wrap the bytes in a ByteArrayInputStream, so can read the data as a stream of bytes
			ByteArrayInputStream baisData = new ByteArrayInputStream(echoReplyData);
			//wrap the byte array output stream in an InputStreamReader, so can read the data as a stream of characters
			InputStreamReader isrData = new InputStreamReader(baisData);
			//wrap the InputStreamReader in a BufferedReader, so can read the character data a line at a time
			BufferedReader fromClientData = new BufferedReader(isrData);
			String sentence = fromClientData.readLine();
			String splitSentence[] = sentence.split(":");
			operationCode = splitSentence[1];
			return splitSentence[0];
		}
		
		public void predecessorAnalyser (int clientN) {
			if (clientN != -1) { // if clientN is a valid peer Number
	         	if (predecessor1 == -1 && predecessor2 == -1) // if there is no predecessor now
	         		predecessor1 = clientN;
	         	else if (predecessor1 != -1 && predecessor2 == -1 && predecessor1 != clientN) // if predecessor2 is empty and predecessor1 is not clientN
	         		predecessor2 = clientN;
	         	else if (predecessor1 == -1 && predecessor2 != -1 && predecessor2 != clientN) // if predecessor1 is empty and predecessor2 is not clientN
	         		predecessor1 = clientN;
			}
			if (predecessor1 >= 0 && predecessor2 >= 0 && successor1 >= 0 && successor2 >= 0) { // means the peer is full, with 2 predecessors and 2 successors
				predecessorFull = true;
				nodeTypeAnalyser();
			}
		}
		
		public void nodeTypeAnalyser () {
			if (predecessor1 > peerN && predecessor2 > peerN) { //the firstNode, two predecessors are larger than peerN
				firstNode = true;
				if (predecessor1 < predecessor2) {
					int temp;
					temp = predecessor2;
					predecessor2 = predecessor1;
					predecessor1 = temp;
				}
			}
			else if ((predecessor1 > peerN && predecessor2 < peerN) || (predecessor1 < peerN && predecessor2 > peerN)) { //the secondNode, one predecessor is larger than peerN
				secondNode = true;
				if (predecessor1 > predecessor2) {
					int temp;
					temp = predecessor2;
					predecessor2 = predecessor1;
					predecessor1 = temp;
				}
			}
			else {
				if (predecessor1 < predecessor2) {
					int temp;
					temp = predecessor2;
					predecessor2 = predecessor1;
					predecessor1 = temp;
				}
			}
			if (successor1 < peerN && successor2 < peerN) { //the lastNode, peerN is larger than the two successors
				lastNode = true;
				if (successor1 > successor2) {
					int temp;
					temp = successor2;
					successor2 = successor1;
					successor1 = temp;
				}
			}
			else if ((successor1 < peerN && successor2 > peerN) || (successor2 < peerN && successor1 > peerN)) {//the penultimateNode, peerN is larger than one of the two successors
				penultimateNode = true;
				if (successor1 < successor2) {
					int temp;
					temp = successor2;
					successor2 = successor1;
					successor1 = temp;
				}
			}
			else {
				if (successor1 > successor2) {
					int temp;
					temp = successor2;
					successor2 = successor1;
					successor1 = temp;
				}
			}
		}


	}  //end of class UDP_PING_Server
	

	/*********************************************************************************
	 * 										*
	 *  				     PING CLIENT				*
	 *  										*
	 *  										*
	 *********************************************************************************/
	//client sends the echoRequests to servers, and waits for echoReply from the server. A PING client will also 
	//responsible for checking the sequence number in return packets
	//A client has to the following jobs:
	//		1. sending echoRequest to servers at a constant rate (e.g, 1 packet per second)
	//		2. waiting for the echoResponse from the server, until the timer runs to "0" (PING failed), or a new 
	//			echoResponse message arrives
	//		3. If a client doesn't receive 4 packets in a row, (4s, timer runs to 0) then the server is down
	
	class UDP_PING_Client extends Thread {
		boolean pingTimer;
		String request = new String("request");
		String response = new String("response");
		String operationCode = new String();
		
		public void run () {

			InetAddress serverAddress = null;
			try {
				serverAddress = InetAddress.getLocalHost();
			} catch (UnknownHostException e2) {}
			
			//client does an infinite loop in sending echoRequest to servers
			int i = 0;
			int seq = 0;
			while (!confirm1 || !confirm2 || !confirm3 || !confirm4) {
				if (true) {
					int sentSeq;
					byte[] sendData;
					String clientMessage;
					
					if (seq == 9999)
						seq = 0;
					sentSeq = seq;
					++ seq;
					clientMessage = Integer.toString(sentSeq) + ":" + request + ":end";
					sendData = new byte[1024];
					sendData = clientMessage.getBytes();

					for (i = 0; i < successorCounter; i ++) { //successorCounter can be 1, or 2, actually successorCounter is always 2
						if (i == 0) { //send ping to first successor
							DatagramPacket clientSend = null;
							clientSend = new DatagramPacket(sendData, sendData.length, serverAddress, 50000 + successor1);
							try {
								udpServerSocket.send(clientSend);
							} catch (IOException e) {}
						}
						if (i == 1) { //send ping to second successor	
							DatagramPacket echoRequest = null;
							echoRequest = new DatagramPacket(sendData, sendData.length, serverAddress, 50000 + successor2);
							try {
								udpServerSocket.send(echoRequest);
							} catch (IOException e) {}
						}		
					}
					i = 0;
				 } // end of timer's if
				try {
					Thread.sleep(4000);
				} catch (InterruptedException e) {}
			} //end of big while
		} // end of big run
	} //end of class UDP_PING_Client

	
	/*********************************************************************************
	 * 										*
	 *  					PING TIMER				*
	 *  			   failed part, changed to thread sleep			*
	 *  										*
	 *********************************************************************************/
	
	// timer is working, but the "true" state keeps too long the the ping client can sends multi messages
	// during the time of "true"
	class PingTimer extends Thread { //an infinite loop time, change the value of a global parameter
		public void run() {
			final Timer timeFreq = new Timer();
			timeFreq.scheduleAtFixedRate (new TimerTask() {
				public void run() {
					timerRunner ();
    				if(SYSTEM_RUN == false)
    					timeFreq.cancel();
				}
			}, 0, 1);
		}
		
		//this method will do an infinite loop
		public void timerRunner () {
			if (pingfreqTime == 0) {
				pingfreqTime = 2000;
				pingTrigger = true;
			}
			else {
				--pingfreqTime;
				pingTrigger = false;
			}
		}
		
	} //end of class PingTimer


	/*********************************************************************************
	 * 										*
	 *  				      TCP SERVER				*
	 *  										*
	 *  										*
	 *********************************************************************************/
	class TCP_Server extends Thread {
		int fileN;
		int hash;
		int requestFromClient = 1;
		int forwardedByServer = 2;
		int forwardedToServer = 2;
		int hasFile = 3;
		int operationCode = 0;

		boolean file = false;
		
		public void run () {
			while (!confirm1 || !confirm2 || !confirm3 || !confirm4) {
				String clientSentence = null;
				String sentSentence;
				InetAddress clientAddress = null;
				InetAddress serverAddress;
				Socket listenSocket = null;
				try {
					listenSocket = tcpServerSocket.accept();
				} catch (IOException e1) {}
				BufferedReader inFromClient = null;
				try {
					inFromClient = new BufferedReader (new InputStreamReader (listenSocket.getInputStream()));
				} catch (IOException e1) {}
				try {
					clientSentence = inFromClient.readLine();
				} catch (IOException e1) {}
				clientAddress = listenSocket.getInetAddress();
				serverAddress = listenSocket.getInetAddress();
				
				int clientP = -1;
				int clientN = -1;
				int predecessorP = -1;
				int predecessorN = -1;
				String fileMessage = null;
				String quitMessage = null;
				String predecessorMessage = null;
				String splitFileMessage[] = null;
				String splitQuitMessage[] = null;
				String splitSentence[] = clientSentence.split(":");
				if (splitSentence[0].equals("request") || splitSentence[0].equals("Request")) { //start processing file searching
					fileMessage = clientSentence;
					splitFileMessage = fileMessage.split(":");
					fileN = Integer.parseInt(splitFileMessage[1]);
					hash = fileN % 256;
					operationCode = Integer.parseInt(splitFileMessage[2]); //to determine the source of the file request
					
					clientN = Integer.parseInt(splitFileMessage[3]);
					clientP = clientN + 50000;
					// generate the sentSentence
					if (peerN == hash) { //the file is here, type1 (hash == peerN)
						sentSentence = "file:" + Integer.toString(fileN) + 
								":" + Integer.toString(hasFile) + 
								":" + Integer.toString(peerN) + 
								":end";
						file = true;
					}
					else if (peerN > hash && predecessor1 <= hash && predecessor2 <= hash) { //the file is here, type2 (hash < peerN)
						sentSentence = "file:" + Integer.toString(fileN) + 
								":" + Integer.toString(hasFile) + 
								":" + Integer.toString(peerN) + 
								":end";
						file = true;
					}
					else if (peerN > hash && predecessor1 <= hash && predecessor2 > hash) { //the file is here, type2 (hash < peerN)
						sentSentence = "file:" + Integer.toString(fileN) + 
								":" + Integer.toString(hasFile) + 
								":" + Integer.toString(peerN) + 
								":end";
						file = true;
					}
					else if (firstNode && hash > predecessor1 && hash > predecessor2) { //the file is here, type3 (very large hash in the first peer)
						sentSentence = "file:" + Integer.toString(fileN) + 
								":" + Integer.toString(hasFile) + 
								":" + Integer.toString(peerN) + 
								":end";
						file = true;
					}
					else { // file is not here
						sentSentence = "request:" + Integer.toString(fileN) + 
								":" + Integer.toString(forwardedToServer) + 
								":" + Integer.toString(clientN) + 
								":end";
						file  = false;
					}
					//the response message is like:
					//"2012:2:50232:end", means request will be forwarded by this server
					//"2012:3:50232:end", means here has file, note the client
					//if the message is received from client or from another server, and the file is here, just reply to the client
					if (file == true) { //if file is here, respond to client directly
						Socket replyToClient = null;
						try {
							replyToClient = new Socket (clientAddress, clientN + 50000);
						} catch (IOException e) {}
						//this socket is used as a sender to client/server
						DataOutputStream outToClient = null;
						try {
							outToClient = new DataOutputStream (replyToClient.getOutputStream());
						} catch (IOException e) {}
						String replyMessage = sentSentence;
						try {
							outToClient.writeBytes(replyMessage);
						} catch (IOException e) {}
						try {
							replyToClient.close();
						} catch (IOException e) {}
						System.out.println ("File " + fileN + " is here.");
						System.out.println ("A response message, destined for Peer " + clientN + ", has been sent.");
					}
					//if there is no file, forwarding the message to the first successor
					if (file == false) {
						Socket forwardToServer = null;
						try {
							forwardToServer = new Socket (clientAddress, successor1 + 50000);
						} catch (IOException e) {} //this socket is used as a sender to client/server
						DataOutputStream outToServer = null;
						try {
							outToServer = new DataOutputStream (forwardToServer.getOutputStream());
						} catch (IOException e) {}
						String forwardMessage = sentSentence;
						try {
							outToServer.writeBytes(forwardMessage);
						} catch (IOException e) {}
						try {
							forwardToServer.close();
						} catch (IOException e) {}
						System.out.println ("File " + fileN + " is not stored here.");
						System.out.println ("File request message has been forwarded to my successor.");
					}
				} //end of file operation part
				
				else if (splitSentence[0].equals("file")) {
					int filenumber;
					//part of waiting for response from server, ServerSocket is fromServerResponse, defined before "while(true)"
					int serverN;
					filenumber = Integer.parseInt(splitSentence[1]);
					serverN = Integer.parseInt(splitSentence[3]);
						if (Integer.parseInt(splitSentence[2]) == hasFile) //if the operation code is hasFile
							System.out.println ("Received a response message from Peer " + serverN + ", which has the file " + filenumber + ".");
				} //end of receiving file

				//for the leaving peer peerN, 
				//message "quit:peerN:successor1:successor2:end" is for the predecessor
				//TCP SERVER will process the graceful leaving according to the incoming message, it will change its successor
				//based on the leaving message sent from client
				else if (splitSentence[0].equals("quit") || splitSentence[0].equals("Quit")) {
					quitMessage = clientSentence;
					splitQuitMessage = quitMessage.split(":");
					clientN = Integer.parseInt(splitQuitMessage[1]);
					int new1 = Integer.parseInt(splitQuitMessage[2]);
					int new2 = Integer.parseInt(splitQuitMessage[3]);
					//I am the first predecessor of the leaving peer
					//I should use the given successor in the client message as my new successor2 (need swap)
					//5 - 8 - 10 - 12 - 15, peer 10 is leaving
					//in the example, I am peer 8, use the given 15 as my new successor2, while the old successor2 12, 
					//will be my successor1
					if (clientN == successor1) { // my successor1 is leaving, change my successor1 to a new successor
						System.out.println("Peer " + clientN + " will depart from the network.");
						if (successor2 == new2)
							successor1 = new1;
						else if (successor2 == new1)
							successor1 = new2;
						int temp;
						temp = successor1;
						successor1 = successor2;
						successor2 = temp;
						System.out.println("My first successor is now Peer " + successor1 + ".");
						System.out.println("My second successor is now Peer " + successor2 + ".");
						
						String confirmation = new String("confirmation1");
						Socket confirmSocket = null; //this socket "clientSocket2" used to connect to the second predecessor
						try {
							confirmSocket = new Socket (serverAddress, clientN + 50000);
						} catch (IOException e) {}
						DataOutputStream confirm = null;
						try {
							confirm = new DataOutputStream (confirmSocket.getOutputStream());
						} catch (IOException e) {}
						try {
							confirm.writeBytes(confirmation);
						} catch (IOException e) {}
						try {
							confirmSocket.close();
						} catch (IOException e) {}
					}
					
					//I am the second predecessor of the leaving peer
					//I should use the given successor in the client message as my new successor2
					//5 - 8 - 10 - 12 - 15, peer 10 is leaving
					//in the example, I am peer 5, use the given 12 as my new successor2, while the old successor1 8, won't be changed
					else if (clientN == successor2) { // my successor2 is leaving, change my successor2 to a new successor
						System.out.println("Peer " + clientN + " will depart from the network.");
						successor2 = new1;
						System.out.println("My first successor is now Peer " + successor1 + ".");
						System.out.println("My second successor is now Peer " + successor2 + ".");
						
						String confirmation = new String("confirmation2");
						Socket confirmSocket = null; //this socket "clientSocket2" used to connect to the second predecessor
						try {
							confirmSocket = new Socket (serverAddress, clientN + 50000);
						} catch (IOException e) {}
						DataOutputStream confirm = null;
						try {
							confirm = new DataOutputStream (confirmSocket.getOutputStream());
						} catch (IOException e) {}
						try {
							confirm.writeBytes(confirmation);
						} catch (IOException e) {}
						try {
							confirmSocket.close();
						} catch (IOException e) {}
					}
					else if (clientN == predecessor1) { // my predecessor1 is leaving
						predecessor1 = predecessor2;
						predecessor2 = new2;
						
						String confirmation = new String("confirmation3");
						Socket confirmSocket = null; //this socket "clientSocket2" used to connect to the second predecessor
						try {
							confirmSocket = new Socket (serverAddress, clientN + 50000);
						} catch (IOException e) {}
						DataOutputStream confirm = null;
						try {
							confirm = new DataOutputStream (confirmSocket.getOutputStream());
						} catch (IOException e) {}
						try {
							confirm.writeBytes(confirmation);
						} catch (IOException e) {}
						try {
							confirmSocket.close();
						} catch (IOException e) {}
					}
					else if (clientN == predecessor2) { // my predecessor2 is leaving
						predecessor2 = new1;
						
						String confirmation = new String("confirmation4");
						Socket confirmSocket = null; //this socket "clientSocket2" used to connect to the second predecessor
						try {
							confirmSocket = new Socket (serverAddress, clientN + 50000);
						} catch (IOException e) {}
						DataOutputStream confirm = null;
						try {
							confirm = new DataOutputStream (confirmSocket.getOutputStream());
						} catch (IOException e) {}
						try {
							confirm.writeBytes(confirmation);
						} catch (IOException e) {}
						try {
							confirmSocket.close();
						} catch (IOException e) {}
					}
				} //end of graceful leaving
				
				//begin the process of dealing with DHT reconstruction, due to the peer sudden leave
				//upload the information of successor for another peer, which detected the sudden leave of its successors
				//inform the successor1 to change its predecessor2
				else if (splitSentence[0].equals("requiresuccessor1")) { //eg, peer 8 sends to 12			
					predecessorN = Integer.parseInt(splitSentence[1]);
					predecessorP = predecessorN + 50000;
					String replyPredecessor = "replysuccessor1:" + 
											Integer.toString(successor1) +
											":end";
					if (predecessorN == predecessor2) {
						predecessor1 = predecessorN;
						predecessor2 = Integer.parseInt(splitSentence[2]);
					}
					Socket replyPredecessorSocket = null;
					try {
						replyPredecessorSocket = new Socket (serverAddress, predecessor1 + 50000);
					} catch (IOException e1) {}
					DataOutputStream outToServer = null;
					try {
						outToServer = new DataOutputStream (replyPredecessorSocket.getOutputStream());
					} catch (IOException e1) {}
					try {
						outToServer.writeBytes(replyPredecessor); //peer 12 replies to 8
					} catch (IOException e1) {}
					try {
						replyPredecessorSocket.close();
					} catch (IOException e1) {}
					
					String informString = "changepredecessor2:" + 
										Integer.toString(predecessor1) + 
										":end";
					Socket informSuccessor1Socket = null;
					try {
						informSuccessor1Socket = new Socket (serverAddress, successor1 + 50000);
					} catch (IOException e1) {}
					DataOutputStream informSuccessor = null;
					try {
						informSuccessor = new DataOutputStream (informSuccessor1Socket.getOutputStream());
					} catch (IOException e1) {}
					try {
						informSuccessor.writeBytes(informString); //peer 12 informs 15
					} catch (IOException e1) {}
					try {
						informSuccessor1Socket.close();
					} catch (IOException e1) {}
				}
				else if (splitSentence[0].equals("changepredecessor2")) {
					predecessor2 = Integer.parseInt(splitSentence[1]);
				}
				else if (splitSentence[0].equals("replysuccessor1")) { //peer 8 received from 12
					successor2 = Integer.parseInt(splitSentence[1]);
					successorFull = true;
					System.out.println("My second successor is now peer " + successor2 + ".");
					
					String inform = "successor2lost";
					Socket informPredecessor1Socket = null;
					try {
						informPredecessor1Socket = new Socket (serverAddress, predecessor1 + 50000);
					} catch (IOException e1) {}
					DataOutputStream informSuccessor = null;
					try {
						informSuccessor = new DataOutputStream (informPredecessor1Socket.getOutputStream());
					} catch (IOException e1) {}
					try {
						informSuccessor.writeBytes(inform); //peer 8 informs peer 5 about the lost of peer 10
					} catch (IOException e1) {}
					try {
						informPredecessor1Socket.close();
					} catch (IOException e1) {}
				}
				else if (splitSentence[0].equals("successor2lost")) { //peer 5 received the inform, peer 10 lost
					successorFull = false;
					System.out.println("Peer " + successor2 + " is no longer alive.");
					System.out.println("My first successor is now peer " + successor1 + ".");
					//initialising TCP connection
					Socket peerfindingSocket = null;
					try {
						peerfindingSocket = new Socket (serverAddress, successor1 + 50000);
					} catch (IOException e1) {}
					DataOutputStream outToServer = null;
					try {
						outToServer = new DataOutputStream (peerfindingSocket.getOutputStream());
					} catch (IOException e1) {}
					//send this message to the new successor1, require the successor1 of the new successor1 to be the new successor2
					String sentSentence1 = "requiresuccessor2:" +
									Integer.toString(peerN) + 
									":end";
					try {
						outToServer.writeBytes(sentSentence1); //peer 5 sends to peer 8
					} catch (IOException e1) {}
					try {
						peerfindingSocket.close();
					} catch (IOException e1) {}
				}
				else if (splitSentence[0].equals("requiresuccessor2")) { //peer 8 received from 5
					predecessorN = Integer.parseInt(splitSentence[1]);
					predecessorP = predecessorN + 50000;
					String replyPredecessor = "replysuccessor2:" + 
											Integer.toString(successor1) +
											":end";
					Socket replyPredecessorSocket = null;
					try {
						replyPredecessorSocket = new Socket (serverAddress, predecessor1 + 50000);
					} catch (IOException e1) {}
					DataOutputStream outToServer = null;
					try {
						outToServer = new DataOutputStream (replyPredecessorSocket.getOutputStream());
					} catch (IOException e1) {}
					try {
						outToServer.writeBytes(replyPredecessor);
					} catch (IOException e1) {}
					try {
						replyPredecessorSocket.close();
					} catch (IOException e1) {}
				}
				else if (splitSentence[0].equals("replysuccessor2")) {
					successor2 = Integer.parseInt(splitSentence[1]);
					successorFull = true;
					System.out.println("My second successor is now peer " + successor2 + ".");
				}
				else if (splitSentence[0].equals("confirmation1")) {
					confirm1 = true;
				}
				else if (splitSentence[0].equals("confirmation2")) {
					confirm2 = true;
				}
				else if (splitSentence[0].equals("confirmation3")) {
					confirm3 = true;
				}
				else if (splitSentence[0].equals("confirmation4")) {
					confirm4 = true;
				}
				else {
					System.out.println("Unrecognised message received by TCP server.");
					System.out.println(clientSentence);
				}
			}
		}
		
	} //end of TCP_Server
	
	/*********************************************************************************
	 * 										*
	 *  					TCP CLIENT				*
	 *  										*
	 *  										*
	 *********************************************************************************/
	class TCP_Client extends Thread {
		int fileN;
		int hash;
		int requestFromClient = 1; //request type
		int forwardedByServer = 2;
		int forwardedToServer = 2;
		int hasFile = 3;
		int clientP = 50000 + peerN;
		boolean fileRequest = false;
		boolean gracefulLeave = false;
		
		public void run (){
			while (!confirm1 || !confirm2 || !confirm3 || !confirm4) { //waiting for input from keyboard
				String clientOrder;
				String splitSentence[];
				Scanner scan = new Scanner(System.in); //thread will keep waiting for input for operating, order is like "request 2012"
				while (!confirm1 || !confirm2 || !confirm3 || !confirm4) {
					clientOrder = scan.nextLine ();
					splitSentence = clientOrder.split(" ");
				    if (splitSentence[0].equals("request") || splitSentence[0].equals("Request")) {
				    	fileN = Integer.parseInt(splitSentence[1]);
				    	if (fileN >= 0 && fileN <= 9999) {
				    		fileRequest = true;
							hash = fileN % 256;
				    		break;
				    	}
				    }
				    else if(splitSentence[0].equals("quit") || splitSentence[0].equals("Quit")) {
				    	gracefulLeave = true;
				    	break;
				    }
				    else
				         System.out.println("Invalid input or a wrong file number, this node can only request a file or do a graceful leaving, please try again!");
				}

				if (fileRequest) { //file request
					String sentSentence;
					InetAddress serverAddress = null;
					try {
						serverAddress = InetAddress.getLocalHost();
					} catch (UnknownHostException e2) {}
					
					Socket clientSocket = null;
					try {
						clientSocket = new Socket (serverAddress, successor1 + 50000); //clientSocket used to send message to server
					} catch (IOException e) {}
					DataOutputStream outToServer = null;
					try {
						outToServer = new DataOutputStream (clientSocket.getOutputStream());
					} catch (IOException e2) {}
					//"request:2012:1:50232:end" means the request is sent by a client
					sentSentence = "request:" + Integer.toString(fileN) + 
							":" + Integer.toString(requestFromClient) + 
							":" + Integer.toString(peerN) + 
							":end";
					
					try {
						outToServer.writeBytes(sentSentence);
					} catch (IOException e) {}
					try {
						clientSocket.close();
					} catch (IOException e) {}
					System.out.println ("File request message for " + fileN + " has been sent to my successor.");
				}
				
				else if (gracefulLeave) { //this peer will leave the DHT, TCP CLIENT will send two successors to the two predecessors
					String sentSentence;
					
					//this peer will generate a message "quit:peerN:successorN:end" to predecessors, predecessor will use the successor in the message as the new successor
					InetAddress serverAddress = null;
					try {
						serverAddress = InetAddress.getLocalHost();
					} catch (UnknownHostException e2) {}
					sentSentence = "quit" + 
							":" + Integer.toString(peerN) + 
							":" + Integer.toString(successor1) + 
							":" + Integer.toString(successor2) + 
							":end"; //message "quit1:peerN:successor1:successor2:end" is for the two predecessors
					
					Socket clientSocket1 = null; //this socket "clientSocket1" used to connect to the first predecessor
					try {
						clientSocket1 = new Socket (serverAddress, predecessor1 + 50000);
					} catch (IOException e) {}
					DataOutputStream outToServer1 = null;
					try {
						outToServer1 = new DataOutputStream (clientSocket1.getOutputStream());
					} catch (IOException e) {}
					try {
						outToServer1.writeBytes(sentSentence);
					} catch (IOException e) {}
					try {
						clientSocket1.close();
					} catch (IOException e) {}
					
					Socket clientSocket2 = null; //this socket "clientSocket2" used to connect to the second predecessor
					try {
						clientSocket2 = new Socket (serverAddress, predecessor2 + 50000);
					} catch (IOException e) {}
					DataOutputStream outToServer2 = null;
					try {
						outToServer2 = new DataOutputStream (clientSocket2.getOutputStream());
					} catch (IOException e) {}
					try {
						outToServer2.writeBytes(sentSentence);
					} catch (IOException e) {}
					try {
						clientSocket2.close();
					} catch (IOException e) {}
					
					sentSentence = "quit" + 
							":" + Integer.toString(peerN) + 
							":" + Integer.toString(predecessor1) + 
							":" + Integer.toString(predecessor2) + 
							":end"; 
					Socket clientSocket3 = null; //this socket "clientSocket1" used to connect to the first predecessor
					try {
						clientSocket3 = new Socket (serverAddress, successor1 + 50000);
					} catch (IOException e) {}
					DataOutputStream outToServer3 = null;
					try {
						outToServer3 = new DataOutputStream (clientSocket3.getOutputStream());
					} catch (IOException e) {}
					try {
						outToServer3.writeBytes(sentSentence);
					} catch (IOException e) {}
					try {
						clientSocket3.close();
					} catch (IOException e) {}
					
					Socket clientSocket4 = null; //this socket "clientSocket2" used to connect to the second predecessor
					try {
						clientSocket4 = new Socket (serverAddress, successor2 + 50000);
					} catch (IOException e) {}
					DataOutputStream outToServer4 = null;
					try {
						outToServer4 = new DataOutputStream (clientSocket4.getOutputStream());
					} catch (IOException e) {}
					try {
						outToServer4.writeBytes(sentSentence);
					} catch (IOException e) {}
					try {
						clientSocket4.close();
					} catch (IOException e) {}
				} //end of graceful leave
				else
					System.out.println("Unrecognised message in TCP client.");
			}
		}
	} //end of class TCP_Client
} //end of class DHT

