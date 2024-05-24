# -*- coding: utf-8 -*-

from imio.news.core.contents import IFolder
from imio.news.core.contents import INewsFolder
from imio.news.core.contents import INewsItem
from imio.news.core.interfaces import IImioNewsCoreLayer
from imio.smartweb.common.rest.utils import get_restapi_query_lang
from plone import api
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from plone.restapi.serializer.summary import DefaultJSONSummarySerializer
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer
from zope.interface import Interface
from zope.schema.interfaces import IVocabularyFactory


def get_container_uid(event_uid, summary=None):
    if summary is not None:
        container_uid = summary.get("UID") or summary.get("container_uid")
        if container_uid:
            return container_uid
    brain = api.content.find(UID=event_uid)[0]
    container_uid = getattr(brain, "container_uid", None)
    return container_uid


@implementer(ISerializeToJson)
@adapter(INewsItem, IImioNewsCoreLayer)
class SerializeNewsItemToJson(SerializeFolderToJson):
    def __call__(self, version=None, include_items=True):
        result = super(SerializeNewsItemToJson, self).__call__(
            version, include_items=True
        )
        query = self.request.form
        lang = get_restapi_query_lang(query)
        title = result["title"]
        text = result["text"]
        desc = result["description"]

        if lang and lang != "fr":
            result["title"] = result[f"title_{lang}"]
            result["description"] = result[f"description_{lang}"]
            result["text"] = result[f"text_{lang}"]
            if self.context.local_category:
                factory = getUtility(
                    IVocabularyFactory, "imio.news.vocabulary.NewsLocalCategories"
                )
                vocabulary = factory(self.context, lang=lang)
                term = vocabulary.getTerm(self.context.local_category)
                result["local_category"] = {
                    "token": self.context.local_category,
                    "title": term.title,
                }

        # Getting news folder title/id to use it in rest views
        if query.get("metadata_fields") is not None and "container_uid" in query.get(
            "metadata_fields"
        ):
            newsfolder = None
            news_uid = self.context.UID()
            container_uid = get_container_uid(news_uid)
            if container_uid is not None:
                # newsfolder can be private (admin to access them). That doesn't stop events to be bring.
                with api.env.adopt_user(username="admin"):
                    newsfolder = api.content.get(UID=container_uid)
                # To make a specific newsfolder css class in smartweb carousel common template
                result["usefull_container_id"] = newsfolder.id
                # To display newsfolder title in smartweb carousel common template
                result["usefull_container_title"] = newsfolder.title

        # maybe not necessary :
        result["title_fr"] = title
        result["description_fr"] = desc
        result["text_fr"] = text
        return result


@implementer(ISerializeToJsonSummary)
@adapter(Interface, IImioNewsCoreLayer)
class NewsItemJSONSummarySerializer(DefaultJSONSummarySerializer):
    def __call__(self):
        summary = super(NewsItemJSONSummarySerializer, self).__call__()
        query = self.request.form
        # To get news folder title and use it in carousel,...
        if query.get("metadata_fields") is not None and "container_uid" in query.get(
            "metadata_fields"
        ):
            news_folder = None
            if INewsItem.providedBy(self.context):
                news_uid = self.context.UID()
                container_uid = get_container_uid(news_uid)
            elif INewsFolder.providedBy(self.context) or IFolder.providedBy(
                self.context
            ):
                container_uid = get_container_uid(None, summary)
            elif INewsItem.providedBy(self.context.getObject()):
                # context can be a brain
                news_uid = self.context.UID
                container_uid = get_container_uid(news_uid)
            else:
                container_uid = get_container_uid(None, summary)
            # News folders can be private (admin to access them). That doesn't stop news to be bring.
            with api.env.adopt_user(username="admin"):
                news_folder = api.content.get(UID=container_uid)
            if not news_folder:
                return summary
            # To make a specific news folder css class in smartweb carousel common template
            summary["usefull_container_id"] = news_folder.id
            # To display news folder title in smartweb carousel common template
            summary["usefull_container_title"] = news_folder.title
        lang = get_restapi_query_lang(query)
        if lang == "fr":
            # nothing to go, fr is the default language
            return summary

        obj = IContentListingObject(self.context)
        for orig_field in ["title", "description", "category_title", "local_category"]:
            field = f"{orig_field}_{lang}"
            accessor = self.field_accessors.get(field, field)
            value = getattr(obj, accessor, None) or None
            try:
                if callable(value):
                    value = value()
            except WorkflowException:
                summary[orig_field] = None
                continue
            if orig_field == "description" and value is not None:
                value = value.replace("**", "")
            summary[orig_field] = json_compatible(value)

        return summary
