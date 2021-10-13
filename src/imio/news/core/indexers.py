# -*- coding: utf-8 -*-

from imio.news.core.contents.newsitem.content import INewsItem
from imio.news.core.utils import get_news_folder_for_news_item
from plone.indexer import indexer

import copy


@indexer(INewsItem)
def category_and_topics_indexer(obj):
    list = []
    if obj.topics is not None:
        list = copy.deepcopy(obj.topics)

    if obj.category is not None:
        list.append(obj.category)

    if obj.local_categories is not None:
        list.append(obj.local_category)
    return list


@indexer(INewsItem)
def container_uid(obj):
    uid = get_news_folder_for_news_item(obj).UID()
    return uid
