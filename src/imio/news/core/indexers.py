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
def description_fr(obj):
    if not obj.description:
        raise AttributeError
    return obj.description


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
        topics.append(
            translate_vocabulary_term("imio.smartweb.vocabulary.Topics", topic)
        )

    category = translate_vocabulary_term(
        "imio.news.vocabulary.NewsCategories", getattr(obj.aq_base, "category", None)
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
            safe_unicode(category),
        )
    )
    return _unicode_save_string_concat(result)


@indexer(INewsItem)
def SearchableText_fr_contact(obj):
    return get_searchable_text(obj, "fr")


@indexer(INewsItem)
def SearchableText_nl_contact(obj):
    return get_searchable_text(obj, "nl")


@indexer(INewsItem)
def SearchableText_de_contact(obj):
    return get_searchable_text(obj, "de")


@indexer(INewsItem)
def SearchableText_en_contact(obj):
    return get_searchable_text(obj, "en")
