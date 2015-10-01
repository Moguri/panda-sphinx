import re

def transform_title(title):
    title = title.replace('CXX', 'C++')
    title = re.sub(r'[_ /]', '-', title)
    title = re.sub(r'[^a-zA-Z0-9-+]', '', title)
    title = re.sub(r'-+', '-', title)
    return title.lower()
