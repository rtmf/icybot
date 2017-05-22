#!/usr/bin/python
# vim:sw=4:ts=4:noexpandtab
import icybot_cmd
import icybot_icy
import icybot_bot
import icybot_cfg
from icybot_xml import s2x
import threading
import importlib

	
def printTitles():
	global icy,bot,cfg,ttl,bth
	try:
		titles=icy.title()
		if len(titles)==0:
			print("Nothing Playing :(")
		for title in titles:
			print("-=|[%10s]|=- %s"%title)
	except:
		print("ERROR")
	finally:
		ttl=threading.Timer(1,printTitles)
		ttl.start()

def runBot(ircbot):
	try:
		print(ircbot._host)
		ircbot.start()
	except:
		reload_func()

def reload_func(cmdonly=0):
	global icy,bot,cfg,ttl,bth
	if (cmdonly==1):
		importlib.reload(icybot_cmd)
		for ircbot in bot:
			ircbot._cmd=icybot_cmd.IcyBotCommands(ircbot,reload_func)
	else:
		if bot is not None:
			for ircbot in bot:
				ircbot.disconnect()
				del ircbot
			for bthread in bth:
				del bthread
		del bot
		del bth
		del icy
		del cfg
		del ttl
		importlib.reload(icybot_cmd)
		importlib.reload(icybot_icy)
		importlib.reload(icybot_bot)
		importlib.reload(icybot_cfg)
		cfg = s2x(open('icy.cfg').read())
		icy = icybot_icy.Icecast(cfg.find("icecast"))
		bot = [icybot_bot.RFHBot(icy,irccfg,reload_func) for irccfg in cfg.findall("irc")]
		bth = [threading.Thread(target=runBot,args=(ircbot,)) for ircbot in bot]
		for bthread in bth:
			bthread.start()
		printTitles()


def main():
	global icy,bot,cfg,ttl,bth
	cfg=None
	icy=None
	bot=None
	ttl=None
	bth=None
	reload_func()

def get_icy():
	cfg = s2x(open('icy.cfg').read())
	icy = icybot_icy.Icecast(cfg.find("icecast"))

if __name__ == "__main__":
	main()
