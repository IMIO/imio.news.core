# -*- coding: utf-8 -*-

from imio.news.core.rest.odwb_endpoint import OdwbEndpointGet
from imio.news.core.rest.odwb_endpoint import OdwbEntitiesEndpointGet
from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest.mock import MagicMock
from unittest.mock import patch

import requests
import unittest


class RestFunctionalTest(unittest.TestCase):
    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="entity",
            title="Entity",
        )
        self.news_folder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            id="news_folder",
            title="NewsFolder",
        )

    @patch("requests.post")
    def test_odwb_url_errors(self, mock_post):
        event = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="event",
            title="NewsItem",
        )
        # OdwbEndpointGet.test_in_staging_or_local = True
        mock_request = MagicMock()

        mock_post.side_effect = requests.exceptions.ConnectionError(
            "ODWB : Connection error occurred"
        )
        endpoint = OdwbEndpointGet(event, mock_request)
        response = endpoint.reply()
        self.assertEqual(response, "ODWB : Connection error occurred")
        mock_post.side_effect = requests.exceptions.Timeout("ODWB : Request timed out")
        endpoint = OdwbEndpointGet(event, mock_request)
        response = endpoint.reply()
        self.assertEqual(response, "ODWB : Request timed out")

        mock_post.side_effect = requests.exceptions.HTTPError(
            "ODWB : HTTP error occurred"
        )
        endpoint = OdwbEndpointGet(event, mock_request)
        response = endpoint.reply()
        self.assertEqual(response, "ODWB : HTTP error occurred")

        mock_post.side_effect = Exception("ODWB : Unexpected error occurred")
        endpoint = OdwbEndpointGet(event, mock_request)
        response = endpoint.reply()
        self.assertEqual(response, "ODWB : Unexpected error occurred")

    @patch("requests.post")
    def test_get_news_to_send_to_odwb(self, m):
        event = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="event",
            title="NewsItem",
        )
        event.exclude_from_nav = True

        entity2 = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="entity2",
            title="Entity 2",
        )
        news_folder2 = api.content.create(
            container=entity2,
            type="imio.news.NewsFolder",
            id="news_folder",
            title="NewsFolder 2",
        )

        event2 = api.content.create(
            container=news_folder2,
            type="imio.news.NewsItem",
            id="event",
            title="NewsItem 2",
        )

        api.content.transition(event, "publish")
        endpoint = OdwbEndpointGet(self.portal, self.request)
        endpoint.reply()
        # 1 (published) event is returned on self.portal
        self.assertEqual(len(endpoint.__datas__), 1)

        api.content.transition(event2, "publish")
        endpoint = OdwbEndpointGet(self.portal, self.request)
        endpoint.reply()
        # 2 (published) news are returned on self.portal
        self.assertEqual(len(endpoint.__datas__), 2)

        for data in endpoint.__datas__:
            if data.get("geolocation", None) is not None:
                self.assertEqual(data.get("geolocation"), {"lat": 4.5, "lon": 45})
            if data.get("latitude", None) is not None:
                self.assertEqual(data.get("latitude"), 4.5)
            if data.get("longitude", None) is not None:
                self.assertEqual(data.get("longitude"), 45)

        # test endpoint on news_folder
        endpoint = OdwbEndpointGet(self.news_folder, self.request)
        endpoint.reply()
        # 1 (published) event is returned on self.news_folder
        self.assertEqual(len(endpoint.__datas__), 1)

    @patch("requests.post")
    def test_get_entities_to_send_to_odwb(self, m):
        api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="entity2",
            title="Entity 2",
        )
        # OdwbEntitiesEndpointGet.test_in_staging_or_local = True
        endpoint = OdwbEntitiesEndpointGet(self.portal, self.request)
        endpoint.reply()
        # 2 entities are returned on self.portal (entities are automaticly published)
        self.assertEqual(len(endpoint.__datas__), 2)

        api.content.transition(self.entity, "reject")
        endpoint = OdwbEntitiesEndpointGet(self.portal, self.request)
        endpoint.reply()
        self.assertEqual(len(endpoint.__datas__), 1)
