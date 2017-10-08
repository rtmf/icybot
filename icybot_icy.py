import icybot_cfg
from icybot_xml import s2x,x2d
import requests
class Icecast(icybot_cfg.Configurable):
    def __attr__(self):
        return ["username","password","hostname"]
    def __conf__(self):
        self.__url__="http://%s:%s@%s/admin"%(self._username,self._password,self._hostname)
    def call(self,function,args={},mount=None):
        params=args
        params["mount"]=mount
        return requests.get("%s/%s"%(self.__url__,function),params=params)
    def mounts(self):
        return [source.get("mount") for source in s2x(self.call("listmounts").text).findall("source")]

    def each(self,function,args={}):
        return [(mount,self.call(function,args=args,mount=mount)) for mount in self.mounts()]

    def song(self,song):
        return self.each(function="metadata",args={"mode":"updinfo","song":song})

    def status(self):
        return [(mount[0],s2x(mount[1].text)) for mount in self.each(function="stats")]

    def stats(self):
        return x2d(s2x(self.call('stats').text))

    def title(self):
        return [(mount[0],mount[1].find("source").find("title").text) for mount in self.status() if mount[1].find("source").find("title") is not None]

    def clients(self):
        return self.each(function="listclients")


