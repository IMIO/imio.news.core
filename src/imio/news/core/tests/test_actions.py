# -*- coding: utf-8 -*-

from imio.news.core.interfaces import IImioNewsCoreLayer
from imio.news.core.testing import IMIO_NEWS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import setRoles
from plone.testing.zope import Browser
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

import transaction
import unittest


class TestCropping(unittest.TestCase):
    layer = IMIO_NEWS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests"""
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        self.portal_url = api.portal.get().absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
        )
        self.news_folder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            title="Folder",
        )
        self.news = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="News",
        )

        self.browser = Browser(self.layer["app"])
        self.browser.handleErrors = False
        self.browser.addHeader(
            "Authorization",
            "Basic %s:%s" % (TEST_USER_NAME, TEST_USER_PASSWORD),
        )

    def test_cannot_delete_non_empty_news_folder(self):
        transaction.commit()
        self.browser.open(self.news_folder.absolute_url() + "/@@delete_confirmation")
        self.assertEqual(self.browser.url, self.news_folder.absolute_url())
        self.assertIn("can't be removed", self.browser.contents)
        self.assertIn("folder", self.entity.objectIds())

    def test_can_delete_empty_news_folder(self):
        api.content.delete(self.news)
        transaction.commit()
        self.browser.open(self.news_folder.absolute_url() + "/@@delete_confirmation")
        self.assertIn("Delete", self.browser.contents)

        # Click Delete button
        self.browser.getControl(name="form.buttons.Delete").click()
        self.assertNotIn("folder", self.portal.objectIds())
        self.assertEqual(self.browser.url, self.entity.absolute_url())

    def test_can_delete_news(self):
        transaction.commit()
        self.browser.open(self.news.absolute_url() + "/@@delete_confirmation")
        self.assertIn("Delete", self.browser.contents)
        self.browser.getControl(name="form.buttons.Delete").click()
        self.assertNotIn("news", self.news_folder.objectIds())
        self.assertEqual(self.browser.url, self.news_folder.absolute_url())

    # action “trash” in folder_contents
    def test_trash_cannot_delete_non_empty_news_folder(self):
        request = TestRequest()
        alsoProvides(request, IImioNewsCoreLayer)
        view = getMultiAdapter((self.entity, request), name="fc-delete")
        view.errors = []
        view.action(self.news_folder)
        self.assertIn("folder", self.entity.objectIds())

    # action “trash” in folder_contents
    def test_trash_can_delete_empty_news_folder(self):
        api.content.delete(self.news)
        request = TestRequest()
        alsoProvides(request, IImioNewsCoreLayer)
        view = getMultiAdapter((self.entity, request), name="fc-delete")
        view.action(self.news_folder)
        self.assertNotIn("folder", self.entity.objectIds())
