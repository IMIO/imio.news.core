# -*- coding: utf-8 -*-

from plone import api
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer
import os


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "imio.news.core:uninstall",
        ]


def post_install(context):
    """Post install script"""
    portal = api.portal.get()
    default_entity = api.content.create(
        type="imio.news.Entity", title="Imio", container=portal
    )
    faceted_config = "/faceted/config/news.xml"
    # Create global faceted newsfolder
    faceted = api.content.create(
        type="imio.news.NewsFolder", title="News folder", container=default_entity
    )
    subtyper = faceted.restrictedTraverse("@@faceted_subtyper")
    subtyper.enable()
    with open(os.path.dirname(__file__) + faceted_config, "rb") as faceted_config:
        faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
            import_file=faceted_config
        )


def uninstall(context):
    """Uninstall script"""
