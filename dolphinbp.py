
def manageBpReg(bp, cb, message, state):
	if(state['dolphin']['reg']['pc']!=bp):
		return
	cb(state)

breakpointsList=[]

def checkAndRefresh(message, state):
	for bp in breakpointsList:
		state['sendMessage']("ADDBP: "+str(bp))
	
def createBp(bp, state):
	if(len(breakpointsList)==0):
		state['addMessageHandler']("BPREFRESH", checkAndRefresh)
	if(not bp in breakpointsList):
		state['sendMessage']("ADDBP: "+str(bp))
		breakpointsList.append(bp)

def createManagedBp(bp, cb, state):
	state['addMessageHandler']("REG", lambda m,s : manageBpReg(bp, cb, m, s))
	createBp(bp, state)
