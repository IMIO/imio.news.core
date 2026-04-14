# -*- coding: utf-8 -*-

from imio.news.core.converters import i18n_message_converter
from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from plone.restapi.interfaces import IJsonCompatible
from unittest.mock import patch
from zope.i18nmessageid.message import Message

import unittest


class ConvertersTest(unittest.TestCase):
    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.request = self.layer["request"]
        # snapshot form keys added by this test so tearDown can remove them
        self._added_form_keys = []

    def tearDown(self):
        for key in self._added_form_keys:
            self.request.form.pop(key, None)

    def _set_form(self, **kwargs):
        for key, value in kwargs.items():
            self.request.form[key] = value
            self._added_form_keys.append(key)

    # --- adapter registration ---

    def test_adapter_is_registered(self):
        """IJsonCompatible adapter for Message is wired up in overrides.zcml."""
        result = IJsonCompatible(Message("sometext"))
        self.assertIsInstance(result, str)

    # --- return type ---

    def test_converter_returns_string(self):
        result = i18n_message_converter(Message("sometext"))
        self.assertIsInstance(result, str)

    # --- language selection ---

    def test_default_language_is_french(self):
        """No translated_in_* key in request form → target language is fr."""
        with patch("imio.news.core.converters.translate") as mock_translate:
            mock_translate.return_value = "traduit"
            i18n_message_converter(Message("sometext"))
            self.assertEqual(mock_translate.call_args.kwargs["target_language"], "fr")

    def test_language_from_single_translated_in_key(self):
        """translated_in_nl in form → target language is nl."""
        self._set_form(translated_in_nl="1")
        with patch("imio.news.core.converters.translate") as mock_translate:
            mock_translate.return_value = "vertaald"
            i18n_message_converter(Message("sometext"))
            self.assertEqual(mock_translate.call_args.kwargs["target_language"], "nl")

    def test_multiple_translated_in_keys_fall_back_to_french(self):
        """Multiple translated_in_* keys are ambiguous → falls back to fr."""
        self._set_form(translated_in_nl="1", translated_in_de="1")
        with patch("imio.news.core.converters.translate") as mock_translate:
            mock_translate.return_value = "traduit"
            i18n_message_converter(Message("sometext"))
            self.assertEqual(mock_translate.call_args.kwargs["target_language"], "fr")
