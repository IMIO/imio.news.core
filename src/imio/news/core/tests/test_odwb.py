# -*- coding: utf-8 -*-

from imio.news.core.rest.odwb_endpoint import OdwbEndpointGet
from imio.news.core.rest.odwb_endpoint import OdwbEntitiesEndpointGet
from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from imio.news.core.tests.utils import mock_odwb
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

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_get_news_to_send_to_odwb(self, m_post, m_reg):
        fake_response = MagicMock()
        fake_response.text = "KAMOULOX"
        m_post.return_value = fake_response
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
        # 1 (published) news is returned on self.portal
        self.assertEqual(endpoint.__datas_count__, 1)
        m_post.assert_called()
        called_url = m_post.call_args.args[0]
        self.assertIn("https://www.odwb.be/api/push/1.0", called_url)

        api.content.transition(event2, "publish")
        endpoint = OdwbEndpointGet(self.portal, self.request)
        endpoint.reply()
        # 2 (published) news are returned on self.portal
        self.assertEqual(endpoint.__datas_count__, 2)

        # test endpoint on news_folder
        endpoint = OdwbEndpointGet(self.news_folder, self.request)
        endpoint.reply()
        # 1 (published) news is returned on self.news_folder
        self.assertEqual(endpoint.__datas_count__, 1)

        # test endpoint on entity
        endpoint = OdwbEndpointGet(self.entity, self.request)
        endpoint.reply()
        # 1 (published) news is returned on self.entity
        self.assertEqual(endpoint.__datas_count__, 1)

    @patch("requests.post")
    def test_get_entities_to_send_to_odwb(self, m):
        api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="entity2",
            title="Entity 2",
        )
        # OdwbEntitiesEndpointGet.test_in_staging_or_local = True
        with mock_odwb():
            endpoint = OdwbEntitiesEndpointGet(self.portal, self.request)
            endpoint.reply()
            # 2 entities are returned on self.portal (entities are automaticly published)
            self.assertEqual(len(endpoint.__datas__), 2)

            api.content.transition(self.entity, "reject")
            endpoint = OdwbEntitiesEndpointGet(self.portal, self.request)
            endpoint.reply()
            self.assertEqual(len(endpoint.__datas__), 1)
