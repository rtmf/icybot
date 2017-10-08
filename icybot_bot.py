# vim: set ts=2 sw=2 noexpandtab:
import irc.bot
import icybot_cfg
import icybot_cmd
import threading
class RFHBot(irc.bot.SingleServerIRCBot,icybot_cfg.Configurable):
	def __attr__(self):
		return ["host","port","password",("channels","channel"),"nick","name","gangsign","joinMsg",("authors","author"),("access","user","level"),"prefix"]
	def runthread(self):
		if self._thread is not None:
			self.die()
		else:
			self._reaper=None
			self._thread=threading.Thread(target=self._icy.runBot,args=[self])
			self._thread.start()
		return self
	def delthread(self):
		self.die()
		if self._thread is not None and self._reaper is None:
			self._reaper = threading.Thread(target=self.diethread,args=())
			self._reaper.start()
	def diethread(self):
		secs=0
		while(self._thread.is_alive()):
			print("Waiting for bot on host %s to die %d seconds elapsed."%(self._host,secs))
			self._thread.join(1)
			secs+=1
		print("Bot thread died for host %s, so will the reaper thread!"%host)
	def __init__(self,conf,sect,indx):
		icybot_cfg.Configurable.__init__(self,conf,sect,indx)
	def setup(self,icy):
		self._thread=None
		self._icy=icy
		self.setcfg()
		irc.bot.SingleServerIRCBot.__init__(self,[(self._host,int(self._port))],self._nick,self._name)
		self._cmd = icybot_cmd.IcyBotCommands(self,icy.reload_func)
		self._context = None
		return self

	def on_privnotice(self, connection, event):
		"""Identify to nickserv and log privnotices"""
		if not event.source:
			return
		source = event.source.nick
		if source and source.lower() == "nickserv":
			if event.arguments[0].lower().find("identify") >= 0:
				if self._nick == connection.get_nickname():
					connection.privmsg("nickserv", "identify %s %s" % (self._nick, self._password))

	def splitlong(self,target,text,func):
		text=text.replace('\n','\\n')
		parts=[text[i:i+420] for i in range(0, len(text), 420)]
		if len(parts)>1:
			parts[0]=parts[0]+"…"
			parts[-1]="…"+parts[-1]
			for idx in range(1,len(parts)-1):
				parts[idx]="…"+parts[idx]+"…"
		for part in parts:
			try:
				func(target,part)
			except irc.client.MessageTooLong as m:
				pass

	def irc(self,target,text):
		try:
			if self._context is not None:
				context=self._context
			else:
				context=[(self,target)]
			if len(text)==0:
				return
			if text[0]=='/':
				cmd=text.split(' ',1)
				for ircmd,ircfunc in [
						('/action', 'do'),
						('/me'    , 'do'),
						('/say'   , 'say'),
						]:
					if ircmd.startswith(cmd[0]):
						for bot,realtarget in context:
							getattr(bot,ircfunc)(realtarget,cmd[1])
						return
			self.say(target,text)
		except Exception as e:
			self.say(target,"?INTERNAL ERROR - %s"%(str(e)))

	def setcontext(self,context):
		contexts=None
		if context=='allchan':
			contexts=[(bot,chan) for sublist in [[(bot,chan) for chan in bot._channels] for bot in self._icy.bots()] for (bot,chan) in sublist]
		elif context is not None:
			contexts=[(self,context)]
		for bot in self._icy.bots():
			bot._context=contexts

	def say(self,target,text):
		self.splitlong(target,text,self.connection.privmsg)

	def do(self,target,text):
		self.splitlong(target,text,self.connection.action)

	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")
		c.privmsg("nickserv", "GHOST %s %s" % (self._nick, self._password))
	
	def on_privmsg(self, c, e):
		self._cmd.do_command(c, e, e.arguments[0].lstrip(), e.source.nick)
	
	def on_pubmsg(self, c, e):
		lmsg = e.arguments[0].lower().lstrip()
		for trigger in [self._prefix] + [self._nick+suffix for suffix in [": ",", ",":",","," "]]:
			if lmsg.startswith(trigger.lower()):
				self._cmd.do_command(c,e,e.arguments[0].lstrip()[len(trigger):],e.target)
				break

	def on_welcome(self,c,e):
                for channel in self._channels:
                    c.join(channel)
                    self.say(channel,self._joinMsg)

