# -*- coding: utf-8 -*-

from imio.news.core.utils import get_news_folder_uid_for_news_item
from imio.smartweb.common.faceted.utils import configure_faceted
import os


def set_default_news_folder_uid(news_item):
    news_item.selected_news_folders = news_item.selected_news_folders or []
    uid = get_news_folder_uid_for_news_item(news_item)
    if uid not in news_item.selected_news_folders:
        news_item.selected_news_folders = news_item.selected_news_folders + [uid]
        news_item.reindexObject()


def init_faceted(obj):
    faceted_config_path = "{}/faceted/config/news.xml".format(os.path.dirname(__file__))
    configure_faceted(obj, faceted_config_path)


def added_entity(obj, event):
    init_faceted(obj)


def added_news_folder(obj, event):
    init_faceted(obj)


def added_news_item(obj, event):
    set_default_news_folder_uid(obj)


def modified_news_item(obj, event):
    set_default_news_folder_uid(obj)
