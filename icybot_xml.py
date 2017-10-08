import lxml.etree as xt
def x2d(element):
    return {tag: text for (tag,text) in [(child.tag,(x2d(child),child.text)) for child in element]}
def s2x(text):
    return xt.fromstring(text)
def x2s(tree):
    return xt.tounicode(tree,pretty_print=True)
def cae(cfg,name,text="",**attrib):
    ele=xt.SubElement(cfg,name,attrib)
    ele.text=text
    return ele
