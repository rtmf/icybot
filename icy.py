#!/usr/bin/python
# vim: sw=2 ts=2 noet syntax=python:
import icybot_cmd
import icybot_icy
import icybot_bot
import icybot_cfg
import threading
import importlib
import time
import traceback

class IcyTitles():
	def __init__(self,icy):
		self._icy=icy
		self._reaper=None
		self._running=True
		self._timer=None
		self._titles=None
		self._bare=""
		self.printTitles()
	def poll(self):
			titles=self._icy.ice().title()
			if len(titles)==0:
				titles="Nothing Playing :("
				self._bare=""
			else:
				titles=titles[list(titles.keys())[0]]
				self._bare=titles
				titles="[ %s ] - %s"%((" , ".join(["%s:%s"%(k,v) for k,v in (self._icy.ice()).query("listeners").items()])),titles)
			if titles!=self._titles:
				self._titles=titles
				return True
			return False
#				for bot in self._icy._bot:
#					for chan in bot._channels:
#						bot.do(chan,"is now playing: %s"%titles)
	def title(self):
		return self._titles
	def bare(self):
		return self._bare
	def printTitles(self):
		try:
			if self.poll():
				print("[%s]: %s"%(time.ctime(),self.title()))
		except:
			traceback.print_exc()
			print("ERROR")
		finally:
			if self._timer is not None:
				del self._timer
			if (self._running):
				self._timer=threading.Timer(1,self.printTitles)
				self._timer.start()
			else:
				self._timer=None
	def stop(self):
		if (self._timer) is not None:
			self._running=False
			if (self._reaper) is None:
				self._reaper=threading.Thread(target=self.reap,args=())
				self._reaper.start()
	def reap(self):
		secs=0
		while(self._timer is not None):
			print("Waiting for title display thread to die %d seconds elapsed."%secs)
			self._timer.join(1)
			secs+=1
		print("Title display thread died, so will the reaper thread!")
class Icy:
	def runBot(self,ircbot):
		try:
			#print(ircbot._host)
			ircbot.start()
		except:
			self.reload_func()
	def __init__(self):
		self._ice=None
		self._tit=None
		self._bot=[]
		self._cfg=None
		self.reload_func()
	def nocfg(self):
		self._cfg=None
	def mkcfg(self,path):
		self._cfg=icybot_cfg.Configuration(path)
	def cfg(self):
		return self._cfg
	def nobots(self):
		bot=self.bots()
		if bot is not None and len(bot)>0:
			self._bot=[]
			for ircbot in bot:
				ircbot.delthread()
				del ircbot
		self._bot=[]
	def notit(self):
		if self._tit is not None:
			self._tit.stop()
		self._tit=None
	def mktit(self):
		if self._tit is None:
			self._tit=IcyTitles(self)
	def tit(self):
		return self._tit
	def noice(self):
		if self._ice is not None:
			del self._ice
		self._ice=None
	def mkice(self):
		self._ice = icybot_icy.Icecast(self.cfg(),"icecast",0)
	def ice(self):
		return self._ice
	def tit(self):
		return self._tit
	def mkbots(self):
		self._bot = [bot.setup(self).runthread() for bot in icybot_cfg.ConfigurableFactory(self.cfg(),"irc",icybot_bot.RFHBot)]
	def bots(self):
		return self._bot
	def reload_func(self,cmdonly=0):
		if (cmdonly==1):
			importlib.reload(icybot_cmd)
			for ircbot in self.bots():
				ircbot._cmd=icybot_cmd.IcyBotCommands(ircbot,self.reload_func)
		else:
			self.nobots()
			self.notit()
			self.noice()
			self.nocfg()
			importlib.reload(icybot_cmd)
			importlib.reload(icybot_icy)
			importlib.reload(icybot_bot)
			importlib.reload(icybot_cfg)
			self.mkcfg('icy.cfg')
			self.mkice()
			self.mktit()
			self.mkbots()
			self.cfg().savcfg()

def main():
	ibt=Icy()


if __name__ == "__main__":
	main()
