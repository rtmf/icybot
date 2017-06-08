# vim: set ts=2 sw=2 noexpandtab:
import irc.bot
from icybot_cfg import setcfg
import icybot_cmd
class RFHBot(irc.bot.SingleServerIRCBot):
	def __init__(self,icy,cfg,reload_func):
		self._icy=icy
		setcfg(self,cfg,"host","port","password",("channels","channel"),"nick","name","gangsign","joinMsg",("authors","author"),("access","user","level"),"prefix")
		irc.bot.SingleServerIRCBot.__init__(self,[(self._host,int(self._port))],self._nick,self._name)
		self._cmd = icybot_cmd.IcyBotCommands(self,reload_func)

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

