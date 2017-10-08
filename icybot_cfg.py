import icybot_xml
from icybot_xml import *
class ConfigEntity:
    def __init__(self,configurable,cfg,attr):
        self._attr=attr
        self._obj=configurable
        self._cfg=cfg
    def cfg(self):
        return self._cfg
    def val(self):
        return self._val
    def att(self):
        return ([self._attr] if type(self._attr)==str else self._attr)
    def set(self):
        print("[_%s]:%s"%(self.att()[0],str(self.__des__())))
        setattr(self._obj,"_%s"%self.att()[0],self.__des__())
        print (type(self._obj))
    def get(self):
        self.__ser__(getattr(self._obj,"_%s"%self.att()[0]))
    def ent(self):
        return self.__ent__()
    def foc(self,node,name,**attr):
        ent=node.findall(name)
        if ent is None:
            ent = [cae(node,name,**attr)]
        return ent
    def __ent__(self):
        return self.foc(self.cfg(),self.att()[0])[0]
    def __des__(self):
        return self.ent().text.strip()
    def __ser__(self,val):
        self.ent().text=str(val)
class ConfigList(ConfigEntity):
    def __lis__(self):
        return self.foc(self.ent(),self.att()[1])
    def lis(self):
        return self.__lis__()
    def lsr(self,par,val):
        return self.__lsr__(par,val)
    def lds(self,lis,val):
        return self.__lds__(lis,val)
    def __lds__(self,lis,val):
        return lis+[val.text.strip()]
    def __lsr__(self,lis,val):
        return cae(self.ent(),self.att()[1],val)
    def __des__(self):
        lis=self.els()
        for val in self.lis():
            lis=self.lds(lis,val)
        return lis
    def __els__(self):
        return []
    def els(self):
        return self.__els__()
    def __ser__(self,lis):
        self.ent().clear()
        for val in lis:
            self.ent().append(self.lsr(lis,val))
class ConfigDict(ConfigList):
    def __els__(self):
        return {}
    def __lsr__(self,dic,val):
        ent=cae(self.ent(),self.att()[1],val)
        ent.set(self.att()[2],dic[val])
        return ent
    def __lds__(self,dic,val):
        body=val.text.strip()
        attr=val.get(self.att()[2])
        if attr is None:
            val.set(self.att()[2],"")
            attr=""
        dic[body]=attr
        return dic

class Configurable:
    def __init__(self,conf,sect,indx=0):
        self._conf=None
        self._sect=sect
        self._indx=indx
        self.newcfg(conf)
    def __conf__(self):
        pass
    def __sync__(self):
        pass
    def conf(self):
        self.__conf__()
    def sync(self):
        self.__sync__()
    def __del__(self):
        self.delcfg()
        self._conf=None
    def newcfg(self,conf):
        self.delcfg()
        self._conf=conf
        conf.regcfg(self)
        self.getcfg()
    def delcfg(self):
        if self._conf is not None:
            self._conf.discfg(self)
            self._conf=None
    def getval(self,name):
        return getattr(self,"_%s"%(name))
    def setval(self,name,val):
        setattr(self,"_%s"%(name),val)
    def cfgent(self,cfg,attr):
        if type(attr)==str:
            return ConfigEntity(self,cfg,[attr])
        elif len(attr)==2:
            return ConfigList(self,cfg,attr)
        elif len(attr)==3:
            return ConfigDict(self,cfg,attr)
    def setcfg(self):
        cfg=self._conf.getsec(self)
        for attr in self.attr():
            self.cfgent(cfg,attr).set()
        self.conf()
    def getcfg(self):
        self.sync()
        cfg=self._conf.getsec(self)
        for attr in self.__attr__():
            self.cfgent(cfg,attr).get()
    def indx(self):
        return self.__indx__()
    def sect(self):
        return self.__sect__()
    def attr(self):
        return self.__attr__()
    def __indx__(self):
        return self._indx
    def __sect__(self):
        return self._sect
    def __attr__(self):
        return self._attr

def ConfigurableFactory(conf,sect,inst):
        lis=[]
        indx=0
        for ins in conf.getlis(sect):
            lis+=[inst(conf,sect,indx)]
            indx+=1
        return lis
class Configuration:
    def __init__(self,path):
        self._objs=[]
        self.loadcfg(path)
    def loadcfg(self,path):
        try:
            conf=s2x(open(path).read())
        except e:
            self._path=None
        else:
            self._conf=conf
            self._path=path
        for obj in self._objs:
            obj.setcfg()
    def regcfg(self,obj):
        self.discfg(obj)
        self._objs+=[obj]
        obj.setcfg()
    def savcfg(self):
        if self._path is None:
            return
        for obj in self._objs:
            obj.getcfg()
        open(self._path,'w').write(x2s(self._conf))
    def discfg(self,obj):
        self._objs=[_obj for _obj in self._objs if _obj is not obj]
    def getlis(self,sec):
        cfg=self._conf.findall(sec)
        if cfg is None:
            cfg=[cae(self._conf,sect)]
        return cfg
    def getsec(self,obj):
        sect=obj.sect()
        indx=obj.indx()
        cfg=self._conf.findall(sect)
        if cfg is None:
            cfg=[]
        while indx>=len(cfg):
            cfg+=cae(self._conf,sect)
        return cfg[indx]
