# -*- coding: utf-8 -*-

from imio.news.core.contents import INewsItem
from imio.news.core.testing import IMIO_NEWS_CORE_FUNCTIONAL_TESTING
from imio.news.core.tests.utils import get_leadimage_filename
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from plone.namedfile.file import NamedBlobFile
from zope.component import createObject
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class ContactFunctionalTest(unittest.TestCase):

    layer = IMIO_NEWS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests"""
        self.authorized_types_in_newsitem = ["File", "Image"]

        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
        )
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
        )
        self.newsfolder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            title="News folder",
        )

    def test_ct_newsitem_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsItem")
        schema = fti.lookupSchema()
        self.assertEqual(INewsItem, schema)

    def test_ct_newsitem_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsItem")
        self.assertTrue(fti)

    def test_ct_newsitem_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsItem")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            INewsItem.providedBy(obj),
            u"INewsItem not provided by {0}!".format(
                obj,
            ),
        )

    def test_news_local_category(self):
        news = api.content.create(
            container=self.newsfolder,
            type="imio.news.NewsItem",
            id="my-news",
        )
        factory = getUtility(
            IVocabularyFactory, "imio.news.vocabulary.NewsLocalCategories"
        )
        vocabulary = factory(news)
        self.assertEqual(len(vocabulary), 0)

        self.entity.local_categories = "First\nSecond\nThird"
        vocabulary = factory(news)
        self.assertEqual(len(vocabulary), 3)

    def test_view(self):
        newsitem = api.content.create(
            container=self.newsfolder,
            type="imio.news.NewsItem",
            title="My news item",
        )
        view = queryMultiAdapter((newsitem, self.request), name="view")
        self.assertIn("My news item", view())

    def test_embed_video(self):
        newsitem = api.content.create(
            container=self.newsfolder,
            type="imio.news.NewsItem",
            title="My news item",
        )
        newsitem.video_url = "https://www.youtube.com/watch?v=_dOAthafoGQ"
        view = queryMultiAdapter((newsitem, self.request), name="view")
        embedded_video = view.get_embed_video()
        self.assertIn("iframe", embedded_video)
        self.assertIn(
            "https://www.youtube.com/embed/_dOAthafoGQ?feature=oembed", embedded_video
        )

    def test_has_leadimage(self):
        newsitem = api.content.create(
            container=self.newsfolder,
            type="imio.news.NewsItem",
            title="My news item",
        )
        view = queryMultiAdapter((newsitem, self.request), name="view")
        self.assertEqual(view.has_leadimage(), False)
        newsitem.image = NamedBlobFile(
            "ploneLeadImage", filename=get_leadimage_filename()
        )
        self.assertEqual(view.has_leadimage(), True)
