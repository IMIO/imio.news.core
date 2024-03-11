# -*- coding: utf-8 -*-

from imio.news.core.testing import IMIO_NEWS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser

import json
import transaction
import unittest


class TestBringNews(unittest.TestCase):
    layer = IMIO_NEWS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
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
        self.news_folder1b = api.content.create(
            container=self.entity1,
            type="imio.news.NewsFolder",
            id="news_folder1b",
            title="news folder 1b",
        )
        self.news1 = api.content.create(
            container=self.news_folder1,
            type="imio.news.NewsItem",
            id="news1",
            title="News 1",
        )

        self.entity2 = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="entity2",
            title="Entity 2",
        )
        self.news_folder2 = api.content.create(
            container=self.entity2,
            type="imio.news.NewsFolder",
            id="news_folder2",
            title="News folder 2",
        )
        self.news2 = api.content.create(
            container=self.news_folder2,
            type="imio.news.NewsItem",
            id="news2",
            title="News 2",
        )

    def test_brings_news_into_news_folders(self):
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
        browser.open(
            f"{self.news2.absolute_url()}/@@bring_news_into_news_folders_form/@@getVocabulary?name=imio.news.vocabulary.UserNewsFolders&field=news_folders"
        )
        content = browser.contents
        results = json.loads(content).get("results")
        available_news_folders_uids = [r.get("id") for r in results]
        self.assertNotIn(self.news2.selected_news_folders, available_news_folders_uids)

        # to be continued...
