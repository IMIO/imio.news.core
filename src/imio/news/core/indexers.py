# -*- coding: utf-8 -*-

from plone.indexer import indexer
from imio.news.core.contents.newsitem.content import INewsItem


@indexer(INewsItem)
def category_and_topics_indexer(obj):
    list = []
    if obj.topics is not None:
        list = obj.topics

    if obj.category is not None:
        list.append(obj.category)

    if obj.local_categories is not None:
        list.append(obj.local_category)
    return list
