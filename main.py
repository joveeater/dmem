#!/usr/bin/python3

import curses
import socket
import io
import time
import re
import cwindows
import memoryscan
import eternaldarkness
import startup

stateMessageR=re.compile("^STATE: (\w+)\s+(\d+)(\s+0x([a-fA-F0-9]+)\s+([a-fA-F0-9]+))?")

def handleStateMessage(message, state):
	m=stateMessageR.match(message)

	if(m==None):
		state["window"].logError(message)
		return
	base=m.group(4)
	if(base==None):
		base="-1"
	size=m.group(5)
	if(size==None):
		size="-1"

	state["dolphin"]={"running":m.group(1),
					  "pid":int(m.group(2), 10),
					  "mem":{"base": int(base, 16), "size":int(size, 16)}}

	if(state["dolphin"]["mem"]["base"]!=-1 and (state["memscan"].pid!=state["dolphin"]["pid"] or state["memscan"].base!=state["dolphin"]["mem"]["base"])):
		state["memscan"]=memoryscan.MemoryScanner(state["dolphin"]["pid"], state["dolphin"]["mem"]["base"],state["dolphin"]["mem"]["size"])

regMessageR=re.compile("^REG: "+("([a-fA-F0-9]+)\s+"*98)+"$")

def handleRegMessage(message, state):
	m=regMessageR.match(message)
	if(m==None):
		state['window'].logError(message)
		return

	state['dolphin']['reg']={}
	state['dolphin']['reg']['pc']=int(m.group(1), 16)
	state['dolphin']['reg']['lr']=int(m.group(2), 16)
	state['dolphin']['reg']['gpr']=[]
	state['dolphin']['reg']['fpr']=[]

	i=0
	while(i<32):
		state['dolphin']['reg']['gpr'].append(int(m.group(3+i), 16))
		i+=1

	i=0
	while(i<32):
		state['dolphin']['reg']['fpr'].append([int(m.group(35+i*2), 16), int(m.group(36+i*2), 16)])
		i+=1
	
message_handlers={}

def addMessageHandler(message, handler):
	if(message in message_handlers.keys()):
		message_handlers[message].append(handler)
		return len(message_handlers[message])-1
	else:
		message_handlers[message]=[handler]
		return 0
		

parseMessageR=re.compile("^(\w+):");
def parseMessage(message, state):
	m=parseMessageR.match(message)
	if(m==None):
		state['window'].logError(message)
		return
	t=m.group(1)

	if(not t in message_handlers.keys()):
		state['window'].logError(message)
		return

	for h in message_handlers[t]:
		h(message, state)
		
def sendMessage(socket, message):
	
	buf=bytearray();
	buf.extend(len(message.encode()).to_bytes(8, 'little'));
	buf.extend(message.encode())
	socket.send(buf)

def main(stdscr):
	stdscr.nodelay(True)
	curses.update_lines_cols()
	curses.start_color()
	
	curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
	
	window_stack=cwindows.CursesStack(stdscr, cwindows.ReplWindow(66, -20, -42, -1))

	
	addMessageHandler("STATE", handleStateMessage);
	addMessageHandler("REG", handleRegMessage);

	s = socket.socket(socket.AF_INET)
	s.connect(('127.0.0.1', 3330))
	s.setblocking(False);

	i=0;

	state={}
	state["state"]=state
	state["window"]=window_stack
	state["cwindows"]=cwindows
	state["eternaldarkness"]=eternaldarkness
	state["memscan"]=memoryscan.MemoryScanner(-1, -1, -1)
	state["addMessageHandler"]=addMessageHandler
	state["sendMessage"]=lambda x : sendMessage(s, x)

	startup.startup(state)

	curbuf=bytearray();

	while 1:
		try:
			curbuf.extend(s.recv(4096));
			while(len(curbuf)>8):
				packetSize=int.from_bytes(curbuf[0:8], "little");
				if(len(curbuf)>=packetSize+8):
					message=str(curbuf[8:8+packetSize], "UTF-8")
					parseMessage(message, state)
					curbuf=curbuf[8+packetSize:]
					window_stack.update(state)
					i=0
				else:
					break
		except io.BlockingIOError:
			pass
		try:
			key=stdscr.getkey()
			window_stack.handleKey(key, state)
			window_stack.update(state)
			i=0
		except curses.error:
			pass
		if(i==100):
			i=0
			window_stack.update(state)
		else:
			i+=1
		time.sleep(0.001)

curses.wrapper(main);

