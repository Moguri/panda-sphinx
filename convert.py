#!/usr/bin/env python3

import os, sys
import re
import tempfile
import subprocess
from bs4 import BeautifulSoup
from bs4.element import *
from hashlib import sha1
from toolz import curry

from common import transform_title

KEEP=["b", "i", "u", "strong", "em", "blockquote", "sub", "sup"]
CODE=["code", "pre", "syntaxhighlight"]
REMOVE=["div", "span", "html", "head", "body", "p", "font", "big"]

REMOVE_AND_NEWLINE = ["center"]

AS_HTML=["table", "h1", "h2", "h3", "h4", "h5", "ol", "ul"]

LANG_SWITCH=["python", "cxx"]

CONTENTS = dict()



# set to '--columns=72' to allow wrapping
NOWRAP = '--columns=78' #'--no-wrap'

def replacer(char_follows):

    def matcher(match):
        conv = CONTENTS[match.group(1)]
        res = conv.output()
        if char_follows and not re.search(r"\s$", res):
            res += " "
        return res

    return matcher



class Converter(object):
    def __init__(self, elem):
        self.elem = elem

    def output(self):
        raise NotImplementedError

class HTML(Converter):
    def output(self):
        self.pipe = subprocess.Popen(['pandoc', '-fhtml', '-trst', '-F./filter.py', NOWRAP], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #print(self.elem.prettify(encoding="ascii", formatter="minimal").decode("ascii"))
        res = self.pipe.communicate(str(self.elem).encode("utf-8"))[0].decode("utf-8")
        return res
    
        
class LangSwitch(Converter):
    def output(self):
        pipe = Pandoc().convert(self.elem)

        lang = self.elem.name
        if lang == 'cxx':
            lang = 'cpp'

        res = ["""

.. only:: {}

""".format(lang)]

        for line in pipe.stdout:
            translated_line = replace_placeholders(line.decode("utf-8"))
            res.extend('    ' + tl for tl in translated_line.splitlines(True))

        return "".join(res)    



def replace_placeholders(line):
    translated_line = re.sub(r"XXXREPLACE-([0-9a-f]+)XXX *(?=\w)", replacer(char_follows=True), line)
    translated_line = re.sub(r"XXXREPLACE-([0-9a-f]+)XXX *(?!\w)", replacer(char_follows=False), translated_line)
    return translated_line

    
class Code(Converter):
    @staticmethod
    def dump(text):
        return "".join(u"    " + line for line in text.splitlines(True))

    @staticmethod
    def convert_langtag(lang):
        mapped = {
            "cxx": "cpp",
            "html4strict": "html",
            "prc": "text",
            "cg": "glsl", # not 100% correct, but who cares
            "egg": "text",
        }
        try:
            return mapped[lang]
        except KeyError:
            return lang
    
    def output(self):
        r = []
        if len(list(self.elem.descendants))>1:
            raise RuntimeError("invalid code object "+str(self.elem))
        if self.elem.attrs and self.elem.name != "pre":
            lang = str(list(self.elem.attrs.keys())[0])
            if self.elem.has_attr("lang"):
                lang = self.elem["lang"]
            assert lang != "lang", "invalid lang for elem"+str(self.elem)
            r.append("\n\n.. code-block:: " + self.convert_langtag(lang) + "\n")
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
                r.append("\n")
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
        self.pipe = subprocess.Popen(["pandoc", "-fmediawiki", "-trst", '-F./filter.py', NOWRAP], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #pipe = subprocess.Popen(["cat"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        for elem in root:
            self.handle(elem)

        self.pipe.stdin.close()
        return self.pipe


class CData:
    def __init__(self, s, sections):
        self.s = s
        self.sections = sections

    def replacer(self, match):
        return self.sections[match.group(1)]
    
    def restore(self, new_s):
        return re.sub(r"XXXCDATA-([0-9a-f]+)", self.replacer, new_s, flags=re.M|re.DOTALL)
    
def save_and_replace_cdata(s):

    content = {}
    def replace(match):
        h = sha1(match.group(1).encode("utf-8")).hexdigest()
        
        content[h] = match.group(1)
        return "XXXCDATA-"+h

    replaced = re.sub(r"(<!\[CDATA\[.*?\]\]>)", replace, s, flags=re.M|re.DOTALL)
    return CData(replaced, content)


if len(sys.argv) >= 2 and sys.argv[1] != '-':
    infile = open(sys.argv[1], "rt", encoding="utf-8")
else:
    infile = sys.stdin

with sys.stdin as f:
    data = f.read()

# replace weird python/c++ tags
data = data.replace('[;]', '')
data = data.replace('[::]', '.')
data = data.replace('[->]', '.')
data = data.replace('[func]', '')
data = data.replace('[/func]', '')

# Canonicalize Panda3D site URLs.
data = re.sub(r'https?://(www\.)?panda3d\.[orgnetcm]+(\.cmu\.edu)?', 'https://www.panda3d.org', data)
data = data.replace('//www.panda3d.org/phpbb2', '//www.panda3d.org/forums')
data = data.replace('//www.panda3d.org/wiki', '//www.panda3d.org/manual')

#data = data.replace("<code cxx>", '<code cpp>')
#data = re.sub(r'<code ([a-z]+)>(.*?)</code>', r'<syntaxhighlight lang="\1">\2</syntaxhighlight>', data)

# convert mediawiki tags to html (and also the python/cxx pseudotags)
data = re.sub(r"\[(/?(code|python|cxx))\]", r"<\1>", data)

# add CDATA to code blocks
data = re.sub(r"(<(code|pre|syntaxhighlight).*?>)(.*?)(</\2>)", r"\1<![CDATA[\3]]>\4", data, flags=re.DOTALL)


# pandoc gets confused if we use any form of < tag, even if it is written as &lt;
# (because of multiple passes, so we replace them with our own tag "\2" (instead of XXXLT)



# fix text that looks like tags
# some end with >, some don't, because we want for example to replace <object> but not <object ...> (the latter occurs in a code block which
# is already handled via CDATA
data = re.sub(r"<(your|object>|char>|event name>|function>|solid|parameters|param>|RGBA>|character's)", r"{}\1".format('\2'), data, flags=re.I)



# HACK, temporarily remove all cdata tags so our regexp doesn't do anything with them
cdata = save_and_replace_cdata(data)

#and some more, mainly from Egg Syntax, this time complete tags

data = re.sub(r"""
<(BFace|Billboard|Bundle|Collide|Comment|CoordinateSystem|Dart|DCS|Distance|Dxyz|DynamicVertexPool|
Entry-type|Group|Instance|Joint|Material|Model|MRef|MyClass|Normal|NurbsCurve|ObjectType|Polygon|Ref|S\$Anim|
Scalar|Switch|SwitchCondition|T|Tag|Texture|Transform|TRef|UV|V|Vertex|VertexPool|VertexRef
)>""", r"{}\1>".format('\2'), cdata.s, flags=re.I|re.M|re.VERBOSE)


data = cdata.restore(data)

# end of hack


data = re.sub(r"==$[^$]", u"==\n\n", data, flags=re.M)

data = re.sub(r"\[/?func\]", "", data)


root = BeautifulSoup(data, 'html.parser')

pipe = Pandoc().convert(root)


if False:
    sys.stdout.write("""..
  This file was automatically converted from MediaWiki syntax.
  If some markup is wrong, looks weird or doesn't make sense, feel free
  to fix it.

  Please remove this comment once this file was manually checked
  and no "strange ReST" artifacts remain.

""")

for i, line in enumerate(pipe.stdout):
    line = line.decode("utf-8")
    # restore escaped <
    line = line.replace('\2', '<')
    #sys.stdout.write(line)

    sys.stdout.write(replace_placeholders(line))

