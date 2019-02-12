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
import argparse
import traceback
from apiclient.discovery import build
from apiclient.errors import HttpError
from mysql import connector as mc
import icybot_cfg
# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyA7RZ3GBfd97qIt6cBHnYQrnkY7mYgyt0c"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
_cmd={}
class cmdArgParser(argparse.ArgumentParser):
	def parse_known_args(self,args):
		ret=None
		try:
			self.errorMessage=None
			ret=super().parse_known_args(args)
		except TypeError:
			ret=(self.format_usage(),args)
		if self.errorMessage is not None:
			return (self.errorMessage,args)
		elif ret is None:
			return (self.format_usage(),args)
		else:
			return ret
	def error(self,message):
		self.errorMessage=message
	def exit(self,status=0,message=None):
		self.errorMessage=message
		raise TypeError

def youtube_search(query,devkey,offset=0,length="long",order="date"):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
		developerKey=devkey)

	# Call the search.list method to retrieve results matching the specified
	# query term.
	search_response = youtube.search().list(
		q=query,
		safeSearch="none",
		part="snippet,id",
		#maxResults=50,
		order=order,
		type="video",
		videoDuration=length
	).execute()

	videos = []
	channels = []
	playlists = []

	# Add each result to the appropriate list, and then display the lists of
	# matching videos, channels, and playlists.
	for search_result in search_response.get("items", []):
		if search_result["id"]["kind"] == "youtube#video":
			if offset > 0:
				offset -= 1
			else:
				return "https://youtu.be/%s"%search_result["id"]["videoId"]
	return None

@contextlib.contextmanager
def stdoutIO(stdout=None):
	old = sys.stdout
	if stdout is None:
		stdout = io.StringIO()
	sys.stdout = stdout
	yield stdout
	sys.stdout = old

def icy_register_command(access,func):
	print("icy_register_command(%d,%s)"%(access,repr(func)))
	global _cmd
	cinf={
		"func":func,
		"access":access
		}
	_cmd[func.__name__.lower()]=cinf
def icy_command(access=0):
	if callable(access):
		return (icy_command_decorator(0))(access)
	else:
		return icy_command_decorator(access)
def icy_command_decorator(access):
	def icy_decorator(func):
		icy_register_command(access,func)
		return func
	return icy_decorator
class IcyBotYoutube(icybot_cfg.Configurable):
	def __schema__(self):
		self.value("devkey")
	def __init__(self,cmds):
		self._cmds=cmds
		self.ytparser=cmdArgParser("yt")
		self.ytparser.add_argument("-o","--offset",nargs=1,dest="offset",default=[0],help="return search result NUM (starting from 0)",metavar="NUM",type=int)
		self.ytparser.add_argument("keywords",nargs="*",default=[],metavar="KEYWORD",help="keywords for the search")
		self.ytparser.add_argument("-s","--sort",metavar=("ORDER"), nargs=1,default=["relevance"],choices=["date","rating","relevance","title","videoCount","viewCount"],help="sort order for results",dest="sort")
		self.ytparser.add_argument("-l","--length",nargs=1,metavar=("LEN"),default=["any"],choices=["any","long","medium","short"],dest="length")
		icybot_cfg.Configurable.__init__(self,cmds._bot._conf,"youtube",0)

class IcyBotDB(icybot_cfg.Configurable):
	def __schema__(self):
		self.value("username").value("password").value("database")
	def __init__(self,cmds):
		self._cmds=cmds
		icybot_cfg.Configurable.__init__(self,self._cmds._bot._conf,"db",0)
		self._cc=mc.Connect(user=self._username,password=self._password,database=self._database)
		self._cc.cmd_query("CREATE TABLE IF NOT EXISTS criticism ( title CHAR(127) not null unique , liked INTEGER not null default 0) CHARSET=utf8mb4;")
	def crit(self,title,liked=1):
		title=(title.replace("'","’").replace("\\","\\\\"))[0:127]
		for result in self._cc.cmd_query_iter("INSERT INTO criticism SET title='%s', liked=%d on duplicate key update title='%s', liked=liked+%d;SELECT liked FROM criticism WHERE title='%s';"%(((title,liked)*3)[:-1])):
			if 'columns' in result:
				columns = result['columns']
				rows=self._cc.get_rows()
				print(rows)
				if len(rows[0]):
					value=int(rows[0][0][0])
					return "Set liked value for -=|[%s]|=- to %d."%(title,value)
		return "Something went db'ly wrong."

class IcyBotCommands:
	def __init__(self,bot,reload_func):
		global _cmd
		self._cmd=_cmd
		self._bot=bot
		self._reload=reload_func
		self._access=bot._access
		self._yt=IcyBotYoutube(self)
		self._db=IcyBotDB(self)
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
					msg=cinf["func"](self,c,e,args)
				else:
					msg="/say ?ACCESS DENIED"
			else:
				msg="/say ?SYNTAX ERROR"
		except Exception as e:
			traceback.print_exc()
			msg="/say ?INTERNAL ERROR - %s"%str(e)
		finally:
			for line in msg.split("\n"):
				self._bot.irc(source,line)

@icy_command
def np(bot,c,e,args):
	return "Now Playing: %s"%bot._bot._icy.tit().title()

@icy_command
def up(bot,c,e,args):
	return str(bot._db.crit(bot._bot._icy.tit().bare(),1))

@icy_command
def dn(bot,c,e,args):
	return str(bot._db.crit(bot._bot._icy.tit().bare(),-1))

@icy_command(access=2)
def chan(bot,c,e,args):
	bot._bot.setcontext(args[0])
	return "set context to %s."%args[0]

@icy_command(access=2)
def here(bot,c,e,args):
	bot._bot.setcontext(None)
	return "set context to follow source."

@icy_command(access=2)
def wall(bot,c,e,args):
	bot._bot.setcontext('allchan')
	return "set context to all channels."

@icy_command
def nl(bot,c,e,args):
	return "At least [ %s ] hoopty froods currently listening to the Horizon Singularity Sound!"%(
			" , ".join(["%s:%s"%(k,v) for k,v in (bot._bot._icy.ice()).query("listeners").items()]))

@icy_command
def ping(bot,c,e,args):
	return "Pong"

@icy_command
def time(bot,c,e,args):
	return "Date: %s"%(str(datetime.now()))

@icy_command
def coinflip(bot,c,e,args):
	return "Your coin flipped %s"%(["heads","tails"][int(random.random()*2)])

@icy_command(access=1)
def join(bot,c,e,args):
	for chan in args:
		c.join(chan)
		bot._bot.say(chan,bot._bot._joinMsg)
	return "Joined %s."%(", ".join(args))

@icy_command(access=1)
def part(bot,c,e,args):
	for chan in args:
			c.part(chan)
	return "Parted %s."%(", ".join(args))

@icy_command
def motd(bot,c,e,args):
	return "Hello! I am "+ bot._bot._nick + " made partially by " + ", ".join(bot._bot._authors) + ", and many others who developed the F/OSS stack underneath me!"

def cmix_stop(then=None):
	print(then)
	os.system('chromix-too rm audible')
	if then is not None:
		os.system(then)

@icy_command(access=2)
def stop(bot,c,e,args):
	cmix_stop()
	return "Stopping anything currently playing..."

@icy_command(access=2)
def yt(bot,c,e,args):
	(options, args)=bot._yt.ytparser.parse_known_args(args)
	if type(options)==str:
		return options
	video=youtube_search(' '.join(options.keywords+args),bot._yt._devkey,int(options.offset[0]),order=options.sort[0],length=options.length[0])
	return "Found %s on YouTube.  %s"%(video,play(bot,c,e,[video])) if video is not None else "Nothing found on YouTube for %s"%(' '.join(options.keywords+args))

@icy_command(access=2)
def play(bot,c,e,args):
	url=' '.join(args).replace('"','\\"')
	cmix_stop('chromix-too open "%s"'%url)
	return "It should be playing momentarily..."

@icy_command(access=2)
def me(bot,c,e,args):
	return '/me '+' '.join(args)

@icy_command(access=2)
def say(bot,c,e,args):
	return '/say '+' '.join(args)

@icy_command(access=2)
def rebot(bot,c,e,args):
	bot._reload()
	return "?UNREACHABLE MESSAGE"

@icy_command(access=2)
def reload(bot,c,e,args):
	bot._reload(1)
	return "Reloading ICYBot Commands..."

#@icy_command(access=3)
#def pyev(bot,c,e,args):
#	try:
#		return str(eval(u" ".join(args).replace('%n',"\n").replace('%%','%')))
#	except Exception as e:
#		return str(e)

#@icy_command(access=3)
#def pyex(bot,c,e,args):
#	with stdoutIO() as s:
#		exec(u" ".join(args).replace('%n',"\n").replace('%%','%'))
#	output = s.getvalue()
#	print(output)
#	return output

@icy_command(access=3)
def shex(bot,c,e,args):
	output=os.popen(u" ".join(args).replace('%n','\n').replace('%%','%')).read()
	print(output)
	return output

@icy_command
def help(bot,c,e,args):
	return "Commands supported w/ access-level required, 0 is anyone: %s"%(str(["(%d):%s"%(bot._cmd[cmd]["access"],cmd) for cmd in bot._cmd.keys()]))

@icy_command
def access(bot,c,e,args):
	return "Access levels granted by regexes: %s"%(str(bot._access))

@icy_command
def lucy(bot,c,e,args):
	return "[rattling the chains reveals a message]: %s"%(xt.fromstring(requests.get('http://tymestl.org/~rtmf/lucy.php').text).find("body").find("p").find("div").text)

@icy_command
def ad(bot,c,e,args):
	return advert(bot,c,e,args)

@icy_command
def rfh(bot,c,e,args):
	return advert(bot,c,e,args)

@icy_command
def advert(bot,c,e,args):
	return "rfh: ♪Radio Free Horizon is ON THE AIR♪ | http://rfh.tymestl.org/500.ogg [HQ-500kbit vorbis] | http://rfh.tymestl.org/320.mp3  [LQ-320kbit mp3] | \"DJ\" RtMF in the...uh...patchbay - feel free to bug her with suggestions! | totally amateur | sometimes  awesome | often crashy | always weird | we're Musick for all Magick | {[Dark]Ice|Broad}casting direct from the Horizon  Singularity | ☮ ♥ 🌈 "
@icy_command(access=1)
def p(bot,c,e,args):
	return play(bot,c,e,args)
@icy_command(access=2)
def y(bot,c,e,args):
	return yt(bot,c,e,args)
@icy_command(access=2)
def o(bot,c,e,args):
	return yo(bot,c,e,args)
