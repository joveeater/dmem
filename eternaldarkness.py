import memoryscan

def readActorList(state):
	list=[]
	link=state['memscan'].read4(0x8064d8a4)
	link=state['memscan'].read4(link+4)
	while(link!=0):
		uid=state['memscan'].read4(link+0x10)

		godata=state['memscan'].read4(link+0x24)

		if(godata!=0):
			gameflag=state['memscan'].read4(godata+0x18)
		
		
			chardata=state['memscan'].read4(link+0x34)
			
			room=-1
			geom=-1
			type=-1
			anim=-1
			if(chardata!=0):
				room=state['memscan'].read4(chardata+0x250)
				geom=state['memscan'].read4(chardata+0x244)
				type=state['memscan'].read4(chardata+0x248)
		
				base=state['memscan'].read4(chardata+0x40)
				if(base!=0):			
					index=state['memscan'].read4(base+0x880)
					i2=state['memscan'].read4(0xb8+base+index*0x110)
					#printf("Index %x %x\n", index, i2);
					if(i2!=0):
						anim=state['memscan'].read4(i2)

			data2=state['memscan'].read4(link+0x28)
			d3=state['memscan'].read4(data2+0x8c)
			script=state['memscan'].read2(d3+0x146)
			s2=state['memscan'].read2(d3+0x148)

			hp=state['memscan'].read2(godata+0x30);

			list.append({"uid":uid, "addr":link, "geom":geom, "type":type, "room":room, "gameflag":gameflag, "script": script, "death": s2, "hp":hp})

		else:
			list.append({"uid":uid, "addr":link})
		link=state['memscan'].read4(link+4)
	return list

def readScriptTable(state):
	list=[]
	i=0
	while(i<10):
		list.append({"script":state['memscan'].read2(0x805faa60+i*8), "advance":state['memscan'].read2(0x805faa62+i*8), "timer":state['memscan'].read2(0x805faa64+i*8), "lock":state['memscan'].read2(0x805faa66+i*8)})
		i+=1
	return list

	
