# -*- coding: utf-8 -*-
from imio.news.core.interfaces import IImioNewsCoreLayer
from imio.news.core.testing import IMIO_NEWS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

import unittest


class TestNewsItemSerializers(unittest.TestCase):
    layer = IMIO_NEWS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        alsoProvides(self.request, IImioNewsCoreLayer)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        # Contenu de base
        self.entity1 = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="entity1",
            title="Entity 1",
        )
        self.news_folder1 = api.content.create(
            container=self.entity1,
            type="imio.news.NewsFolder",
            id="news_folder1",
            title="News folder 1",
        )
        self.news1 = api.content.create(
            container=self.news_folder1,
            type="imio.news.NewsItem",
            id="news1",
            title="News 1",
            description="Desc FR",
            text={"data": "<p>Texte FR</p>", "mime-type": "text/html"},
        )

    def test_serialize_newsitem_default_fr(self):
        """FR est la langue par défaut: les champs fr sont reflétés."""
        serializer = getMultiAdapter((self.news1, self.request), ISerializeToJson)
        data = serializer()

        self.assertEqual(data["title"], "News 1")
        self.assertEqual(data["description"], "Desc FR")

        self.assertEqual(data["title_fr"], "News 1")
        self.assertEqual(data["description_fr"], "Desc FR")
        self.assertIn("text_fr", data)

        self.assertNotIn("usefull_container_id", data)
        self.assertNotIn("usefull_container_title", data)

    def test_serialize_newsitem_switch_language_en(self):
        """When lang != fr, serializer switch to suffixed fields."""
        self.entity1.local_categories = [
            {
                "de": "",
                "en": "local category EN",
                "fr": "catégorie spécifique",
                "nl": "",
            }
        ]

        self.news1.title_en = "News 1 EN"
        self.news1.description_en = "Desc EN"
        self.news1.text_en = {"data": "<p>Text EN</p>", "mime-type": "text/html"}
        self.news1.reindexObject()
        newsfolder_uid = self.news_folder1.UID()
        # Guest language in query (translated_in_en)
        self.request.form = {
            "selected_news_folders": newsfolder_uid,
            "portal_type": "imio.news.NewsItem",
            "metadata_fields": [
                "category",
                "local_category",
                "container_uid",
                "topics",
                "has_leadimage",
                "UID",
            ],
            "sort_on": "effective",
            "sort_order": "descending",
            "b_size": "20",
            "b_start": "0",
            "fullobjects": "1",
            "translated_in_en": "1",
        }
        # By default, we've got local_category in French but in query, we ask for english
        self.news1.local_category = "catégorie spécifique"
        serializer = getMultiAdapter((self.news1, self.request), ISerializeToJson)
        data = serializer()
        self.assertEqual(data["local_category"].get("title"), "local category EN")
        self.assertEqual(data["title"], "News 1 EN")
        self.assertEqual(data["description"], "Desc EN")
        self.assertEqual(data["title_fr"], "News 1")
        self.assertEqual(data["description_fr"], "Desc FR")
        self.assertIn("text_fr", data)
        self.assertIn("text", data)

    def test_summary_newsitem_default_fr(self):
        """Summary de NewsItem en FR (lang par défaut)."""
        summary = getMultiAdapter((self.news1, self.request), ISerializeToJsonSummary)()

        self.assertEqual(summary.get("title"), "News 1")
        self.assertIn("description", summary)

    def test_summary_newsitem_switch_language_en(self):
        """Summary de NewsItem: bascule de langue pour title/description/etc."""
        self.news1.title_en = "News 1 EN"
        self.news1.description_en = "Desc EN"
        # category_title/local_category_* ne sont testés que si présents sur l'obj/catalog
        self.news1.reindexObject()
        newsfolder_uid = self.news_folder1.UID()
        self.request.form = {
            "selected_news_folders": newsfolder_uid,
            "portal_type": "imio.news.NewsItem",
            "metadata_fields": [
                "category",
                "local_category",
                "container_uid",
                "topics",
                "has_leadimage",
                "UID",
            ],
            "sort_on": "effective",
            "sort_order": "descending",
            "b_size": "20",
            "b_start": "0",
            "fullobjects": "1",
            "translated_in_en": "1",
        }
        summary = getMultiAdapter((self.news1, self.request), ISerializeToJsonSummary)()
        self.assertEqual(summary.get("title"), "News 1 EN")
        self.assertEqual(summary.get("description"), "Desc EN")

    def test_summary_with_brain_context(self):
        """Le sérialiseur supporte aussi un brain (catalog brain)."""
        brain = api.content.find(UID=self.news1.UID())[0]

        self.request.form["metadata_fields"] = ["container_uid"]
        summary = getMultiAdapter((brain, self.request), ISerializeToJsonSummary)()

        self.assertEqual(summary.get("title"), "News 1")
        self.assertIn("title", summary)
