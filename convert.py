#!/usr/bin/env python3

import os, sys
import re
import tempfile
import subprocess
from bs4 import BeautifulSoup
from bs4.element import *
from hashlib import sha1

KEEP=["b", "i", "u", "strong", "em", "blockquote"]
CODE=["code", "pre", "syntaxhighlight"]
REMOVE=["div", "span", "html", "head", "body", "p", "font", "big"]

REMOVE_AND_NEWLINE = ["center"]

AS_HTML=["table", "h1", "h2", "h3", "h4", "h5", "ol", "ul"]

LANG_SWITCH=["python", "cxx"]

CONTENTS = dict()



class Converter(object):
    def __init__(self, elem):
        self.elem = elem

    def output(self):
        raise NotImplementedError

class HTML(Converter):
    def output(self):
        self.pipe = subprocess.Popen(['pandoc', '-fhtml', '-trst', '-F./filter.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self.pipe.communicate(str(self.elem).encode("utf-8"))[0].decode("utf-8")

class LangSwitch(Converter):
    def output(self):
        pipe = Pandoc().convert(self.elem)


        res = ["""
.. only:: {}

""".format(self.elem.name)]

        for line in pipe.stdout:
            translated_line = re.sub(r"XXXREPLACE-([0-9a-f]+)XXX", replacer, line.decode("utf-8"))
            res.extend('    ' + tl for tl in translated_line.splitlines(True))

        return "".join(res)    

    
class Code(Converter):
    @staticmethod
    def dump(text):
        return "".join(u"    " + line for line in text.splitlines(True))

    def output(self):
        r = []
        if len(list(self.elem.descendants))>1:
            raise RuntimeError("invalid code object "+str(self.elem))
        if self.elem.attrs and self.elem.name != "pre":
            lang = str(list(self.elem.attrs.keys())[0])
            if self.elem.name == "syntaxhighlight":
                lang = self.elem["lang"]
            r.append("\n\n.. code-block:: " + ("cpp" if lang == "cxx" else lang)+"\n")
            code = str(self.elem.string)
            if not code.startswith("\n"):
                r.append("\n")
            r.append(self.dump(code))
            r.append("\n")
        else:
            t = str(self.elem.string)
            if "\n" not in t:
                r.append(u'``' + t + '``')
            else:
                r.append(u"::\n")
                r.append(self.dump(t))
        return "".join(r)


class Pandoc(object):
    
    def write(self, s):
        self.pipe.stdin.write(s.encode("utf-8"))

    def placeholder(self, conv, elem):
        global CONTENTS
        h = sha1(str(elem).encode("utf-8")).hexdigest()
        CONTENTS[h] = conv(elem)
        self.write("XXXREPLACE-" + h + "XXX")
        
    
    def handle(self, elem):
        if isinstance(elem, NavigableString):
            self.write(str(elem))

        elif isinstance(elem, Tag):
            if elem.name in CODE:
                self.placeholder(Code, elem)
            elif elem.name == "br":
                self.write("\n\n")
                for ch in elem.children:
                    self.handle(ch)
            elif elem.name in KEEP:
                self.write("<" + elem.name + ">")
                for ch in elem.children:
                    self.handle(ch)
                self.write("</" + elem.name + ">")
            elif elem.name in REMOVE:
                for ch in elem.children:
                    self.handle(ch)
            elif elem.name in REMOVE_AND_NEWLINE:
                for ch in elem.children:
                    self.handle(ch)
                self.write("\n")
            elif elem.name in AS_HTML:
                if elem.name in ["table", "ol", "ul"]:
                    self.write("\n")
                self.placeholder(HTML, elem)
                self.write("\n")
            elif elem.name in LANG_SWITCH:
                self.placeholder(LangSwitch, elem)
                self.write("\n")
                
            else:
                raise RuntimeError("unknown tag "+elem.name)
        else:
            raise RuntimeError("Unknown type "+str(type(elem)))


    def convert(self, root):
        self.pipe = subprocess.Popen(["pandoc", "-fmediawiki", "-trst", '-F./filter.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #pipe = subprocess.Popen(["cat"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        for elem in root:
            self.handle(elem)

        self.pipe.stdin.close()
        return self.pipe
    


    
with open(sys.argv[1], "rt", encoding="utf-8") as f:
    data = f.read()

    
# fix borked code

# convert mediawiki tags to html (and also the python/cxx pseudotags)

data = re.sub(r"\[(/?(code|python|cxx))\]", r"<\1>", data)

# add CDATA to code blocks
data = re.sub(r"(<(code|pre|syntaxhighlight).*?>)(.*?)(</\2>)", r"\1<![CDATA[\3]]>\4", data, flags=re.DOTALL)

# fix text that looks like tags
# some end with >, some don't, because we want for example to replace <object> but not <object ...> (the latter occurs in a code block which
# is already handled via CDATA
data = re.sub(r"<(your|object>|Texture>|char>|event name>|function>|parameters|param>|RGBA>)", r"&lt;\1", data)

data = re.sub(r"==$[^$]", u"==\n\n", data, flags=re.M)

data = re.sub(r"\[/?func\]", "", data)


# raise RuntimeError(data)

root = BeautifulSoup(data, 'html.parser')

pipe = Pandoc().convert(root)

def replacer(match):
    conv = CONTENTS[match.group(1)]
    return conv.output()

if True:
        
    sys.stdout.write("""..
  This file was automatically converted from MediaWiki syntax.
  If some markup is wrong, looks weird or doesn't make sense, feel free
  to fix it.

  Please remove this comment once this file was manually checked
  and no "strange ReST" artifacts remain.

""")

    title = sys.argv[1].split("/")[-1].replace(".txt", "").replace(" ", "-").replace('"', '').lower()

    sys.stdout.write(".. _{}:\n\n".format(title))

for i, line in enumerate(pipe.stdout):
    line = line.decode("utf-8")
    #sys.stdout.write(line)

    sys.stdout.write(re.sub(r"XXXREPLACE-([0-9a-f]+)XXX", replacer, line))

