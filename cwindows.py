import os;
import curses;
import curses.textpad;
import code;
import sys;
import traceback;
from codeop import CommandCompiler, compile_command


class CursesStack:
	def __init__(self, stdscr, start_window):
		self.screen=stdscr
		
		self.lines=curses.LINES
		self.cols=curses.COLS
		
		self.fullwin=stdscr
		
		start_window.setWindow(stdscr)
		
		self.sub_windows=[start_window]
		self.current_window=0
		self.changeActive(0)
		self.logger=start_window
		
	def update(self, state):
		self.fullwin.erase()
		i=0;
		while(i<len(self.sub_windows)):
			self.sub_windows[(self.current_window+1+i) %len(self.sub_windows)].update(state)
			i=i+1

	def handleKey(self, key, state):
		if(key=="KEY_F(2)"):
			self.addWindow(ReplWindow(40, 40, 40, 10))
			return True
		if(key=="\t"):
			self.changeActive(self.current_window+1);
			return True
		if(key=="KEY_BTAB"):
			self.changeActive(self.current_window-1);
			return True
		return self.sub_windows[self.current_window].handleKey(key, state)

	def addWindow(self, window):
		window.setWindow(self.fullwin)
		self.sub_windows.append(window)
		
	def changeActive(self, to):
		self.sub_windows[self.current_window].setActive(False)
		if(to==-1):
			self.current_window=to+len(self.sub_windows)
		else:
			self.current_window=to%len(self.sub_windows)
		self.sub_windows[self.current_window].setActive(True)
		
	def logError(self, message):
		self.logger.log("Error: "+message)
		

class StackSubwindow():
	def __init__(self, x, y, width, height):
		self.x=x
		self.y=y
		self.height=height
		self.width=width
		
		if(self.x<0):
			self.x=curses.COLS+self.x

		if(self.y<0):
			self.y=curses.LINES+self.y

		if(self.height<0):
			self.height=curses.LINES-self.y+self.height-1

		if(self.width<0):
			self.width=curses.COLS-self.x+self.width-1

		if(self.x>curses.COLS):
			self.x=curses.COLS-3
			
		if(self.y>curses.LINES):
			self.y=curses.LINES-3
			
		if(self.x+self.width>curses.COLS):
			self.width=curses.COLS-self.x-2
			
		if(self.y+self.height>curses.LINES):
			self.height=curses.LINES-self.y-2

		self.vScroll=0
		self.hScroll=0
		self.content=[]
		self.active=False

	def update(self, state):

		if(self.active):
			self.window.attron(curses.color_pair(2))
		curses.textpad.rectangle(self.window, self.y, self.x, self.height+self.y, self.width+self.x)
		if(self.active):
			self.window.attron(curses.color_pair(1))

		self.content=self.getContent(state)
		
		if(self.vScroll==-1):
			self.vScroll=max(0, len(self.content)-self.height+1)
		
		i=0
		for line in self.content[self.vScroll:self.vScroll+self.height-1]:
			self.mvaddstr(self.x+1, self.y+1+i, line[self.hScroll:self.hScroll+self.width-2])
			i+=1
	
	def setActive(self, to):
		self.active=to

	def scrollTop(self):
		self.vScroll=0
		
	def scrollBottom(self):
		self.vScroll=-1
		
	def scrollUp(self):
		self.vScroll=max(0, self.vScroll-1)
	
	def scrollDown(self):
		self.vScroll+=1
		if(self.vScroll+self.height>len(self.content)):
			self.scrollBottom()

	def scrollLeft(self):
		self.hScroll=max(0, self.hScroll-1)

	def scrollRight(self):
		self.hScroll+=1

	def getContent(self, state):
		return []
		
	def handleKey(self, key, state):
		if(key=="KEY_UP"):
			self.scrollUp()
			return True
		if(key=="KEY_DOWN"):
			self.scrollDown();
			return True
		if(key=="KEY_HOME"):
			self.scrollTop();
			return True
		if(key=="KEY_END"):
			self.scrollBottom();
			return True
		if(key=="KEY_LEFT"):
			self.scrollLeft();
			return True
		if(key=="KEY_RIGHT"):
			self.scrollRight();
			return True
		return False
		
	def addstr(self, data):
		self.window.addstr(data)
		
	def mvaddstr(self, x, y, data):
		self.window.addstr(y, x, data)
	
	def setWindow(self, win):
		self.window=win
		
class SimpleWindow(StackSubwindow):
	def __init__(self, x, y, width, height, cb):
		super().__init__(x, y, width, height)
		self.cb=cb
		
	def getContent(self, state):
		return self.cb(state)

class ReplWindow(StackSubwindow):
	def __init__(self, x, y, width, height):
		super().__init__(x, y, width, height)
		
		self.input=[""]
		self.logBuffer=[]

	def getContent(self, state):
		s=[]
		s.extend(self.logBuffer)
		s.append("> "+self.input[0])
		s.extend(self.input[1:])
		return s
		
	def log(self, data):
		for line in data.split("\n"):
			self.logBuffer.append(line)
		self.scrollBottom()
		
	def displayHook(self):
		return lambda v : self.log(repr(v))
       
	def handleKey(self, key, state):
		if(key=="\n"):
			inp="\n".join(self.input)
			try:
				comp=code.compile_command(inp, "<input>", "single")#TODO partial lines
				if(comp==None):
					self.input.append("")
					self.scrollBottom()
					return True
				else:
					self.log("> "+inp)
					self.input=[""]
			except (OverflowError, SyntaxError, ValueError):
				self.log("> "+inp)
				type, value, tb = sys.exc_info()
				lines = traceback.format_exception_only(type, value)
				self.log(''.join(lines))
				self.scrollBottom()
				self.input=[""]
				return True
			try:
				oldhook=sys.displayhook
				sys.displayhook=self.displayHook()
				exec(comp, None, state)
				sys.displayhook=oldhook
			except SystemExit:
				raise
			except:
				type, value, tb = sys.exc_info()
				lines = traceback.format_exception(type, value, tb)
				self.log(''.join(lines))
		elif(key[0:3]=="KEY"):
			if(key=="KEY_BACKSPACE"):
				self.input[-1]=self.input[-1][0:-1]
			else:
				return False
		else:
			self.input[-1]+=key
		self.scrollBottom()
		return True

class TableWindow(StackSubwindow):
	def __init__(self, x, y, width, height, tablegen):
		super().__init__(x, y, width, height)

		self.tablegen=tablegen

	def getContent(self, state):
		table=self.tablegen(state)

		if(table==None or len(table)==0):
			return []

		res=[""]
		keys=[]

		for ele in table:
			line=""
			ekeys=ele.keys()
			for ekey in ekeys:
				if(not ekey in keys):
					keys.append(ekey)
			for key in keys:
				try:
					line+=str(ele[key])+"\t"
				except KeyError:
					line+="N/A\t"
			
			res.append(line)
		
		line=""
		for key in keys:
			line+=str(key)+"\t"
		res[0]=line
		return res

class FormattedTableWindow(StackSubwindow):
	def __init__(self, x, y, width, height, tablegen, fm):
		super().__init__(x, y, width, height)

		self.tablegen=tablegen
		self.format=fm
		
		for fmt in self.format:
			if(not "filter" in fmt.keys()):
				fmt["filter"]=lambda x : x
		
	def getContent(self, state):
		table=self.tablegen(state)
		
		if(table==None or len(table)==0):
			return []
			
		header=""
		
		for fmt in self.format:
			if(len(fmt['header'])>fmt['width']):
				header+=fmt['header'][0:fmt['width']]
			else:
				header+=fmt['header']+(" "*(fmt['width']-len(fmt['header'])))
		
		res=[header]
		
		for ele in table:
			line=""
			for fmt in self.format:
				try:
					val=str(fmt['filter'](ele[fmt["key"]]))
					if(len(val)>fmt['width']):
						line+=val[0:fmt['width']]
					else:
						line+=val+" "*(fmt['width']-len(val))
				except KeyError:
					line+=" "*fmt['width']
			res.append(line)
		
		return res

