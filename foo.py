from lxml import etree
import sys
import os
import subprocess
import shutil
import json

from common import *

# Pages under these namespaces won't be converted.
ignore_namespaces = ['Category', 'Dev', 'File', 'Help', 'MediaWiki',
                     'Panda3D Manual', 'Panda3D Wiki', 'Talk',
                     'Template', 'User talk', 'User']

# Create the pages dir, if it doesn't exist.
if not os.path.isdir('pages'):
    os.mkdir('pages')

# Parse the MediaWiki xml dump.
with open(sys.argv[1]) as f:
    root = etree.parse(f)

NS = dict(e = "http://www.mediawiki.org/xml/export-0.6/")

pages = root.xpath("//e:page", namespaces=NS)
paths = set()
num_errors = 0
num_images = 0

# Catalogue all images in the images dir.
all_images = {}
for image in os.listdir('manual-images'):
    name = transform_title(image)
    assert name not in all_images
    all_images[name] = os.path.join('manual-images', image)

# The first page should be the main page.
main_page = pages.pop(0)
assert main_page.xpath("e:title/text()", namespaces=NS)[0] == 'Main Page'
t = main_page.xpath(".//e:text/text()", namespaces=NS)[-1]

# Parse the table of contents from the main page contents.
parse_toc_tree(t.strip())
write_toc_tree('toctree.json')

# Write out the toc tree in RST form for the main page.
with open("source/index.rst", "wb") as f:
    children = get_page_children('Main Page') or []

    f.write(b'Table of Contents\n')
    f.write(b'=================\n')
    f.write(b'\n')
    f.write(b'.. toctree::\n')
    f.write(b'   :titlesonly:\n\n')

    for child in children:
        f.write(b'   ' + (child.encode('utf-8')))
        f.write(b'\n')


# Find all of the redirects.
redirects = {}
for page in pages:
    title = page.xpath("e:title/text()", namespaces=NS)[0]
    t = page.xpath(".//e:text/text()", namespaces=NS)

    if t:
        # Take the last revision.
        t = t[-1].strip()

    if t and t.startswith('#') and t.upper().startswith('#REDIRECT'):
        # Ignore redirects.
        target = t.strip().split(' ', 1)[-1].strip('[]')
        redirects[title] = target

# Store the redirects to disk.
json.dump(redirects, open('redirects.json', 'w'))


# Convert all of the other pages.
for i, page in enumerate(pages):
    progress = (100 * i) // (len(pages) - 1)

    title = page.xpath("e:title/text()", namespaces=NS)[0]
    if title in redirects:
        # Ignore redirects.
        continue

    if ':'in title:
        namespace = title.split(':', 1)[0]
        if namespace in ignore_namespaces:
            continue

    transformed = transform_title(title)
    path = get_page_path(title)

    if not path:
        # Not in table of contents.  Skip.
        continue

    t = page.xpath(".//e:text/text()", namespaces=NS)
    if t:
        # Take the last revision.
        t = t[-1].strip()

    if not t:
        # Ignore empty page
        print("Ignoring empty page %s" % (path))
        continue

    # Ensure there are no two non-redirect pages with the same name.
    assert path not in paths
    paths.add(path)

    # Make sure the parent directory exists.
    parent = 'source'
    if '/' in path:
        parent = "source/{}".format(os.path.dirname(path))
        if not os.path.isdir(parent):
            os.makedirs(parent)

    # Find all the image references on this page.
    for image in re.findall(r'[[][[]Image:([^|\]]+)[|\]]', t):
        name = transform_title(image)
        source = all_images.get(name)
        if not source:
            print("\nWarning: missing image %s" % (source))
            continue
        target = os.path.join(parent, name)
        shutil.copyfile(source, target)
        num_images += 1

    with open("source/{}.rst".format(path), "wb") as f:
        #print("converting %s" % (path))
        print("\x1b[1Fconverting [%+3s%%] \x1b[1m%s\x1b[m\x1b[K" % (progress, path))

        # Write an anchor so we can refer to this page.
        f.write(".. _{}:\n\n".format(transformed).encode('utf-8'))
        f.flush()

        handle = subprocess.Popen(["./convert.py", "-"], stdin=subprocess.PIPE, stdout=f)

        # Prepend a first-level header containing the page title.
        data = "= {} =\n". format(title.replace('CXX', 'C++')).encode("utf-8")
        data += t.encode("utf-8")
        handle.communicate(data)

        if handle.returncode != 0:
            print()
            num_errors += 1

        # If this page has children, write out a toc tree at the bottom.
        children = get_page_children(title)
        if children:
            f.write(b'\n\n.. toctree::\n')
            f.write(b'   :maxdepth: 2\n')
            f.write(b'\n')

        for child in children:
            f.write(b'   ' + (child.encode('utf-8')))
            f.write(b'\n')

print("Wrote %s files to source/ (%d had errors). %d images copied." % (len(paths), num_errors, num_images))
