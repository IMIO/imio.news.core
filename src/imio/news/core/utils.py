# -*- coding: utf-8 -*-

from imio.news.core.contents import INewsFolder
from Products.CMFPlone.utils import parent


def get_news_folder_for_news_item(news_item):
    obj = news_item
    while not INewsFolder.providedBy(obj):
        obj = parent(obj)
    news_folder = obj
    return news_folder
