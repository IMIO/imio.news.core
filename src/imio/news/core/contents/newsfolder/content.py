# -*- coding: utf-8 -*-
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class INewsFolder(model.Schema):
    """Marker interface and Dexterity Python Schema for NewsFolder"""


@implementer(INewsFolder)
class NewsFolder(Container):
    """NewsFolder class"""
