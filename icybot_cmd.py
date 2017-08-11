# vim:sw=4:ts=4:noexpandtab
import os
import sys
import io
import contextlib
import random
import threading
import time
import xml.etree.ElementTree as xt
import requests
import re
import datetime

@contextlib.contextmanager
def stdoutIO(stdout=None):
	old = sys.stdout
	if stdout is None:
		stdout = io.StringIO()
	sys.stdout = stdout
	yield stdout
	sys.stdout = old

class IcyBotCommands():
	def __init__(self,bot,reload_func):
		self._bot=bot
		self._reload=reload_func
		self._cmd=self.list_cmd()
		self._access=bot._access

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
			self._bot.irc(source,msg)
	
	def cmd_np(self,c,e,args):
		return ", ".join(["-=|[%10s]|=- %s"%title for title in self._bot._icy.title()])
	
	def acmd_2_chan(self,c,e,args):
		self._bot.setcontext(args[0])
		return "set context to %s."%args[0]

	def acmd_2_here(self,c,e,args):
		self._bot.setcontext(None)
		return "set context to follow source."

	def acmd_2_wall(self,c,e,args):
		self._bot.setcontext('allchan')
		return "set context to all channels."

	def cmd_nl(self,c,e,args):
		return "At least %s hoopty froods currently listening to the Horizon Singularity Sound!"%(((self._bot._icy.stats())["listeners"])[1])

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

	def acmd_2_play(self,c,e,args):
		url=' '.join(args).replace('"','\\"')
		os.system('chromix with "^https://[^/]*youtu[^/]*/" close;chromix load "%s"'%(url))
		return "It should be playing momentarily..."

	def acmd_2_me(self,c,e,args):
		return '/me '+' '.join(args)

	def acmd_2_say(self,c,e,args):
		return '/say '+' '.join(args)

	def acmd_2_rebot(self,c,e,args):
		self._reload()
		return "?UNREACHABLE MESSAGE"

	def acmd_2_reload(self,c,e,args):
		self._reload(1)
		return "Reloading ICYBot Commands..."

	def acmd_2_eval(self,c,e,args):
		try:
			return str(eval(u" ".join(args).replace('%n',"\n").replace('%%','%')))
		except Exception as e:
			return str(e)

	def acmd_2_exec(self,c,e,args):
		with stdoutIO() as s:
			exec(u" ".join(args).replace('%n',"\n").replace('%%','%'))
		output = s.getvalue()
		print(output)
		return output

	def cmd_help(self,c,e,args):
		return "Commands supported w/ access-level required, 0 is anyone: %s"%(str(["(%d):%s"%(self._cmd[cmd]["access"],cmd) for cmd in self._cmd.keys()]))
	
	def cmd_access(self,c,e,args):
		return "Access levels granted by regexes: %s"%(str(self._access))

	def cmd_mark(self,c,e,args):
		return "[rattling the chains reveals a message]: %s"%(xt.fromstring(requests.get('http://tymestl.org/~rtmf/mark.php').text).find("body").find("p").find("div").text)
	
	def cmd_ad(self,c,e,args):
		return self.cmd_advert(c,e,args)
	
	def cmd_rfh(self,c,e,args):
		return self.cmd_advert(c,e,args)

	def cmd_advert(self,c,e,args):
		return "rfh: ♪Radio Free Horizon is ON THE AIR♪ | http://rfh.tymestl.org/500.ogg [HQ-500kbit vorbis] | http://rfh.tymestl.org/320.mp3  [LQ-320kbit mp3] | \"DJ\" RtMF in the...uh...patchbay - feel free to bug her with suggestions! | totally amateur | sometimes  awesome | often crashy | always weird | we're Musick for all Magick | {[Dark]Ice|Broad}casting direct from the Horizon  Singularity | ☮ ♥ 🌈 "
