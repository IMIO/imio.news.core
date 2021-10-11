# -*- coding: utf-8 -*-

from imio.news.core.contents.newsfolder.content import INewsFolder  # NOQA E501
from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING  # noqa
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import createObject
from zope.component import queryUtility
from zope.lifecycleevent import modified
from z3c.relationfield import RelationValue
from z3c.relationfield.interfaces import IRelationList
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import Attributes

import unittest


class TestNewsFolder(unittest.TestCase):

    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.authorized_types_in_newsfolder = [
            "imio.news.Folder",
            "imio.news.NewsItem",
        ]
        self.unauthorized_types_in_newsfolder = [
            "imio.news.NewsFolder",
            "Document",
            "File",
            "Image",
        ]

        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.parent = self.portal
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="imio.news.Entity",
        )

    def test_ct_newsfolder_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsFolder")
        schema = fti.lookupSchema()
        self.assertEqual(INewsFolder, schema)

    def test_ct_newsfolder_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsFolder")
        self.assertTrue(fti)

    def test_ct_newsfolder_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsFolder")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            INewsFolder.providedBy(obj),
            u"INewsFolder not provided by {0}!".format(
                obj,
            ),
        )

    def test_ct_newsfolder_adding(self):
        obj = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            id="imio.news.NewsFolder",
        )

        self.assertTrue(
            INewsFolder.providedBy(obj),
            u"INewsFolder not provided by {0}!".format(
                obj.id,
            ),
        )

        parent = obj.__parent__
        self.assertIn("imio.news.NewsFolder", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("imio.news.NewsFolder", parent.objectIds())

    def test_ct_newsfolder_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsFolder")
        self.assertFalse(
            fti.global_allow, u"{0} is not globally addable!".format(fti.id)
        )

    def test_ct_newsfolder_filter_content_type_true(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsFolder")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.entity,
            "imio.news.NewsFolder_id",
            title="imio.news.NewsFolder container",
        )
        folder = self.entity[parent_id]
        for t in self.unauthorized_types_in_newsfolder:
            with self.assertRaises(InvalidParameterError):
                api.content.create(
                    container=folder,
                    type=t,
                    title="My {}".format(t),
                )
        for t in self.authorized_types_in_newsfolder:
            api.content.create(
                container=folder,
                type=t,
                title="My {}".format(t),
            )
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=folder,
                type="imio.news.Entity",
                title="My Entity",
            )

    def test_populating_newsfolders(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        newsfolder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            id="imio.news.NewsFolder",
        )
        entity2 = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="entity2",
        )
        newsfolder2 = api.content.create(
            container=entity2,
            type="imio.news.NewsFolder",
            id="newsfolder2",
        )
        newsitem2 = api.content.create(
            container=newsfolder2,
            type="imio.news.NewsItem",
            id="newsitem2",
        )
        entity3 = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            id="entity3",
        )
        newsfolder3 = api.content.create(
            container=entity3,
            type="imio.news.NewsFolder",
            id="newsfolder3",
        )
        newsitem3 = api.content.create(
            container=newsfolder3,
            type="imio.news.NewsItem",
            id="newsitem3",
        )
        intids = getUtility(IIntIds)

        # Link newsfolder2 (all these news) to our object "newsfolder".
        setattr(
            newsfolder,
            "populating_newsfolders",
            [RelationValue(intids.getId(newsfolder2))],
        )
        modified(newsfolder, Attributes(IRelationList, "populating_newsfolders"))
        # So newsfolder.uid() can be find on newsitem2
        self.assertIn(newsfolder.UID(), newsitem2.selected_news_folders)

        # Clear linking newsfolders out of our object "newsfolder".
        setattr(newsfolder, "populating_newsfolders", [])
        modified(newsfolder, Attributes(IRelationList, "populating_newsfolders"))
        # So newsfolder.uid() can not be find on newsitem2
        self.assertNotIn(newsfolder.UID(), newsitem2.selected_news_folders)

        # First, link newsfolder2 and newsfolder3
        setattr(
            newsfolder,
            "populating_newsfolders",
            [
                RelationValue(intids.getId(newsfolder2)),
                RelationValue(intids.getId(newsfolder3)),
            ],
        )
        modified(newsfolder, Attributes(IRelationList, "populating_newsfolders"))
        # Assert link is OK
        self.assertIn(newsfolder.UID(), newsitem2.selected_news_folders)
        self.assertIn(newsfolder.UID(), newsitem3.selected_news_folders)

        # Next, we delete newsfolder so we remove this newsfolder.UID() out of news.
        api.content.delete(newsfolder)
        self.assertNotIn(newsfolder.UID(), newsitem2.selected_news_folders)
        self.assertNotIn(newsfolder.UID(), newsitem3.selected_news_folders)
