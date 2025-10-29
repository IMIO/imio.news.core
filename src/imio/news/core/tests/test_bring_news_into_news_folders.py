# -*- coding: utf-8 -*-

from imio.news.core.interfaces import IImioNewsCoreLayer
from imio.news.core.testing import IMIO_NEWS_CORE_FUNCTIONAL_TESTING
from imio.news.core.viewlets.news import (
    user_is_contributor_in_entity_which_authorize_to_bring_news,
)
from plone import api
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.interface import alsoProvides

import mock
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

    def _fake_vocab(self, *values_and_titles):
        class _Term:
            def __init__(self, value, title):
                self.value = value
                self.title = title

        return [_Term(v, t) for v, t in values_and_titles]

    def test_view_is_registered_and_traversable(self):
        alsoProvides(self.request, IImioNewsCoreLayer)
        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")
        self.assertIsNotNone(view)
        self.assertTrue(hasattr(view, "schema"))
        self.assertTrue(hasattr(view, "update"))
        self.assertEqual(view.label, "Add/Remove news folder(s)")

    @mock.patch("imio.smartweb.common.utils.get_vocabulary")
    def test_update_widgets_prefills_selected_news_folders(self, mock_get_vocab):
        uid1 = api.content.get_uuid(self.news_folder1b)
        uid2 = api.content.get_uuid(self.news_folder2)

        # Fake vocabulary to return both folders
        mock_get_vocab.return_value = self._fake_vocab(
            (uid1, self.news_folder1b.Title()),
            (uid2, self.news_folder2.Title()),
        )

        self.news1.selected_news_folders = [uid1, uid2]

        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")
        view.update()
        self.assertIn("news_folders", view.widgets)
        self.assertEqual(view.widgets["news_folders"].value, f"{uid1};{uid2}")

    @mock.patch("imio.smartweb.common.utils.get_vocabulary")
    def test_submit_adds_missing_news_folders(self, mock_get_vocab):
        alsoProvides(self.request, IImioNewsCoreLayer)
        self.request["REQUEST_METHOD"] = "POST"

        uid1 = api.content.get_uuid(self.news_folder1b)
        uid2 = api.content.get_uuid(self.news_folder2)

        mock_get_vocab.return_value = self._fake_vocab(
            (uid1, self.news_folder1b.Title()),
            (uid2, self.news_folder2.Title()),
        )

        self.news1.selected_news_folders = [uid1]

        # Simulate submitting both uids -> should add uid2
        self.request.form["form.widgets.news_folders"] = f"{uid1};{uid2}"
        self.request.form["form.buttons.submit"] = "Submit"

        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")

        # Patch reindex and redirect to observe side effects
        with mock.patch.object(
            self.news1, "reindexObject"
        ) as reindex_mock, mock.patch.object(
            self.request.response, "redirect"
        ) as redirect_mock:
            view.update()  # z3c.form processes the submit here

            self.assertIn(uid1, self.news1.selected_news_folders)
            self.assertIn(uid2, self.news1.selected_news_folders)
            reindex_mock.assert_called_once()
        self.assertIn("added", str(view.status).lower())

    @mock.patch("imio.smartweb.common.utils.get_vocabulary")
    def test_submit_removes_unchecked_news_folders(self, mock_get_vocab):
        alsoProvides(self.request, IImioNewsCoreLayer)
        self.request["REQUEST_METHOD"] = "POST"

        uid1 = api.content.get_uuid(self.news_folder1b)
        uid2 = api.content.get_uuid(self.news_folder2)

        mock_get_vocab.return_value = self._fake_vocab(
            (uid1, self.news_folder1b.Title()),
            (uid2, self.news_folder2.Title()),
        )

        # Etat initial: deux dossiers sélectionnés
        self.news1.selected_news_folders = [uid1, uid2]

        # Envoi du formulaire avec SEULEMENT uid1 -> doit retirer uid2
        self.request.form["form.widgets.news_folders"] = uid1
        self.request.form["form.buttons.submit"] = "Submit"

        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")

        with mock.patch.object(
            self.news1, "reindexObject"
        ) as reindex_mock, mock.patch.object(
            self.request.response, "redirect"
        ) as redirect_mock:
            view.update()  # déclenche handle_submit

            self.assertIn(uid1, self.news1.selected_news_folders)
            self.assertNotIn(uid2, self.news1.selected_news_folders)
            reindex_mock.assert_called_once()
        self.assertIn("removed", str(view.status).lower())

    def test_cancel_button_redirects_without_changes(self):
        alsoProvides(self.request, IImioNewsCoreLayer)

        # Simule un POST + clic sur le bouton Cancel
        self.request["REQUEST_METHOD"] = "POST"
        self.request.form["form.buttons.cancel"] = "Cancel"

        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")

        with mock.patch.object(
            self.request.response, "redirect"
        ) as redirect_mock, mock.patch.object(
            self.news1, "reindexObject"
        ) as reindex_mock:
            view.update()
            reindex_mock.assert_not_called()

    @mock.patch("imio.smartweb.common.utils.get_vocabulary")
    def test_user_permission(self, mock_get_vocab):
        alsoProvides(self.request, IImioNewsCoreLayer)
        self.entity1.authorize_to_bring_news_anywhere = True
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")
        self.assertIsNone(view.update())
        self.assertNotIn("You don't have rights to access this page.", view.render())

        setRoles(self.portal, TEST_USER_ID, ["Site Administrator"])
        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")
        self.assertIsNone(view.update())
        self.assertNotIn("You don't have rights to access this page.", view.render())

        setRoles(self.portal, TEST_USER_ID, ["Editor"])
        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")
        self.assertIsNone(view.update())
        self.assertNotIn("You don't have rights to access this page.", view.render())

        setRoles(self.portal, TEST_USER_ID, ["Owner"])
        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")
        self.assertFalse(view.update())
        self.assertIn("You don't have rights to access this page.", view.render())

        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        view = self.news1.restrictedTraverse("@@bring_news_into_news_folders_form")
        self.assertFalse(view.update())
        self.assertIn("You don't have rights to access this page.", view.render())

    def test_anonymous_user_bring_button(self):
        logout()
        self.assertFalse(user_is_contributor_in_entity_which_authorize_to_bring_news())
