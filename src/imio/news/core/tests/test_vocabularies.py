# -*- coding: utf-8 -*-

from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestVocabularies(unittest.TestCase):

    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    def test_news_categories(self):
        factory = getUtility(
            IVocabularyFactory, "imio.news.vocabulary.NewsCategories"
        )
        vocabulary = factory()
        self.assertEqual(len(vocabulary), 4)
