import icybot_xml
def setcfg(obj,cfg,*attrs):
    for attr in attrs:
        name = None
        try:
            if type(attr)==str:
                name=attr
                val=cfg.find(attr).text.strip()
            elif len(attr)==2:
                name=attr[0]
                val=[child.text.strip() for child in cfg.find(attr[0]).findall(attr[1])]
            elif len(attr)==3:
                name=attr[0]
                val={body: param for (body,param) in [(child.text.strip(),child.get(attr[2])) for child in cfg.find(attr[0]).findall(attr[1])]}
        except AttributeError:
            print("could not find config key %s"%attr)
        else:
            setattr(obj,"_%s"%(name),val)
