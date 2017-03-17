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
	global icy,bot,cfg,ttl
#	try:
	titles=icy.title()
	for title in titles:
		print("-=|[%10s]|=- %s"%title)
	#except:
	#	print("ERROR\nERROR")
	ttl=threading.Timer(1,printTitles)
	ttl.start()

def reload_func(cmdonly=0):
	global icy,bot,cfg,ttl
	if (cmdonly==1):
		importlib.reload(icybot_cmd)
		bot._cmd=icybot_cmd.IcyBotCommands(bot,reload_func)
	else:
		if bot is not None:
			bot.disconnect()
		del bot
		del icy
		del cfg
		del ttl
		importlib.reload(icybot_cmd)
		importlib.reload(icybot_icy)
		importlib.reload(icybot_bot)
		importlib.reload(icybot_cfg)
		cfg = s2x(open('icy.cfg').read())
		icy = icybot_icy.Icecast(cfg.find("icecast"))
		bot = icybot_bot.RFHBot(icy,cfg.find("irc"),reload_func)
		printTitles()
		try:
			bot.start()
		except:
			reload_func()

def main():
	global icy,bot,cfg,ttl
	cfg=None
	icy=None
	bot=None
	ttl=None
	reload_func()


if __name__ == "__main__":
	main()
