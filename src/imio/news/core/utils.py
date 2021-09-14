# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from Acquisition import aq_parent
from imio.news.core.contents import INewsFolder


def get_news_folder_uid_for_news_item(news_item):
    obj = news_item
    while not INewsFolder.providedBy(obj):
        parent = aq_parent(aq_inner(obj))
        obj = parent
    news_folder = obj
    return news_folder.UID()
