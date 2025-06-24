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
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

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


def get_category_title(obj, lang):
    if obj.category is not None:
        return translate_vocabulary_term(
            "imio.news.vocabulary.NewsCategories", obj.category, lang
        )
    raise AttributeError


@indexer(INewsItem)
def category_title_fr(obj):
    return get_category_title(obj, "fr")


@indexer(INewsItem)
def category_title_nl(obj):
    return get_category_title(obj, "nl")


@indexer(INewsItem)
def category_title_de(obj):
    return get_category_title(obj, "de")


@indexer(INewsItem)
def category_title_en(obj):
    return get_category_title(obj, "en")


def get_local_category(obj, lang):
    if not obj.local_category:
        raise AttributeError
    factory = getUtility(IVocabularyFactory, "imio.news.vocabulary.NewsLocalCategories")
    vocabulary = factory(obj, lang=lang)
    try:
        term = vocabulary.getTerm(obj.local_category)
        return term.title
    except LookupError:
        return obj.local_category


@indexer(INewsItem)
def local_category_nl(obj):
    return get_local_category(obj, "nl")


@indexer(INewsItem)
def local_category_de(obj):
    return get_local_category(obj, "de")


@indexer(INewsItem)
def local_category_en(obj):
    return get_local_category(obj, "en")


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
def description_nl(obj):
    if not obj.description_nl:
        raise AttributeError
    return obj.description_nl


@indexer(INewsItem)
def description_de(obj):
    if not obj.description_de:
        raise AttributeError
    return obj.description_de


@indexer(INewsItem)
def description_en(obj):
    if not obj.description_en:
        raise AttributeError
    return obj.description_en


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


def get_searchable_text(obj, lang):
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
        term = translate_vocabulary_term("imio.smartweb.vocabulary.Topics", topic, lang)
        topics.append(term)

    category = getattr(obj.aq_base, "category", None)
    category_term = translate_vocabulary_term(
        "imio.news.vocabulary.NewsCategories", category, lang
    )
    subjects = obj.Subject()
    title_field_name = "title"
    description_field_name = "description"
    if lang != "fr":
        title_field_name = f"{title_field_name}_{lang}"
        description_field_name = f"{description_field_name}_{lang}"

    result = " ".join(
        (
            safe_unicode(getattr(obj, title_field_name)) or "",
            safe_unicode(getattr(obj, description_field_name)) or "",
            safe_unicode(get_text(lang)) or "",
            *topics,
            *subjects,
            safe_unicode(category_term),
        )
    )
    return _unicode_save_string_concat(result)


@indexer(INewsItem)
def SearchableText_fr_news(obj):
    return get_searchable_text(obj, "fr")


@indexer(INewsItem)
def SearchableText_nl_news(obj):
    return get_searchable_text(obj, "nl")


@indexer(INewsItem)
def SearchableText_de_news(obj):
    return get_searchable_text(obj, "de")


@indexer(INewsItem)
def SearchableText_en_news(obj):
    return get_searchable_text(obj, "en")
