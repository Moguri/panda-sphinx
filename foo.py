from lxml import etree
import sys
import os

from common import transform_title

ignore_namespaces = ['Category', 'Dev', 'File', 'Help', 'MediaWiki',
                     'Panda3D Manual', 'Panda3D Wiki', 'Talk',
                     'Template', 'User talk', 'User']

if not os.path.isdir('pages'):
    os.mkdir('pages')

with open(sys.argv[1]) as f:
    root = etree.parse(f)

NS = dict(e = "http://www.mediawiki.org/xml/export-0.6/")

pages = root.xpath("//e:page", namespaces=NS)
basenames = set()

for page in pages:
    title = page.xpath("e:title/text()", namespaces=NS)[0]
    if ':'in title:
        namespace = title.split(':', 1)[0]
        if namespace in ignore_namespaces:
            continue

    basename = transform_title(title)

    t = page.xpath(".//e:text/text()", namespaces=NS)
    if t:
        # Take the last revision.
        t = t[-1].strip()

    if not t:
        # Ignore empty page
        print("Ignoring empty page %s" % (basename))
        continue

    if t.startswith('#REDIRECT'):
        # Ignore redirects.
        target = t.strip().split(' ', 1)[-1]
        #print("Ignoring %s, which is redirect to %s" % (basename, target))
        continue

    # Ensure there are no two non-redirect pages with the same name.
    assert basename not in basenames
    basenames.add(basename)

    with open("pages/{}.txt".format(basename), "wb") as f:
        # make it easy to link
        f.write("= {} =\n". format(title).encode("utf-8"))
        f.write(t.encode("utf-8"))

print("Wrote %s files to pages/" % (len(basenames)))
