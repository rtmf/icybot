import icybot_cfg
from icybot_xml import s2x,x2d
from lxml import etree as xt
import requests
class Icecast(icybot_cfg.Configurable):
    def __schema__(self):
        self.value("username","icybot").value("password").value("hostname")
    def __conf__(self):
        self.__url__="http://%s:%s@%s/admin"%(self._username,self._password,self._hostname)
    def call(self,function,args={},mount=None):
        params=args
        params["mount"]=mount
        return requests.get("%s/%s"%(self.__url__,function),params=params)
    def mounts(self):
        return [source.get("mount") for source in s2x(self.call("listmounts").text).findall("source")]

    def each(self,function,args={}):
        el=xt.Element(function)
        for mount in self.mounts():
            (lambda el,mo,re: 
                xt.SubElement(el,"mount",{"path":mount}).append(re)
                )(el,mount,s2x(self.call(function,args=args,mount=mount).text))
        return el

    def song(self,song):
        return self.each(function="metadata",args={"mode":"updinfo","song":song})

    def stats(self):
        return x2d(s2x(self.call('stats').text))

    def title(self):
        return self.query("title")

    def query(self,query):
        return {f.getparent().getparent().getparent().get("path"):f.text for f in
                self.each("stats").xpath("//mount/icestats/source/%s"%(query))}

    def clients(self):
        return self.each(function="listclients")


