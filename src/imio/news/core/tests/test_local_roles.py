# -*- coding: utf-8 -*-

from imio.news.core.testing import IMIO_NEWS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser

import transaction
import unittest


class TestLocalRoles(unittest.TestCase):

    layer = IMIO_NEWS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
        )
        self.newsfolder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            title="NewsFolder",
        )
        self.folder = api.content.create(
            container=self.newsfolder,
            type="imio.news.Folder",
            title="Folder",
        )
        self.newsitem = api.content.create(
            container=self.folder,
            type="imio.news.NewsItem",
            title="NewsItem",
        )

    def test_local_manager_in_sharing(self):
        transaction.commit()
        browser = Browser(self.layer["app"])
        browser.addHeader(
            "Authorization",
            "Basic %s:%s"
            % (
                TEST_USER_NAME,
                TEST_USER_PASSWORD,
            ),
        )
        browser.open("{}/@@sharing".format(self.entity.absolute_url()))
        content = browser.contents
        self.assertIn("Can manage locally", content)

        browser.open("{}/@@sharing".format(self.newsfolder.absolute_url()))
        content = browser.contents
        self.assertNotIn("Can manage locally", content)

        browser.open("{}/@@sharing".format(self.folder.absolute_url()))
        content = browser.contents
        self.assertNotIn("Can manage locally", content)

        browser.open("{}/@@sharing".format(self.newsitem.absolute_url()))
        content = browser.contents
        self.assertNotIn("Can manage locally", content)
