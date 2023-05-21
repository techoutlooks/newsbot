from newsutils.conf import configure
if configure():
    from .crawlall import *
    from .nlp import *
    from .publish import *
