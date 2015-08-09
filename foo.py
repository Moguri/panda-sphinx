from lxml import etree

with open("Panda3D+Manual-20150808210716.xml") as f:
   root = etree.parse(f)

NS = dict(e = "http://www.mediawiki.org/xml/export-0.6/")

pages = root.xpath("//e:page", namespaces=NS)

for page in pages:
    title = page.xpath("e:title/text()", namespaces=NS)[0]
    with open("pages/{}.txt".format(title.replace("/", "-")), "wt") as f:
        t = page.xpath(".//e:text/text()", namespaces=NS)
        # make it easy to link
        f.write("= {} =\n". format(title).encode("utf-8"))
        if t:
            t = t[0]
            f.write(t.encode("utf-8"))
