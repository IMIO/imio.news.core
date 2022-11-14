# -*- coding: utf-8 -*-

from imio.news.core.utils import reload_faceted_config
from imio.smartweb.common.upgrades import upgrades
from plone import api
from zope.globalrequest import getRequest

import logging

logger = logging.getLogger("imio.news.core")


def refresh_objects_faceted(context):
    request = getRequest()
    brains = api.content.find(portal_type=["imio.news.Entity", "imio.news.NewsFolder"])
    for brain in brains:
        obj = brain.getObject()
        reload_faceted_config(obj, request)
        logger.info("Faceted refreshed on {}".format(obj.Title()))


def reindex_searchable_text(context):
    upgrades.reindex_searchable_text(context)


def add_translations_indexes(context):
    new_indexes = ["translated_in_nl", "translated_in_de", "translated_in_en"]
    catalog = api.portal.get_tool("portal_catalog")
    indexes = catalog.indexes()
    indexables = []
    for new_index in new_indexes:
        if new_index in indexes:
            continue
        catalog.addIndex(new_index, "BooleanIndex")
        indexables.append(new_index)
        logger.info(f"Added BooleanIndex for field {new_index}")
    if len(indexables) > 0:
        logger.info(f"Indexing new indexes {', '.join(indexables)}")
        catalog.manage_reindexIndex(ids=indexables)
