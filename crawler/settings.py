from settings_defaults import *


# scrapy
# ======

COMMANDS_MODULE = 'crawler.commands'


# news_utils (overrides)
# =========

POSTS = {
    "SIMILARITY_SIBLINGS_THRESHOLD": .1,
    "SIMILARITY_RELATED_THRESHOLD": .05,
    "SIMILARITY_MAX_DOCS": 5
}
