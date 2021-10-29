# -*- coding: utf-8 -*-

from embeddify import Embedder
from imio.smartweb.common.utils import get_term_from_vocabulary
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.app.contenttypes.browser.folder import FolderView
from Products.CMFPlone.resources import add_bundle_on_request
from zope.i18n import translate


class View(FolderView):
    def __call__(self):
        images = self.context.listFolderContents(contentFilter={"portal_type": "Image"})
        if len(images) > 0:
            add_bundle_on_request(self.request, "spotlightjs")
            add_bundle_on_request(self.request, "flexbin")
        return self.index()

    def files(self):
        return self.context.listFolderContents(contentFilter={"portal_type": "File"})

    def images(self):
        return self.context.listFolderContents(contentFilter={"portal_type": "Image"})

    def has_leadimage(self):
        if ILeadImage.providedBy(self.context) and getattr(
            self.context, "image", False
        ):
            return True
        return False

    def get_embed_video(self):
        embedder = Embedder(width=800, height=600)
        return embedder(self.context.video_url, params=dict(autoplay=False))

    def category(self):
        term = get_term_from_vocabulary(
            "imio.news.vocabulary.NewsCategories", self.context.category
        )
        return term.title

    def topics(self):
        topics = self.context.topics
        items = []
        for item in topics:
            term = get_term_from_vocabulary("imio.smartweb.vocabulary.Topics", item)
            translated_title = translate(_(term.title), context=self.request)
            items.append(translated_title)
        return ", ".join(items)

    def iam(self):
        iam = self.context.iam
        items = []
        for item in iam:
            term = get_term_from_vocabulary("imio.smartweb.vocabulary.IAm", item)
            translated_title = translate(_(term.title), context=self.request)
            items.append(translated_title)
        return ", ".join(items)

    def effective_date(self):
        if self.context.EffectiveDate() == "None":
            return
        return self.context.effective().strftime("%d/%m/%Y")

    def expiration_date(self):
        if self.context.ExpirationDate() == "None":
            return
        return self.context.expires().strftime("%d/%m/%Y")
