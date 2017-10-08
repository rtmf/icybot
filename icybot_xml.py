import xml.etree.ElementTree as xt
def x2d(element):
    return {tag: text for (tag,text) in [(child.tag,(x2d(child),child.text)) for child in element]}
def s2x(text):
    return xt.fromstring(text)
def x2s(tree):
    return xt.tostring(tree)
def cae(cfg,name,text="",**attrib):
    ele=v2e(name,text,**attrib)
    cfg.append(ele)
    return ele
def v2e(name,text="",**attrib):
    ele=xt.Element(name,**attrib)
    ele.text=text
    return ele
