# -*- coding: utf-8 -*-

from datetime import datetime
from DateTime import DateTime
from imio.news.core.contents import INewsFolder
from imio.news.core.contents import IEntity
from imio.news.core.contents import INewsItem
from imio.news.core.utils import get_news_folder_for_news_item
from imio.news.core.utils import get_entity_for_obj
from imio.smartweb.common.rest.odwb import OdwbBaseEndpointGet
from imio.smartweb.common.utils import is_log_active
from imio.smartweb.common.utils import (
    activate_sending_data_to_odwb_for_staging as odwb_staging,
)
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot

import itertools
import json
import logging
import os

logger = logging.getLogger("imio.news.core")


def _batched(iterable, n):
    """Backport of itertools.batched (Python 3.12+) for older runtimes."""
    it = iter(iterable)
    while batch := list(itertools.islice(it, n)):
        yield batch


class OdwbEndpointGet(OdwbBaseEndpointGet):
    def __init__(self, context, request):
        imio_service = (
            "actualites-en-wallonie"
            if not odwb_staging()
            else "staging-actualites-en-wallonie"
        )
        pushkey = f"imio.news.core.odwb_{imio_service}_pushkey"
        super(OdwbEndpointGet, self).__init__(context, request, imio_service, pushkey)
        self.__datas_count__ = 0

    def _log_odwb_response(self, action, count, response_text):
        """Log the ODWB response at INFO (success) or WARNING (error).

        action  : "push" or "delete"
        count   : number of items in the batch
        """
        verb = "sent/updated" if action == "push" else "deleted"
        try:
            data = json.loads(response_text)
            success = data.get("ok") or data.get("status") == "ok"
            if success:
                logger.info(
                    "ODWB %s: %d news item(s) %s — ODWB response: %s",
                    action,
                    count,
                    verb,
                    response_text,
                )
            else:
                logger.warning(
                    "ODWB %s: %d news item(s) — ODWB returned an error: %s",
                    action,
                    count,
                    response_text,
                )
        except (json.JSONDecodeError, AttributeError):
            # odwb_query returns a plain error string on network/HTTP exceptions
            logger.warning(
                "ODWB %s: %d news item(s) — unexpected response: %s",
                action,
                count,
                response_text,
            )

    def reply(self):
        if not super(OdwbEndpointGet, self).available():
            logger.info(
                "ODWB push skipped (not available) for %s",
                self.context.absolute_url(),
            )
            return
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/push/?pushkey={self.odwb_pushkey}"
        if is_log_active():
            logger.info(f"ODWB push url: {url}")
        self.__datas_count__ = 0
        responses = []
        for batch in _batched(self.get_news(), 500):
            self.__datas_count__ += len(batch)
            payload = json.dumps(list(batch))
            response_text = self.odwb_query(url, payload)
            self._log_odwb_response("push", len(batch), response_text)
            responses.append(response_text)
        logger.info(
            "ODWB push complete: %d news item(s) sent from %s",
            self.__datas_count__,
            self.context.absolute_url(),
        )
        if not responses:
            return None
        unique = set(responses)
        return responses[-1] if len(unique) == 1 else responses

    def get_news(self):
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
                yield json.loads(News(news_obj).to_json())
        elif IEntity.providedBy(self.context):
            brains = api.content.find(
                object_provides=INewsItem.__identifier__,
                review_state="published",
                path={"query": "/".join(self.context.getPhysicalPath()), "depth": -1},
            )
            for brain in brains:
                news_obj = brain.getObject()
                yield json.loads(News(news_obj).to_json())
        elif INewsItem.providedBy(self.context):
            yield json.loads(News(self.context).to_json())

    def remove(self):
        if not super(OdwbEndpointGet, self).available():
            logger.info(
                "ODWB delete skipped (not available) for %s",
                self.context.absolute_url(),
            )
            return
        url = f"{self.odwb_api_push_url}/{self.odwb_imio_service}/temps_reel/delete/?pushkey={self.odwb_pushkey}"
        if is_log_active():
            logger.info(f"ODWB delete url: {url}")
        deleted_count = 0
        responses = []
        for batch in _batched(self.get_news(), 500):
            deleted_count += len(batch)
            payload = json.dumps(list(batch))
            response_text = self.odwb_query(url, payload)
            self._log_odwb_response("delete", len(batch), response_text)
            responses.append(response_text)
        logger.info(
            "ODWB delete complete: %d news item(s) sent to ODWB delete endpoint from %s",
            deleted_count,
            self.context.absolute_url(),
        )
        if not responses:
            return None
        unique = set(responses)
        return responses[-1] if len(unique) == 1 else responses


class News:

    def __init__(self, context):
        self.id = context.id
        self.title = context.title
        self.description = context.description
        if context.image is not None:
            portal = api.portal.get()
            # context.absolute_url() depends on the current request URL, which may be an
            # internal IP when running upgrade steps directly (bypassing the reverse proxy).
            # ODWB is an external service and cannot reach internal addresses, so we use the
            # DOMAINS environment variable (already set in the deployment config) to build a
            # publicly accessible URL. Falls back to portal.absolute_url() when DOMAINS is not
            # set (e.g. in production where requests always go through the reverse proxy).
            domain = os.environ.get("DOMAINS", "")
            public_url = f"https://{domain}" if domain else portal.absolute_url()
            public_url = public_url.rstrip("/")
            context_subpath = "/".join(
                context.getPhysicalPath()[len(portal.getPhysicalPath()) :]
            )
            content_type = getattr(context.image, "contentType", "")
            scale = "" if content_type == "image/svg+xml" else "/preview"
            self.image = f"{public_url}/{context_subpath}/@@images/image{scale}"
            logger.info(
                "ODWB image for %s: type=%s, contentType=%s, size=%s, url=%s",
                context.absolute_url(),
                type(context.image).__name__,
                content_type,
                getattr(context.image, "size", "?"),
                self.image,
            )
        else:
            self.image = None
            logger.info(
                "ODWB image for %s: no lead image (context.image is None)",
                context.absolute_url(),
            )
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


class OdwbEndpointDelete(OdwbEndpointGet):
    def reply(self):
        return self.remove()


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
        if is_log_active():
            logger.info(f"ODWB push url: {url}")
        payload = json.dumps(lst_entities)
        return self.odwb_query(url, payload)
