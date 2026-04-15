# -*- coding: utf-8 -*-

from imio.news.core.rest.odwb_endpoint import News
from imio.news.core.rest.odwb_endpoint import OdwbEndpointGet
from imio.news.core.rest.odwb_endpoint import OdwbEntitiesEndpointGet
from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from imio.news.core.tests.utils import make_named_image
from imio.news.core.tests.utils import mock_odwb
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedBlobImage
from unittest.mock import MagicMock
from unittest.mock import patch

import json
import os
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

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_reply_with_single_news_item_context(self, m_post, m_reg):
        fake_response = MagicMock()
        fake_response.text = "KAMOULOX"
        m_post.return_value = fake_response
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        api.content.transition(news_item, "publish")
        endpoint = OdwbEndpointGet(news_item, self.request)
        endpoint.reply()
        self.assertEqual(endpoint.__datas_count__, 1)

    def test_reply_returns_none_when_no_published_news(self):
        with mock_odwb():
            endpoint = OdwbEndpointGet(self.portal, self.request)
            result = endpoint.reply()
            self.assertIsNone(result)

    def test_remove_news_item(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        api.content.transition(news_item, "publish")
        with mock_odwb() as m:
            endpoint = OdwbEndpointGet(news_item, self.request)
            endpoint.remove()
            m.assert_called_once()
            called_url = m.call_args.args[0]
            self.assertIn("delete", called_url)
            self.assertIn("actualites-en-wallonie", called_url)
            payload = json.loads(m.call_args.args[1])
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["title"], "NewsItem")

    def test_remove_from_news_folder_context(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        api.content.transition(news_item, "publish")
        with mock_odwb() as m:
            endpoint = OdwbEndpointGet(self.news_folder, self.request)
            endpoint.remove()
            m.assert_called_once()
            payload = json.loads(m.call_args.args[1])
            self.assertEqual(len(payload), 1)

    def test_remove_from_entity_context(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        api.content.transition(news_item, "publish")
        with mock_odwb() as m:
            endpoint = OdwbEndpointGet(self.entity, self.request)
            endpoint.remove()
            m.assert_called_once()
            payload = json.loads(m.call_args.args[1])
            self.assertEqual(len(payload), 1)

    def test_remove_returns_none_when_no_news(self):
        with mock_odwb():
            endpoint = OdwbEndpointGet(self.portal, self.request)
            self.assertIsNone(endpoint.remove())

    def test_news_image_url_with_domains_env(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        news_item.image = NamedBlobImage(**make_named_image())
        with patch.dict(os.environ, {"DOMAINS": "test.example.com"}):
            news = News(news_item)
        self.assertTrue(news.image.startswith("https://test.example.com/"))
        self.assertIn("/@@images/image/preview", news.image)

    def test_news_image_url_without_domains_env(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        news_item.image = NamedBlobImage(**make_named_image())
        with patch.dict(os.environ, {"DOMAINS": ""}):
            news = News(news_item)
        portal = api.portal.get()
        self.assertTrue(news.image.startswith(portal.absolute_url()))
        self.assertIn("/@@images/image/preview", news.image)

    def test_news_svg_image_no_preview_scale(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        svg_data = b'<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        news_item.image = NamedBlobImage(
            data=svg_data, contentType="image/svg+xml", filename="image.svg"
        )
        news = News(news_item)
        self.assertTrue(news.image.endswith("/@@images/image"))
        self.assertNotIn("/preview", news.image)

    def test_news_no_image(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        news = News(news_item)
        self.assertIsNone(news.image)

    def test_log_odwb_response_accepts_status_ok(self):
        """ODWB returns {"status": "ok"}, not {"ok": true} — both must log at INFO."""
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        api.content.transition(news_item, "publish")
        with mock_odwb(ok_response='{"status": "ok"}'):
            with self.assertLogs("imio.news.core", level="INFO") as cm:
                endpoint = OdwbEndpointGet(news_item, self.request)
                endpoint.reply()
            # Must not log a WARNING — only INFO
            warnings = [
                line for line in cm.output if "WARNING" in line and "ODWB push" in line
            ]
            self.assertEqual(warnings, [])
            infos = [
                line for line in cm.output if "INFO" in line and "sent/updated" in line
            ]
            self.assertTrue(infos)

    def test_news_encoder_serializes_datetime_fields(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
            title="NewsItem",
        )
        news = News(news_item)
        data = json.loads(news.to_json())
        # DateTime fields must be serialized as ISO 8601 strings
        self.assertIsInstance(data["creation_datetime"], str)
        self.assertIsInstance(data["modification_datetime"], str)

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
