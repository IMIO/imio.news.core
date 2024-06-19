# -*- coding: utf-8 -*-

from datetime import datetime
from DateTime import DateTime
from imio.news.core.contents import INewsFolder
from imio.news.core.contents import IEntity
from imio.news.core.contents import INewsItem
from imio.news.core.utils import get_news_folder_for_news_item
from imio.news.core.utils import get_entity_for_obj
from imio.smartweb.common.rest.odwb import OdwbBaseEndpointGet
from imio.smartweb.common.utils import (
    activate_sending_data_to_odwb_for_staging as odwb_staging,
)
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot

import json
import logging
import requests

logger = logging.getLogger("imio.news.core")


class OdwbEndpointGet(OdwbBaseEndpointGet):
    def __init__(self, context, request):
        imio_service = (
            "actualites-en-wallonie"
            if not odwb_staging()
            else "staging-actualites-en-wallonie"
        )
        pushkey = f"imio.news.core.odwb_{imio_service}_pushkey"
        super(OdwbEndpointGet, self).__init__(context, request, imio_service, pushkey)

    def reply(self):
        if not super(OdwbEndpointGet, self).available():
            return
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/push/?pushkey={self.odwb_pushkey}"
        self.__datas__ = self.get_news()
        batched_lst = [
            self.__datas__[i : i + 1000] for i in range(0, len(self.__datas__), 1000)
        ]
        for elem in batched_lst:
            payload = json.dumps(elem)
            response_text = self.odwb_query(url, payload)
            logger.info(response_text)
        return response_text

    def get_news(self):
        lst_news = []
        if IPloneSiteRoot.providedBy(self.context) or INewsFolder.providedBy(
            self.context
        ):
            brains = api.content.find(
                object_provides=INewsItem.__identifier__, review_state="published"
            )
            for brain in brains:
                if INewsFolder.providedBy(self.context):
                    if self.context.UID() not in brain.selected_news_folders:
                        continue
                news_obj = brain.getObject()
                news = News(news_obj)
                lst_news.append(json.loads(news.to_json()))
        elif INewsItem.providedBy(self.context):
            news = News(self.context)
            lst_news.append(json.loads(news.to_json()))
        return lst_news

    def remove(self):
        if not super(OdwbEndpointGet, self).available():
            return
        lst_news = []
        if INewsItem.providedBy(self.context):
            news = News(self.context)
            lst_news.append(json.loads(news.to_json()))
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/delete/?pushkey={self.odwb_pushkey}"
        payload = json.dumps(lst_news)
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.text


class News:

    def __init__(self, context):
        self.id = context.id
        self.title = context.title
        self.description = context.description
        self.image = f"{context.absolute_url()}/@@images/image/preview"
        self.category = context.category
        self.topics = context.topics
        self.text = context.text.raw if context.text else None
        self.facebook_url = context.facebook
        self.instagram_url = context.instagram
        self.twitter_url = context.twitter
        self.video_url = context.video_url
        self.owner_id = get_entity_for_obj(context).UID()
        self.owner_name = get_entity_for_obj(context).Title()
        self.owner_news_folder_id = get_news_folder_for_news_item(context).UID()
        self.owner_news_folder_name = get_news_folder_for_news_item(context).Title()
        # DateTime(2024/02/14 13:59:7.829612 GMT+1),
        self.creation_datetime = context.creation_date
        # DateTime(2024/02/14 15:51:52.128648 GMT+1),
        self.modification_datetime = context.modification_date

        self.description_de = context.description_de
        self.description_en = context.description_en
        self.description_nl = context.description_nl
        # DateTime(2024/02/14 13:59:00 GMT+1),
        self.effective_date = context.effective_date
        # datetime.datetime(2024, 2, 14, 13, 0, tzinfo=<UTC>),
        self.exclude_from_nav = context.exclude_from_nav
        self.expiration_date = context.expiration_date
        self.iam = context.iam
        self.language = context.language
        self.local_category = context.local_category
        # datetime.datetime(2024, 2, 14, 12, 0, tzinfo=<UTC>),
        self.subjects = context.subject
        # self.taxonomy_event_public = context.taxonomy_event_public
        self.text_de = context.text_de.raw if context.text_de else None
        self.text_en = context.text_en.raw if context.text_en else None
        self.text_nl = context.text_nl.raw if context.text_nl else None
        self.title_de = context.title_de
        self.title_en = context.title_en
        self.title_nl = context.title_nl

    def to_json(self):
        return json.dumps(self.__dict__, cls=NewsEncoder)


class NewsEncoder(json.JSONEncoder):

    def default(self, attr):
        if isinstance(attr, DateTime):
            iso_datetime = attr.ISO8601()
            return iso_datetime
        elif isinstance(attr, datetime):
            return attr.isoformat()
        else:
            return super().default(attr)


class OdwbEntitiesEndpointGet(OdwbBaseEndpointGet):

    def __init__(self, context, request):
        imio_service = (
            "entites-des-actualites-en-wallonie"
            if not odwb_staging()
            else "staging-entites-des-actualites-en-wallonie"
        )
        pushkey = f"imio.news.core.odwb_{imio_service}_pushkey"
        super(OdwbEntitiesEndpointGet, self).__init__(
            context, request, imio_service, pushkey
        )

    def reply(self):
        if not super(OdwbEntitiesEndpointGet, self).available():
            return
        lst_entities = []
        brains = api.content.find(
            object_provides=IEntity.__identifier__, review_state="published"
        )
        for brain in brains:
            entity = {}
            entity["UID"] = brain.UID
            entity["id"] = brain.id
            entity["entity_title"] = brain.Title
            lst_entities.append(entity)
        self.__datas__ = lst_entities
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/push/?pushkey={self.odwb_pushkey}"
        payload = json.dumps(lst_entities)
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.text
