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
    catalog = api.portal.get_tool("portal_catalog")

    new_indexes = ["translated_in_nl", "translated_in_de", "translated_in_en"]
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

    new_metadatas = ["title_fr", "title_nl", "title_de", "title_en"]
    metadatas = list(catalog.schema())
    must_reindex = False
    for new_metadata in new_metadatas:
        if new_metadata in metadatas:
            continue
        catalog.addColumn(new_metadata)
        must_reindex = True
        logger.info(f"Added {new_metadata} metadata")
    if must_reindex:
        logger.info("Reindexing catalog for new metadatas")
        catalog.clearFindAndRebuild()


def reindex_catalog(context):
    catalog = api.portal.get_tool("portal_catalog")
    catalog.clearFindAndRebuild()


def remove_searchabletext_fr(context):
    catalog = api.portal.get_tool("portal_catalog")
    catalog.manage_delIndex("SearchableText_fr")


def remove_title_description_fr(context):
    catalog = api.portal.get_tool("portal_catalog")
    catalog.delColumn("title_fr")
    catalog.delColumn("description_fr")


def migrate_local_categories(context):
    brains = api.content.find(portal_type=["imio.news.Entity"])
    for brain in brains:
        obj = brain.getObject()
        if obj.local_categories:
            categories = obj.local_categories.splitlines()
            datagrid_categories = [
                {"fr": cat, "nl": "", "de": "", "en": ""} for cat in categories
            ]
            obj.local_categories = datagrid_categories
            logger.info(
                "Categories migrated to Datagrid for entity {}".format(obj.Title())
            )


def unpublish_news_in_private_newsfolders(context):
    brains = api.content.find(
        portal_type=["imio.news.NewsFolder"], review_state="private"
    )
    for brain in brains:
        news_brains = api.content.find(
            context=brain.getObject(),
            portal_type=["imio.news.NewsItem"],
            review_state="published",
        )
        for n_brain in news_brains:
            news = n_brain.getObject()
            api.content.transition(news, "retract")
            logger.info("News {} go to private status".format(news.absolute_url()))


def reindex_newsfolders_and_folders(context):
    brains = api.content.find(portal_type=["imio.news.NewsFolder", "imio.news.Folder"])
    for brain in brains:
        brain.getObject().reindexObject()
