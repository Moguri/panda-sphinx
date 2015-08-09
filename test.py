import re

data = """

asdasdasd 
 <code python>
  ficken 200
 </code>
 <code p>asd</code>
"""

print re.sub(r"(<code.*?>)(.*?)(</code>)", r"\1<![CDATA[\2]]>\3", data, flags=re.DOTALL)

