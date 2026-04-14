# -*- coding: utf-8 -*-

from imio.news.core.ia.browser.categorization_button_add import IACategorizeAddForm
from imio.news.core.ia.browser.categorization_button_add import IACategorizeAddView
from imio.news.core.ia.browser.categorization_button_edit import IACategorizeEditForm
from imio.news.core.ia.browser.categorization_button_edit import PageEditView
from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from imio.smartweb.common.ia.browser.categorization_button_add import (
    IACategorizeAddForm as BaseIACategorizeAddForm,
)
from imio.smartweb.common.ia.browser.categorization_button_edit import (
    IACategorizeEditForm as BaseIACategorizeEditForm,
)
from plone.dexterity.browser.add import DefaultAddView
from unittest.mock import patch

import unittest


class TestIACategorizeAddForm(unittest.TestCase):
    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def test_inherits_from_base_add_form(self):
        self.assertTrue(issubclass(IACategorizeAddForm, BaseIACategorizeAddForm))

    def test_update_delegates_to_super(self):
        with patch.object(BaseIACategorizeAddForm, "update") as mock_update:
            form = IACategorizeAddForm.__new__(IACategorizeAddForm)
            IACategorizeAddForm.update(form)
            mock_update.assert_called_once_with()


class TestIACategorizeAddView(unittest.TestCase):
    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def test_inherits_from_default_add_view(self):
        self.assertTrue(issubclass(IACategorizeAddView, DefaultAddView))

    def test_form_attribute_is_news_add_form(self):
        self.assertIs(IACategorizeAddView.form, IACategorizeAddForm)


class TestIACategorizeEditForm(unittest.TestCase):
    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def test_inherits_from_base_edit_form(self):
        self.assertTrue(issubclass(IACategorizeEditForm, BaseIACategorizeEditForm))

    def test_update_delegates_to_super(self):
        with patch.object(BaseIACategorizeEditForm, "update") as mock_update:
            form = IACategorizeEditForm.__new__(IACategorizeEditForm)
            IACategorizeEditForm.update(form)
            mock_update.assert_called_once_with()


class TestPageEditView(unittest.TestCase):
    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def test_page_edit_view_is_defined(self):
        self.assertIsNotNone(PageEditView)

    def test_page_edit_view_wraps_edit_form(self):
        # layout.wrap_form stores the wrapped form class on the view
        self.assertIs(PageEditView.form, IACategorizeEditForm)
