# -*- coding: utf-8 -*-

from imio.news.core.contents import INewsItem
from imio.news.core.interfaces import IImioNewsCoreLayer
from imio.news.core.testing import IMIO_NEWS_CORE_FUNCTIONAL_TESTING
from imio.news.core.tests.utils import make_named_image
from plone import api
from plone.app.contenttypes.behaviors.leadimage import ILeadImageBehavior
from plone.app.dexterity.behaviors.metadata import IBasic
from plone.app.imagecropping import PAI_STORAGE_KEY
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from plone.dexterity.interfaces import IDexterityFTI
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from z3c.relationfield import RelationValue
from z3c.relationfield.interfaces import IRelationList
from zope.annotation.interfaces import IAnnotations
from zope.component import createObject
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.interface import alsoProvides
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import modified
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestNewsItem(unittest.TestCase):
    layer = IMIO_NEWS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests"""
        self.authorized_types_in_newsitem = ["File", "Image"]

        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
        )
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Entity",
        )
        self.news_folder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            title="News folder",
        )

    def test_ct_newsitem_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsItem")
        schema = fti.lookupSchema()
        self.assertEqual(INewsItem, schema)

    def test_ct_newsitem_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsItem")
        self.assertTrue(fti)

    def test_ct_newsitem_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.news.NewsItem")
        factory = fti.factory
        obj = createObject(factory)

        self.assertTrue(
            INewsItem.providedBy(obj),
            "INewsItem not provided by {0}!".format(
                obj,
            ),
        )

    def test_news_local_category(self):
        news = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="my-news",
        )
        factory = getUtility(
            IVocabularyFactory, "imio.news.vocabulary.NewsLocalCategories"
        )
        vocabulary = factory(news)
        self.assertEqual(len(vocabulary), 0)

        self.entity.local_categories = [
            {"fr": "First", "nl": "", "de": "", "en": ""},
            {"fr": "Second", "nl": "", "de": "", "en": ""},
            {"fr": "Third", "nl": "", "de": "", "en": ""},
        ]
        vocabulary = factory(news)
        self.assertEqual(len(vocabulary), 3)

    def test_view(self):
        newsitem = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="My news item",
        )
        view = queryMultiAdapter((newsitem, self.request), name="view")
        self.assertIn("My news item", view())

    def test_embed_video(self):
        newsitem = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="My news item",
        )
        newsitem.video_url = "https://www.youtube.com/watch?v=_dOAthafoGQ"
        view = queryMultiAdapter((newsitem, self.request), name="view")
        embedded_video = view.get_embed_video()
        self.assertIn("iframe", embedded_video)
        self.assertIn(
            "https://www.youtube.com/embed/_dOAthafoGQ?feature=oembed", embedded_video
        )

    def test_has_leadimage(self):
        newsitem = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="My news item",
        )
        view = queryMultiAdapter((newsitem, self.request), name="view")
        self.assertEqual(view.has_leadimage(), False)
        newsitem.image = NamedBlobImage(**make_named_image())
        self.assertEqual(view.has_leadimage(), True)

    def test_subscriber_to_select_current_news_folder(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="My news item",
        )
        self.assertEqual(news_item.selected_news_folders, [self.news_folder.UID()])

    def test_searchable_text(self):
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="Title",
        )
        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(indexes.get("SearchableText"), ["title"])

        news_item.description = "Description"
        news_item.topics = ["agriculture"]
        news_item.category = "works"
        news_item.text = RichTextValue("<p>Text</p>", "text/html", "text/html")
        news_item.reindexObject()

        catalog = api.portal.get_tool("portal_catalog")
        brain = api.content.find(UID=news_item.UID())[0]
        indexes = catalog.getIndexDataForRID(brain.getRID())
        self.assertEqual(
            indexes.get("SearchableText"),
            [
                "title",
                "description",
                "text",
                "agriculture",
                "travaux",
            ],
        )

    def test_referrer_newsfolders(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        intids = getUtility(IIntIds)
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
        setattr(
            self.news_folder,
            "populating_newsfolders",
            [RelationValue(intids.getId(newsfolder2))],
        )
        modified(self.news_folder, Attributes(IRelationList, "populating_newsfolders"))
        self.assertIn(self.news_folder.UID(), newsitem2.selected_news_folders)

        # if we create an newsitem in an newsfolder that is referred in another newsfolder
        # then, referrer newsfolder UID is in newsitem.selected_news_folders list.
        newsitem2b = api.content.create(
            container=newsfolder2,
            type="imio.news.NewsItem",
            id="newsitem2b",
        )
        self.assertIn(self.news_folder.UID(), newsitem2b.selected_news_folders)

    def test_automaticaly_readd_container_newsfolder_uid(self):
        newsitem = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
        )
        self.assertIn(self.news_folder.UID(), newsitem.selected_news_folders)
        newsitem.selected_news_folders = []
        newsitem.reindexObject()
        modified(newsitem)
        self.assertIn(self.news_folder.UID(), newsitem.selected_news_folders)

    def test_removing_old_cropping(self):
        newsitem = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            id="newsitem",
        )
        newsitem.image = NamedBlobImage(**make_named_image())
        view = newsitem.restrictedTraverse("@@crop-image")
        view._crop(fieldname="image", scale="portrait_affiche", box=(1, 1, 200, 200))
        annotation = IAnnotations(newsitem).get(PAI_STORAGE_KEY)
        self.assertEqual(annotation, {"image_portrait_affiche": (1, 1, 200, 200)})

        modified(newsitem, Attributes(IBasic, "IBasic.title"))
        annotation = IAnnotations(newsitem).get(PAI_STORAGE_KEY)
        self.assertEqual(annotation, {"image_portrait_affiche": (1, 1, 200, 200)})

        modified(newsitem, Attributes(ILeadImageBehavior, "ILeadImageBehavior.image"))
        annotation = IAnnotations(newsitem).get(PAI_STORAGE_KEY)
        self.assertEqual(annotation, {})

    def test_name_chooser(self):
        news = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="news",
        )
        self.assertEqual(news.id, news.UID())

        entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="my-entity",
        )
        self.assertNotEqual(entity.id, entity.UID())
        self.assertEqual(entity.id, "my-entity")

    def test_js_bundles(self):
        newsitem = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="NewsItem",
        )

        alsoProvides(self.request, IImioNewsCoreLayer)
        getMultiAdapter((newsitem, self.request), name="view")()
        bundles = getattr(self.request, "enabled_bundles", [])
        self.assertEqual(len(bundles), 0)
        image = api.content.create(
            container=newsitem,
            type="Image",
            title="Image",
        )
        image.image = NamedBlobImage(**make_named_image())
        getMultiAdapter((newsitem, self.request), name="view")()
        bundles = getattr(self.request, "enabled_bundles", [])
        self.assertEqual(len(bundles), 2)
        self.assertListEqual(bundles, ["spotlightjs", "flexbin"])

    def test_files_in_newsitem_view(self):
        newsitem = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="NewsItem",
        )
        view = queryMultiAdapter((newsitem, self.request), name="view")
        self.assertNotIn("event-files", view())
        file_obj = api.content.create(
            container=newsitem,
            type="File",
            title="file",
        )
        file_obj.file = NamedBlobFile(data="file data", filename="file.txt")
        view = queryMultiAdapter((newsitem, self.request), name="view")
        self.assertIn("++resource++mimetype.icons/txt.png", view())
