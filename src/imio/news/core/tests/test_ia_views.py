# -*- coding: utf-8 -*-

from imio.news.core.ia.browser.views import ProcessCategorizeContentView
from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest.mock import patch

import json
import unittest


class TestProcessCategorizeContentView(unittest.TestCase):
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

    def _make_view(self, context=None):
        return ProcessCategorizeContentView(context or self.news_folder, self.request)

    def _set_body(self, title="", richtext=""):
        self.request["BODY"] = json.dumps(
            {
                "formdata": {
                    "form-widgets-IIASmartTitle-title": title,
                    "form-widgets-IRichTextBehavior-text": richtext,
                }
            }
        )

    # --- _get_all_text ---

    def test_get_all_text_combines_title_and_richtext(self):
        self._set_body(title="My Title", richtext="Some content")
        self.assertEqual(self._make_view()._get_all_text(), "My Title Some content")

    def test_get_all_text_title_only(self):
        self._set_body(title="My Title")
        self.assertEqual(self._make_view()._get_all_text(), "My Title")

    def test_get_all_text_empty_fields_returns_empty_string(self):
        self._set_body()
        self.assertEqual(self._make_view()._get_all_text(), "")

    # --- _process_category ---

    def test_process_category_uses_correct_vocabulary(self):
        view = self._make_view()
        with patch.object(view, "_get_structured_data_from_vocabulary") as mock_voc:
            mock_voc.return_value = []
            with patch.object(view, "_ask_categorization_to_ia", return_value={}):
                view._process_category("text", {})
            mock_voc.assert_called_once_with("imio.news.vocabulary.NewsCategories")

    def test_process_category_returns_list_from_ia_result(self):
        view = self._make_view()
        with patch.object(
            view, "_get_structured_data_from_vocabulary", return_value=[]
        ):
            with patch.object(
                view,
                "_ask_categorization_to_ia",
                return_value={"result": [{"title": "Politique", "token": "politics"}]},
            ):
                result = view._process_category("text", {})
        self.assertEqual(result, [{"title": "Politique", "token": "politics"}])

    def test_process_category_returns_none_when_no_ia_data(self):
        view = self._make_view()
        with patch.object(
            view, "_get_structured_data_from_vocabulary", return_value=[]
        ):
            with patch.object(view, "_ask_categorization_to_ia", return_value={}):
                result = view._process_category("text", {})
        self.assertIsNone(result)

    # --- _process_local_category ---

    def test_process_local_category_passes_context_to_vocabulary(self):
        view = self._make_view()
        with patch.object(view, "_get_structured_data_from_vocabulary") as mock_voc:
            mock_voc.return_value = []
            with patch.object(view, "_ask_categorization_to_ia", return_value={}):
                view._process_local_category("text", {})
            mock_voc.assert_called_once_with(
                "imio.news.vocabulary.NewsLocalCategories", self.news_folder
            )

    def test_process_local_category_returns_list_from_ia_result(self):
        view = self._make_view()
        with patch.object(
            view, "_get_structured_data_from_vocabulary", return_value=[]
        ):
            with patch.object(
                view,
                "_ask_categorization_to_ia",
                return_value={"result": [{"title": "Local", "token": "local-cat"}]},
            ):
                result = view._process_local_category("text", {})
        self.assertEqual(result, [{"title": "Local", "token": "local-cat"}])

    def test_process_local_category_returns_none_when_no_ia_data(self):
        view = self._make_view()
        with patch.object(
            view, "_get_structured_data_from_vocabulary", return_value=[]
        ):
            with patch.object(view, "_ask_categorization_to_ia", return_value={}):
                result = view._process_local_category("text", {})
        self.assertIsNone(result)

    # --- _process_specific ---

    def test_process_specific_populates_both_result_fields(self):
        view = self._make_view()
        category = [{"title": "Politique", "token": "politics"}]
        local_category = [{"title": "Local", "token": "local"}]
        with patch.object(view, "_process_category", return_value=category):
            with patch.object(
                view, "_process_local_category", return_value=local_category
            ):
                results = view._process_specific("text", {})
        self.assertEqual(results["form-widgets-category"], category)
        self.assertEqual(results["form-widgets-local_category"], local_category)

    def test_process_specific_omits_none_results(self):
        view = self._make_view()
        with patch.object(view, "_process_category", return_value=None):
            with patch.object(view, "_process_local_category", return_value=None):
                results = view._process_specific("text", {})
        self.assertNotIn("form-widgets-category", results)
        self.assertNotIn("form-widgets-local_category", results)

    def test_process_specific_only_category_populated(self):
        view = self._make_view()
        category = [{"title": "Culture", "token": "culture"}]
        with patch.object(view, "_process_category", return_value=category):
            with patch.object(view, "_process_local_category", return_value=None):
                results = view._process_specific("text", {})
        self.assertIn("form-widgets-category", results)
        self.assertNotIn("form-widgets-local_category", results)

    def test_process_specific_only_local_category_populated(self):
        view = self._make_view()
        local_category = [{"title": "Local", "token": "local"}]
        with patch.object(view, "_process_category", return_value=None):
            with patch.object(
                view, "_process_local_category", return_value=local_category
            ):
                results = view._process_specific("text", {})
        self.assertNotIn("form-widgets-category", results)
        self.assertIn("form-widgets-local_category", results)
