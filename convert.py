#!/usr/bin/env python3

import os, sys
import re
import tempfile
import subprocess
from bs4 import BeautifulSoup
from bs4.element import *
from hashlib import sha1

KEEP=["b", "i", "u"]
CODE=["code", "pre"]
REMOVE=["div", "span", "html", "head", "body", "p"]

REMOVE_AND_NEWLINE = ["center"]

AS_HTML=["table", "h1", "h2", "h3"]

CONTENTS = dict()


pipe = subprocess.Popen(["pandoc", "-fmediawiki", "-trst", '-F./filter.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#pipe = subprocess.Popen(["cat"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

class Converter(object):
    def __init__(self, elem):
        self.elem = elem

    def output(self):
        raise NotImplementedError

class HTML(Converter):
    def output(self):
        pipe = subprocess.Popen(['pandoc', '-fhtml', '-trst', '-F./filter.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return pipe.communicate(str(self.elem).encode("utf-8"))[0].decode("utf-8")

class Code(Converter):
    @staticmethod
    def dump(text):
        return "".join(u"    " + line for line in text.splitlines(True))

    def output(self):
        r = []
        if len(list(self.elem.descendants))>1:
            raise RuntimeError("invalid code object "+str(self.elem))
        if self.elem.attrs:
            lang = str(list(self.elem.attrs.keys())[0])
            
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
        
def write(s):
    pipe.stdin.write(s.encode("utf-8"))

def placeholder(conv, elem):
    h = sha1(str(elem).encode("utf-8")).hexdigest()
    CONTENTS[h] = conv(elem)
    write("XXXREPLACE-" + h + "XXX")


    
def handle(elem):
    if isinstance(elem, NavigableString):
        write(str(elem))

    elif isinstance(elem, Tag):
        if elem.name in CODE:
            placeholder(Code, elem)
        elif elem.name == "br":
            write("\n\n")
            for ch in elem.children:
                handle(ch)
        elif elem.name in KEEP:
            write("<" + elem.name + ">")
            for ch in elem.children:
                handle(ch)
            write("</" + elem.name + ">")
        elif elem.name in REMOVE:
            for ch in elem.children:
                handle(ch)
        elif elem.name in REMOVE_AND_NEWLINE:
            for ch in elem.children:
                handle(ch)
            write("\n")
        elif elem.name in AS_HTML:
            if elem.name == "table":
                write("\n")
                placeholder(HTML, elem)
            
        else:
            raise RuntimeError("unknown tag "+elem.name)
    else:
        raise "Unknown type "+type(elem)


with open(sys.argv[1], "rt", encoding="utf-8") as f:
    data = f.read()


# fix borked code

data = re.sub(r"\[(/?code)\]", r"<\1>", data)
data = re.sub(r"(<(code|pre).*?>)(.*?)(</\1>)", r"\2<![CDATA[\3]]>\4", data, flags=re.DOTALL)
data = re.sub(r"<your", u"&lt;your", data)
data = re.sub(r"==$[^$]", u"==\n\n", data, flags=re.M)

data = re.sub(r"\[/?func\]", "", data)

parsed = BeautifulSoup(data, "html.parser")

for elem in parsed:
    handle(elem)

pipe.stdin.close()

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

