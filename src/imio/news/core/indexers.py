# -*- coding: utf-8 -*-

from imio.news.core.contents.newsitem.content import INewsItem
from imio.news.core.utils import get_news_folder_for_news_item
from imio.smartweb.common.utils import translate_vocabulary_term
from plone import api
from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.app.contenttypes.indexers import _unicode_save_string_concat
from plone.app.textfield.value import IRichTextValue
from plone.indexer import indexer
from Products.CMFPlone.utils import safe_unicode

import copy


@indexer(INewsItem)
def translated_in_nl(obj):
    return bool(obj.title_nl)


@indexer(INewsItem)
def translated_in_de(obj):
    return bool(obj.title_de)


@indexer(INewsItem)
def translated_in_en(obj):
    return bool(obj.title_en)


@indexer(INewsItem)
def category_title(obj):
    if obj.category is not None:
        return translate_vocabulary_term(
            "imio.news.vocabulary.NewsCategories", obj.category
        )


@indexer(INewsItem)
def title_fr(obj):
    return obj.title


@indexer(INewsItem)
def title_nl(obj):
    if not obj.title_nl:
        raise AttributeError
    return obj.title_nl


@indexer(INewsItem)
def title_de(obj):
    if not obj.title_de:
        raise AttributeError
    return obj.title_de


@indexer(INewsItem)
def title_en(obj):
    if not obj.title_en:
        raise AttributeError
    return obj.title_en


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


@indexer(INewsItem)
def SearchableText_news_item(obj):

    def get_text(lang):
        text = ""
        if lang == "fr":
            textvalue = IRichText(obj).text
        else:
            textvalue = getattr(IRichText(obj), f"text_{lang}")
        if IRichTextValue.providedBy(textvalue):
            transforms = api.portal.get_tool("portal_transforms")
            raw = safe_unicode(textvalue.raw)
            text = (
                transforms.convertTo(
                    "text/plain",
                    raw,
                    mimetype=textvalue.mimeType,
                )
                .getData()
                .strip()
            )
        return text

    topics = []
    for topic in getattr(obj.aq_base, "topics", []) or []:
        topics.append(
            translate_vocabulary_term("imio.smartweb.vocabulary.Topics", topic)
        )

    category = translate_vocabulary_term(
        "imio.news.vocabulary.NewsCategories", getattr(obj.aq_base, "category", None)
    )
    subjects = obj.Subject()
    result = " ".join(
        (
            safe_unicode(obj.title) or "",
            safe_unicode(obj.description) or "",
            safe_unicode(get_text("fr")),
            safe_unicode(obj.title_nl) or "",
            safe_unicode(obj.description_nl) or "",
            safe_unicode(get_text("nl")),
            safe_unicode(obj.title_de) or "",
            safe_unicode(obj.description_de) or "",
            safe_unicode(get_text("de")),
            safe_unicode(obj.title_en) or "",
            safe_unicode(obj.description_en) or "",
            safe_unicode(get_text("en")),
            *topics,
            *subjects,
            safe_unicode(category),
        )
    )
    return _unicode_save_string_concat(result)
