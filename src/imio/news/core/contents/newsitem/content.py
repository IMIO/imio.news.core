# -*- coding: utf-8 -*-
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.content import Container
from plone.supermodel import model
from plone.supermodel.interfaces import FIELDSETS_KEY
from plone.supermodel.model import Fieldset
from zope import schema
from zope.interface import implementer


class INewsItem(model.Schema):
    """Marker interface and Dexterity Python Schema for NewsItem"""

    video_url = schema.URI(
        title=_(u"Video url"),
        description=_(u"Video url from youtube, vimeo"),
        required=False,
    )

    site_url = schema.URI(
        title=_(u"Site"),
        description=_(u"NewsItem site url"),
        required=False,
    )

    facebook = schema.URI(
        title=_(u"Facebook"),
        description=_(u"Facebook url for this news"),
        required=False,
    )

    twitter = schema.URI(
        title=_(u"Twitter"),
        description=_(u"Twitter url for this news"),
        required=False,
    )

    instagram = schema.URI(
        title=_(u"Instagram"),
        description=_(u"Instgram url for this news"),
        required=False,
    )

    category = schema.Choice(
        title=_(u"Category"),
        source="imio.news.vocabulary.NewsCategories",
        required=True,
    )


@implementer(INewsItem)
class NewsItem(Container):
    """NewsItem class"""
