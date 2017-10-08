import icybot_xml
from icybot_xml import *
class ConfigValue:
    def __init__(self,configurable,name,defl):
        self._name=name
        self._obj=configurable
        self._defl=defl
    def cfg(self):
        return self._obj._conf.getsec(self._obj)
    def val(self):
        return self._val
    def load(self):
        print("[_%s]:%s"%(self._name,str(self.__des__())))
        setattr(self._obj,"_%s"%self._name,self.__des__())
        print (type(self._obj))
    def save(self):
        self.ser(getattr(self._obj,"_%s"%self._name))
    def ent(self):
        return self.__ent__()
    def foc(self,node,name,**attr):
        ent=node.findall(name)
        if ent is None:
            ent = [cae(node,name,**attr)]
            self.ser(self.defl())
        return ent
    def defl(self):
        return self._defl
    def ded(self):
        return self.__des__()
    def ser(self,val):
        self.__ser__(val)
    def __ent__(self):
        return self.foc(self.cfg(),self._name)[0]
    def __des__(self):
        return self.ent().text.strip()
    def __ser__(self,val):
        self.ent().text=str(val)
class ConfigList(ConfigValue):
    def __init__(self,configurable,name,defl,itemname,itemdefl):
        super().__init__(configurable,name,defl)
        self._itemname=itemname
        self._itemdefl=itemdefl
    def __lis__(self):
        return self.foc(self.ent(),self._name)
    def lis(self):
        return self.__lis__()
    def lsr(self,par,val):
        return self.__lsr__(par,val)
    def lds(self,lis,val):
        return self.__lds__(lis,val)
    def __lds__(self,lis,val):
        return lis+[val.text.strip()]
    def __lsr__(self,lis,val):
        return cae(self.ent(),self._itemname,val)
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

    def __init__(self,configurable,name,defl,itemname,itemdefl,attrname,attrdefl):
        super().__init__(configurable,name,defl,itemname,itemdefl)
        self._attrname=attrname
        self._attrdefl=attrdefl
    def __els__(self):
        return {}
    def __lsr__(self,dic,val):
        ent=cae(self.ent(),self._itemname,val)
        ent.set(self._attrname,dic[val])
        return ent
    def __lds__(self,dic,val):
        body=val.text.strip()
        attr=val.get(self._attrname)
        if attr is None:
            val.set(self._attrname,self._attrdefl)
            attr=self._attrdefl
        dic[body]=attr
        return dic

class Configurable:
    def __init__(self,conf,sect,indx=0):
        self._conf=None
        self._sect=sect
        self._indx=indx
        self._vars=[]
        self.schema()
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
    def value(self,name,defl=""):
        self._vars+=[ConfigValue(self,name,defl)]
        return self
    def list(self,name,itemname,defl=[],itemdefl=""):
        self._vars+=[ConfigList(self,name,defl,itemname,itemdefl)]
        return self
    def dict(self,name,itemname,attrname,defl={},itemdefl="",attrdefl=""):
        self._vars+=[ConfigDict(self,name,defl,itemname,itemdefl,attrname,attrdefl)]
        return self
    def setcfg(self):
        list([var.load() for var in self.cfgvars()])
        self.conf()
    def getcfg(self):
        self.sync()
        list([var.save() for var in self.cfgvars()])
    def indx(self):
        return self.__indx__()
    def sect(self):
        return self.__sect__()
    def cfgvars(self):
        return self.__vars__()
    def schema(self):
        self.__schema__()
    def __vars__(self):
        return self._vars
    def __schema__(self):
        pass
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
        except Exception as e:
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
