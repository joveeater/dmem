import cwindows
import eternaldarkness
import memoryscan
import dolphinbp


def startup(state):
	state['window'].addWindow(cwindows.FormattedTableWindow(66,0, 25, 12, lambda x : memoryscan.ifConnected(x, eternaldarkness.readScriptTable),[
		{"header": "script", "key": "script", "width":8, "filter":lambda v : format(v, 'x')},
		{"header": "adv","key": "advance", "width":5},
		{"header": "time","key": "timer", "width":6},
		{"header": "lock","key": "lock", "width":5},
	]))
	state['eventLog']=[]
	dolphinbp.createManagedBp(0x8016b400, lambda s : s['eventLog'].append("Script ran: "+hex(s['dolphin']['reg']['gpr'][3])), state);
	dolphinbp.createManagedBp(0x800afec0, lambda s : s['eventLog'].append("Created restore"), state);
	dolphinbp.createManagedBp(0x800b002c, lambda s : s['eventLog'].append("Loaded restore"), state);
	dolphinbp.createManagedBp(0x801fea8c, lambda s : s['eventLog'].append(s['memscan'].readString(s['dolphin']['reg']['gpr'][5])+" allocated "+str(s['dolphin']['reg']['gpr'][3])+" bytes"), state);

	state['window'].addWindow(cwindows.SimpleWindow(278,0, 39, 80, lambda x : list(reversed(x['eventLog']))))

	state['window'].addWindow(cwindows.FormattedTableWindow(0,0, 65, 80, lambda x : memoryscan.ifConnected(x, eternaldarkness.readActorList),[
		{"header": "id", "key": "uid", "width":4},
		{"header": "addr", "key": "addr", "width":10, "filter":lambda v : format(v, 'x')},
		{"header": "geom", "key": "geom", "width":6},
		{"header": "type", "key": "type", "width":6},
		{"header": "room", "key": "room", "width":6},
		{"header": "gameflag", "key": "gameflag", "width":10},
		{"header": "script", "key": "script", "width":8},
		{"header": "death", "key": "death", "width":8},
		{"header": "hp", "key": "hp", "width":6},
	]))

