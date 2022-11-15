# -*- coding: utf-8 -*-

from imio.news.core.interfaces import IImioNewsCoreLayer
from imio.news.core.testing import IMIO_NEWS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.interfaces import ISerializeToJsonSummary
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

import transaction
import unittest


class TestMultilingual(unittest.TestCase):

    layer = IMIO_NEWS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests"""
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
        )
        self.news_folder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            title="News folder",
        )

    def test_create_multilingual_news_item(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="Ma news que je vais tester en plusieurs langues",
        )
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertFalse(indexes.get("translated_in_nl"))
        self.assertFalse(indexes.get("translated_in_de"))
        self.assertFalse(indexes.get("translated_in_en"))

        news_item.title_en = "My news item that I will test in several languages"
        news_item.reindexObject()
        transaction.commit()
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertFalse(indexes.get("translated_in_nl"))
        self.assertFalse(indexes.get("translated_in_de"))
        self.assertTrue(indexes.get("translated_in_en"))

        news_item.title_nl = "Mijn nieuws die ik in verschillende talen zal testen"
        news_item.title_de = "Mein nieuws, den ich in mehreren Sprachen testen werde"
        news_item.reindexObject()
        transaction.commit()
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertTrue(indexes.get("translated_in_nl"))
        self.assertTrue(indexes.get("translated_in_de"))
        self.assertTrue(indexes.get("translated_in_en"))

        news_item.title_en = None
        news_item.reindexObject()
        transaction.commit()
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertFalse(indexes.get("translated_in_en"))

    def test_multilingual_searchabletext_news_item(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="Ma news que je vais tester en plusieurs langues",
        )
        news_item.title_en = "My news item that I will test in several languages"
        news_item.title_nl = "Mijn nieuws die ik in verschillende talen zal testen"
        news_item.title_de = "Mein nieuws, den ich in mehreren Sprachen testen werde"
        news_item.text = RichTextValue("<p>Mon texte</p>", "text/html", "text/html")
        news_item.text_en = RichTextValue("<p>My newstext</p>", "text/html", "text/html")
        news_item.text_nl = RichTextValue("<p>Mijn nieuwstekst</p>", "text/html", "text/html")
        news_item.text_de = RichTextValue("<p>Meine nieuwstext</p>", "text/html", "text/html")
        news_item.reindexObject()
        transaction.commit()
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertIn("several", indexes.get("SearchableText"))
        self.assertIn("verschillende", indexes.get("SearchableText"))
        self.assertIn("mehreren", indexes.get("SearchableText"))
        self.assertIn("texte", indexes.get("SearchableText"))
        self.assertIn("newstext", indexes.get("SearchableText"))
        self.assertIn("nieuwstekst", indexes.get("SearchableText"))
        self.assertIn("nieuwstext", indexes.get("SearchableText"))
        metadatas = catalog.getMetadataForRID(brain.getRID())
        self.assertEqual(news_item.title, metadatas.get("title_fr"))
        self.assertEqual(news_item.title_nl, metadatas.get("title_nl"))
        self.assertEqual(news_item.title_de, metadatas.get("title_de"))
        self.assertEqual(news_item.title_en, metadatas.get("title_en"))

        news_item.title_en = None
        news_item.reindexObject()
        transaction.commit()
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertNotIn("several", indexes.get("SearchableText"))

    def test_news_item_serializer(self):
        alsoProvides(self.request, IImioNewsCoreLayer)
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="Ma news",
        )
        news_item.title_en = "My news item"
        news_item.title_nl = "Mijn nieuws"
        news_item.description = "Ma **description**"
        news_item.description_en = "My **description**"
        news_item.description_nl = "Mijn **beschrijving**"
        news_item.text = RichTextValue("<p>Mon texte</p>", "text/html", "text/html")
        news_item.text_en = RichTextValue("<p>My text</p>", "text/html", "text/html")
        news_item.text_nl = RichTextValue("<p>Mijn tekst</p>", "text/html", "text/html")

        serializer = getMultiAdapter((news_item, self.request), ISerializeToJson)
        json = serializer()
        self.assertEqual(json["title"], "Ma news")
        self.assertEqual(json["description"], "Ma **description**")
        self.assertEqual(json["title_fr"], "Ma news")
        self.assertEqual(json["description_fr"], "Ma **description**")

        catalog = api.portal.get_tool("portal_catalog")
        brain = catalog(UID=news_item.UID())[0]
        serializer = getMultiAdapter((brain, self.request), ISerializeToJsonSummary)
        json_summary = serializer()
        self.assertEqual(json_summary["title"], "Ma news")
        self.assertEqual(json_summary["description"], "Ma description")

        self.request.form["translated_in_nl"] = True
        serializer = getMultiAdapter((news_item, self.request), ISerializeToJson)
        json = serializer()
        self.assertEqual(json["title"], "Mijn nieuws")
        self.assertEqual(json["description"], "Mijn **beschrijving**")
        self.assertEqual(json["text"]["data"], "<p>Mijn tekst</p>")
        self.assertEqual(json["title_fr"], "Ma news")
        self.assertEqual(json["description_fr"], "Ma **description**")
        self.assertEqual(json["text_fr"]["data"], "<p>Mon texte</p>")

        brain = catalog(UID=news_item.UID())[0]
        serializer = getMultiAdapter((brain, self.request), ISerializeToJsonSummary)
        json_summary = serializer()
        self.assertEqual(json_summary["title"], "Mijn nieuws")
        self.assertEqual(json_summary["description"], "Mijn beschrijving")
