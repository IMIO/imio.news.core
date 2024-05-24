# -*- coding: utf-8 -*-

from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


def search_all_from_vocabulary(vocabulary, context, catalog):
    factory = getUtility(
        IVocabularyFactory,
        vocabulary,
    )
    output = {}
    vocabulary = factory(context)
    for v in vocabulary.by_value:
        result = catalog.searchResults(**{"category_and_topics": v})
        if len(result) == 0:
            continue
        output[v] = [r.getObject().id for r in result]
    return output


class TestIndexes(unittest.TestCase):
    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.portal_catalog = api.portal.get_tool("portal_catalog")

        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="imio.news.Entity",
            local_categories=[
                {"fr": "Foo", "nl": "", "de": "", "en": ""},
                {"fr": "baz", "nl": "", "de": "", "en": ""},
                {"fr": "bar", "nl": "", "de": "", "en": ""},
                {"fr": "Local category", "nl": "", "de": "", "en": ""},
            ],
        )
        self.news_folder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            id="imio.news.NewsFolder",
        )

    def test_category_and_topics_index(self):
        api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="imio.news.NewsItem",
        )
        search_result = search_all_from_vocabulary(
            "imio.news.vocabulary.NewsCategoriesAndTopicsVocabulary",
            self.news_folder,
            self.portal_catalog,
        )

        self.assertEqual(len(search_result), 0)

        # With categories and topics
        api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="id_news",
            category="works",
            local_category="Foo",
            topics=["culture", "health"],
        )

        api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="id_news2",
            category="presse",
            local_category="baz",
            topics=["tourism", "health"],
        )

        search_result = search_all_from_vocabulary(
            "imio.news.vocabulary.NewsCategoriesAndTopicsVocabulary",
            self.news_folder,
            self.portal_catalog,
        )

        # check if right number of result
        self.assertEqual(len(search_result), 7)

        # check for good result number
        self.assertEqual(len(search_result["Foo"]), 1)
        self.assertEqual(len(search_result["baz"]), 1)
        self.assertEqual(len(search_result["culture"]), 1)
        self.assertEqual(len(search_result["health"]), 2)
        self.assertEqual(len(search_result["tourism"]), 1)

        # check for good return object
        self.assertEqual(search_result["Foo"], ["id_news"])
        self.assertEqual(search_result["baz"], ["id_news2"])
        self.assertEqual(search_result["culture"], ["id_news"])
        self.assertEqual(sorted(search_result["health"]), ["id_news", "id_news2"])
        self.assertEqual(search_result["tourism"], ["id_news2"])

    def test_category_title_index(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="Title",
        )
        news_item.category = "works"
        news_item.reindexObject()
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("category_title"), "Travaux")
        metadatas = catalog.getMetadataForRID(brain.getRID())
        self.assertEqual(metadatas.get("category_title"), "Travaux")
        self.assertEqual(metadatas.get("category_title_nl"), "Werken")
        self.assertEqual(metadatas.get("category_title_de"), "Arbeiten")
        self.assertEqual(metadatas.get("category_title_en"), "Works")
        news_item.local_category = "Local category"
        news_item.reindexObject()
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("category_title"), "Travaux")

    def test_selected_news_folders_index(self):
        news_item1 = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="NewsItem1",
        )
        news_folder2 = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            title="NewsFolder2",
        )
        news_item2 = api.content.create(
            container=news_folder2,
            type="imio.news.NewsItem",
            title="NewsItem2",
        )
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item1.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("container_uid"), self.news_folder.UID())

        # On va requêter sur self.news_folder et trouver les 2 événements car news_item2 vient de s'ajouter dedans aussi.
        news_item2.selected_news_folders = [self.news_folder.UID()]
        news_item2.reindexObject()
        brains = api.content.find(selected_news_folders=self.news_folder.UID())
        lst = [brain.UID for brain in brains]
        self.assertEqual(lst, [news_item1.UID(), news_item2.UID()])

        # On va requêter sur news_folder2 et trouver uniquement news_item2 car news_item2 est dans les 2 news folders mais news_item1 n'est que dans self.news_folder
        news_item2.selected_news_folders = [news_folder2.UID(), self.news_folder.UID()]
        news_item2.reindexObject()
        brains = api.content.find(selected_news_folders=news_folder2.UID())
        lst = [brain.UID for brain in brains]
        self.assertEqual(lst, [news_item2.UID()])

        # Via une recherche catalog sur les news_folder, on va trouver les 2 événements
        brains = api.content.find(
            selected_news_folders=[news_folder2.UID(), self.news_folder.UID()]
        )
        lst = [brain.UID for brain in brains]
        self.assertEqual(lst, [news_item1.UID(), news_item2.UID()])

        # On va requêter sur les 2 news folders et trouver les 2 événements car 1 dans chaque
        news_item2.selected_news_folders = [news_folder2.UID()]
        news_item2.reindexObject()
        brains = api.content.find(
            selected_news_folders=[news_folder2.UID(), self.news_folder.UID()]
        )
        lst = [brain.UID for brain in brains]
        self.assertEqual(lst, [news_item1.UID(), news_item2.UID()])

        api.content.move(news_item1, news_folder2)
        brain = api.content.find(UID=news_item1.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("container_uid"), news_folder2.UID())

    def test_searchable_text_index(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="Title",
        )
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("SearchableText"), ["title"])

        news_item.description = "Description"
        news_item.topics = ["agriculture"]
        news_item.category = "job_offer"
        news_item.text = RichTextValue("<p>Text</p>", "text/html", "text/html")
        news_item.reindexObject()

        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            indexes.get("SearchableText"),
            [
                "title",
                "description",
                "text",
                "agriculture",
                "emploi",
            ],
        )

        news_item.title_nl = "Titel"
        news_item.description_nl = "Descriptie"
        news_item.text_nl = RichTextValue("<p>Tekst</p>", "text/html", "text/html")
        news_item.reindexObject()

        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            indexes.get("SearchableText_nl"),
            [
                "titel",
                "descriptie",
                "tekst",
                "landbouw",
                "vacature",
            ],
        )
