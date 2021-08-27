# -*- coding: utf-8 -*-

from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.content import Container
from plone.supermodel import model
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
        title=_(u"Website"),
        description=_(u"NewsItem website url"),
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
        description=_(u"Instagram url for this news"),
        required=False,
    )

    model.fieldset("categorization", fields=["category", "local_category"])
    category = schema.Choice(
        title=_(u"Category"),
        description=_(
            u"Important! These categories are used to supplement the information provided by the topics"
        ),
        source="imio.news.vocabulary.NewsCategories",
        required=False,
    )

    local_category = schema.Choice(
        title=_(u"Specific category"),
        description=_(
            u"Important! These categories allow you to use criteria that are specific to your organization"
        ),
        source="imio.news.vocabulary.NewsLocalCategories",
        required=False,
    )


@implementer(INewsItem)
class NewsItem(Container):
    """NewsItem class"""
