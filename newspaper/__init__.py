# -*- coding: utf-8 -*-
"""
Wherever smart people work, doors are unlocked. -- Steve Wozniak
"""
__title__ = 'newspaper'
__author__ = 'Tri Songz'
__license__ = 'MIT'
__copyright__ = 'Original Copyright 2014, Lucas Ou-Yang et al., Updated Copyright 2021, Tri Songz'

from .api import (build, build_article, fulltext, hot, languages,
                  popular_urls, Configuration as Config)
from .article import Article, ArticleException
from .gnews import GNews, GNewsCache
from .mthreading import NewsPool
from .source import Source
from .version import __version__

news_pool = NewsPool()

# Set default logging handler to avoid "No handler found" warnings.
import logging

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
