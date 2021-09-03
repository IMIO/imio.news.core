# -*- coding: utf-8 -*-

from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestVocabularies(unittest.TestCase):

    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_news_categories(self):
        factory = getUtility(IVocabularyFactory, "imio.news.vocabulary.NewsCategories")
        vocabulary = factory()
        self.assertEqual(len(vocabulary), 4)

    def test_news_categories_topics_basic(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
            local_categories="",
        )
        newsfolder = api.content.create(
            container=entity,
            type="imio.news.NewsFolder",
            title="News folder",
        )

        news_item = api.content.create(
            container=newsfolder, type="imio.news.NewsItem", title="title"
        )
        factory = getUtility(
            IVocabularyFactory,
            "imio.news.vocabulary.NewsCategoriesAndTopicsVocabulary",
        )
        vocabulary = factory(news_item)
        self.assertEqual(len(vocabulary), 21) #must be updated if add new vocabulary

    def test_news_categories_topics_local_cat(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
            local_categories="Foo\r\nbaz\r\nbar",
        )
        newsfolder = api.content.create(
            container=entity,
            type="imio.news.NewsFolder",
            title="News folder",
        )

        news_item = api.content.create(
            container=newsfolder, type="imio.news.NewsItem", title="title"
        )

        factory = getUtility(
            IVocabularyFactory,
            "imio.news.vocabulary.NewsCategoriesAndTopicsVocabulary",
        )
        vocabulary = factory(news_item)
        self.assertEqual(len(vocabulary), 24) #must be updated if add new vocabulary
