# vim:sw=4:ts=4:noexpandtab
import sys
import random
import threading
import time
import xml.etree.ElementTree as xt
import requests

class IcyBotCommands():
	def __init__(self,bot):
		self._bot=bot

	def do_command(self,c,e,cmd,source):
		cmd=cmd.split(" ")
		msg="?REDO FROM START"
		try:
			msg=getattr(self,"cmd_%s"%(cmd[0].lower()))(c,e,cmd[1:])
		except AttributeError as a:
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

	def cmd_join(self,c,e,args):
		if e.source.nick in self._bot._access:
			if int(self._bot._access[e.source.nick])>0:
				for chan in args:
						c.join(chan)
						self._bot.say(chan,self._bot._joinMsg)
				return "Joined %s."%(", ".join(args))

	def cmd_part(self,c,e,args):
		if e.source.nick in self._bot._access:
			if int(self._bot._access[e.source.nick])>0:
				for chan in args:
						c.part(chan)
				return "Parted %s."%(", ".join(args))

	def cmd_motd(self,c,e,args):
		return "Hello! I am "+ self._bot._nick + " made partially by " + ", ".join(self._bot._authors) + ", and many others who developed the F/OSS stack underneath me!"

	def cmd_reload(self,c,e,args):
		self._bot.reload_cmd()
		return "Reloading ICYBot Commands"

	def cmd_mark(self,c,e,args):
		return "[rattling the chains reveals a message]: %s"%(xt.fromstring(requests.get('http://tymestl.org/~rtmf/mark.php').text).find("body").find("p").find("div").text)
