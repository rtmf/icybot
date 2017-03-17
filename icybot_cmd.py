# vim:sw=4:ts=4:noexpandtab
import sys
import random
import threading
import time
import xml.etree.ElementTree as xt
import requests
import re
import datetime

class IcyBotCommands():
	def __init__(self,bot,reload_func):
		self._bot=bot
		self._reload=reload_func
		self._cmd=self.list_cmd()
		self._access=bot._access
		print (self._cmd)

	def list_cmd(self):
		return {cmd: info for (cmd,info) in (
			[(cmd[4:],{"access":0,"func":getattr(self,cmd)}) for cmd in dir(self) if cmd.startswith("cmd_")] + 
			[(cmd[2],{"access":int(cmd[1]),"func":getattr(self,'_'.join(cmd))}) for cmd in [
				cmd.split("_",2) for cmd in dir(self) if cmd.startswith("acmd_")]])}


	def do_command(self,c,e,cmd,source):
		msg="?REDO FROM START"
		try:
			cmd=cmd.split(" ")
			args=cmd[1:]
			cmd=cmd[0].lower()
			print("Command: [%s]"%(cmd))
			if cmd in self._cmd:
				alev=0
				cinf=self._cmd[cmd]
				userhost=e.source.userhost
				for user in self._access.keys():
					if re.fullmatch(user,userhost) is not None:
						alev=max(alev,int(self._access[user]))
				if alev>=cinf["access"]:
					msg=cinf["func"](c,e,args)
				else:
					msg="?ACCESS DENIED"
			else:
				msg="?SYNTAX ERROR"
		except Exception as e:
			msg="?INTERNAL ERROR - %s"%str(e)
		finally:
			self._bot.say(source,msg)
	
	def cmd_np(self,c,e,args):
		return ", ".join(["-=|[%10s]|=- %s"%title for title in self._bot._icy.title()])

	def cmd_nl(self,c,e,args):
		return "At least %s hoopty froods currently listening to the Horizon Singularity Sound!"%(((self._bot._icy.stats())["listeners"]).text)

	def cmd_ping(self,c,e,args):
		return "Pong"

	def cmd_time(self,c,e,args):
		return "Date: %s"%(str(datetime.now()))

	def cmd_coinflip(self,c,e,args):
		return "Your coin flipped %s"%(["heads","tails"][int(random.random()*2)])

	def acmd_1_join(self,c,e,args):
		for chan in args:
			c.join(chan)
			self._bot.say(chan,self._bot._joinMsg)
		return "Joined %s."%(", ".join(args))

	def acmd_1_part(self,c,e,args):
		for chan in args:
				c.part(chan)
		return "Parted %s."%(", ".join(args))

	def cmd_motd(self,c,e,args):
		return "Hello! I am "+ self._bot._nick + " made partially by " + ", ".join(self._bot._authors) + ", and many others who developed the F/OSS stack underneath me!"

	def acmd_2_rebot(self,c,e,args):
		if check_auth(e.source.nick,2):
			self._reload()
			return "Reloading ICYBot Code..."
		else:
			return "Not authorized!"

	def acmd_2_reload(self,c,e,args):
		self._reload(1)
		return "Reloading ICYBot Commands..."

	def cmd_help(self,c,e,args):
		return "Commands supported w/ access-level required, 0 is anyone: %s"%(str(["(%d):%s"%(self._cmd[cmd]["access"],cmd) for cmd in self._cmd.keys()]))
	
	def cmd_access(self,c,e,args):
		return "Access levels granted by regexes: %s"%(str(self._access))

	def cmd_mark(self,c,e,args):
		return "[rattling the chains reveals a message]: %s"%(xt.fromstring(requests.get('http://tymestl.org/~rtmf/mark.php').text).find("body").find("p").find("div").text)

