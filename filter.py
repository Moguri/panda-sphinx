#! /usr/bin/env python3
import sys

from pandocfilters import *

def convert_links(key, value, format, meta):
    if key == 'Link':
        title = stringify(value[0])
        target, target_type = value[1]
        if target_type == 'wikilink':
            target = target.replace("_", "-").replace('"', '').lower()
            if title.replace(" ","-").replace('"', '').lower() == target:
                #return RawInline('rst', title)
                return RawInline('rst', ':ref:`{}`'.format(target.strip()))
            else:
                return RawInline('rst', ':ref:`{} <{}>`'.format(title.strip(), target.strip()))

    elif key == 'Image':
        # remove caption, replace space with underscore
        return Image([], [x.replace(" ", "_") for x in value[1]])
            
    
toJSONFilter(convert_links)
