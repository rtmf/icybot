#!/usr/bin/python -i
# vim:sw=4:ts=4:noexpandtab
import xml.etree.ElementTree as xt
import requests
import readline
import time
import irc.bot
from datetime import datetime
import random
import threading

def x2d(element):
	return {tag: text for (tag,text) in [(child.tag,child) for child in element]}

def setcfg(obj,cfg,*attrs):
	cfg=x2d(cfg)
	print(cfg.keys())
	for attr in attrs:
		if type(attr)==str:
			val=cfg[attr].text
		elif len(attr)==2:
			val=[child.text for child in cfg[attr[0]].findall(attr[1])]
		elif len(attr)==3:
			val={body: param for (body,param) in [(child.text,child.get(attr[2])) for child in cfg[attr[0]].findall(attr[1])]}
		setattr(obj,"_%s"%attr,val)
				
class Icecast:
	def __init__(self,cfg):
		#username,password,hostname):
		self._cfg=x2d(cfg)
		setcfg(self,cfg,"username","password","hostname")
		self.__url__="http://%s:%s@%s/admin"%(username,password,hostname)

	def call(self,function,args={},mount=None):
		params=args
		params["mount"]=mount
		return requests.get("%s/%s"%(self.__url__,function),params=params)
	def mounts(self):
		return [source.get("mount") for source in xt.fromstring(self.call("listmounts").text).findall("source")]

	def each(self,function,args={}):
		return [(mount,self.call(function,args=args,mount=mount)) for mount in self.mounts()]

	def song(self,song):
		return self.each(function="metadata",args={"mode":"updinfo","song":song})

	def status(self):
		return [(mount[0],xt.fromstring(mount[1].text)) for mount in self.each(function="stats")]

	def stats(self):
		return x2d(xt.fromstring(self.call('stats').text))

	def title(self):
		return [(mount[0],mount[1].find("source").find("title").text) for mount in self.status() if mount[1].find("source").find("title") is not None]

	def clients(self):
		return self.each(function="listclients")

def printTitles(icy):
	try:
		titles=icy.title()
		for title in titles:
			print("-=|[%10s]|=- %s"%title)
	except:
		print("ERROR\nERROR")
	threading.Timer(1,printTitles,[icy]).start()

class RFHBot(irc.bot.SingleServerIRCBot):
	def __init__(self,icy,cfg):
		self._icy=icy
		setcfg(self,cfg,"host","port","password","channel","nick","name","gangsign","joinMsg",("authors","author"),("access","user","level"),"prefix")
		irc.bot.SingleServerIRCBot.__init__(self,[(self._host,self._port)],self._nick,self._name)

	def on_privnotice(self, connection, event):
		"""Identify to nickserv and log privnotices"""
		if not event.source:
			return
		source = event.source.nick
		if source and source.lower() == "nickserv":
			if event.arguments[0].lower().find("identify") >= 0:
				if self._nick == connection.get_nickname():
					connection.privmsg("nickserv", "identify %s %s" % (self._nick, self._password))

	def say(self,target,text):
		parts=[text[i:i+420] for i in range(0, len(text), 420)]
		if len(parts)>1:
			parts[0]=parts[0]+"…"
			parts[-1]="…"+parts[-1]
			for idx in range(1,len(parts)-1):
				parts[idx]="…"+parts[idx]+"…"
		for part in parts:
			try:
				self.connection.privmsg(target,part)
			except irc.client.MessageTooLong as m:
				pass

	def do(self,target,text):
		self.connection.action(target,text)

	def on_nicknameinuse(self, c, e):
		c.nick(c.get_nickname() + "_")
	
	def on_privmsg(self, c, e):
		self.do_command(c, e, e.arguments[0],e.source.nick)
	
	def on_pubmsg(self, c, e):
		lmsg = e.arguments[0].lower()
		for trigger in [self._prefix] + [self._nick+suffix for suffix in [": ",", ",":",","," "]]:
			if lmsg.startswith(trigger.lower()):
				self.do_command(c,e,e.arguments[0][len(trigger):],e.target)
				break
	
	def do_command(self,c,e,cmd,source):
		cmd=cmd.split(" ")
		msg="?REDO FROM START"
		try:
			msg=getattr(self,"cmd_%s"%(cmd[0].lower()))(c,e,cmd[1:])
		except AttributeError as a:
			msg="?SYNTAX ERROR"
		except o:
			msg="?INTERNAL ERROR"
		finally:
			self.say(source,msg)
	
	def cmd_np(self,c,e,args):
		return ", ".join(["-=|[%10s]|=- %s"%title for title in self._icy.title()])

	def cmd_nl(self,c,e,args):
		return "At least %s hoopty froods currently listening to the Horizon Singularity Sound!"%(((self._icy.stats())["listeners"]).text)

	def cmd_ping(self,c,e,args):
		return "Pong"

	def cmd_time(self,c,e,args):
		return "Date: %s"%(str(datetime.now()))

	def cmd_coinflip(self,c,e,args):
		return "Your coin flipped %s"%(["heads","tails"][int(random.random()*2)])

	def cmd_join(self,c,e,args):
		if e.source.nick in self._access:
			if self._access[e.source.nick]>0:
				for chan in args:
						c.join(chan)
						self.say(chan,self._joinMsg)
				return "Joined %s."%(", ".join(args))

	def cmd_part(self,c,e,args):
		if e.source.nick in self._access:
			if self._access[e.source.nick]>0:
				for chan in args:
						c.part(chan)
				return "Parted %s."%(", ".join(args))

	def cmd_motd(self,c,e,args):
		return "Hello! I am "+ self._nick + " made partially by " + ", ".join(self._authors) + ", and many others who developed the F/OSS stack underneath me!"
		
	def on_welcome(self,c,e):
		c.join(self._channel)
		self.say(self._channel,self._joinMsg)

def main():
	cfg = xt.fromstring(open('icy.cfg').read())
	icy = Icecast(cfg.find("icecast"))
	bot = RFHBot(icy,cfg.find("irc"))
	printTitles(icy)
	bot.start()

if __name__ == "__main__":
	main()
