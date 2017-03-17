import xml.etree.ElementTree as xt
def x2d(element):
    return {tag: text for (tag,text) in [(child.tag,(x2d(child),child.text)) for child in element]}
def s2x(text):
    return xt.fromstring(text)
