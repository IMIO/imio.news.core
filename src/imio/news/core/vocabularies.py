# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from imio.news.core.contents import IEntity
from imio.news.core.contents import INewsFolder
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.utils import parent
from zope.component import getUtility
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory


class NewsCategoriesVocabularyFactory:
    def __call__(self, context=None):
        values = [
            ("job_offer", _("Job offer")),
            ("presse", _("Presse")),
            ("city_project", _("City project")),
            ("works", _("Works")),
        ]
        terms = [SimpleTerm(value=t[0], token=t[0], title=t[1]) for t in values]
        return SimpleVocabulary(terms)


NewsCategoriesVocabulary = NewsCategoriesVocabularyFactory()


class NewsLocalCategoriesVocabularyFactory:
    def __call__(self, context=None):
        if IPloneSiteRoot.providedBy(context):
            # ex: call on @types or @vocabularies from RESTAPI
            return SimpleVocabulary([])
        obj = context
        while not IEntity.providedBy(obj) and obj is not None:
            obj = parent(obj)
        if not obj.local_categories:
            return SimpleVocabulary([])

        values = obj.local_categories.splitlines()
        terms = [SimpleTerm(value=t, token=t, title=t) for t in values]
        return SimpleVocabulary(terms)


NewsLocalCategoriesVocabulary = NewsLocalCategoriesVocabularyFactory()


class NewsCategoriesAndTopicsVocabularyFactory:
    def __call__(self, context=None):
        news_categories_factory = getUtility(
            IVocabularyFactory, "imio.news.vocabulary.NewsCategories"
        )

        news_local_categories_factory = getUtility(
            IVocabularyFactory, "imio.news.vocabulary.NewsLocalCategories"
        )

        topics_factory = getUtility(
            IVocabularyFactory, "imio.smartweb.vocabulary.Topics"
        )

        terms = []

        for term in news_categories_factory(context):
            terms.append(
                SimpleTerm(
                    value=term.value,
                    token=term.token,
                    title=term.title,
                )
            )

        for term in news_local_categories_factory(context):
            terms.append(
                SimpleTerm(
                    value=term.value,
                    token=term.token,
                    title=term.title,
                )
            )

        for term in topics_factory(context):
            terms.append(
                SimpleTerm(
                    value=term.value,
                    token=term.token,
                    title=term.title,
                )
            )
        return SimpleVocabulary(terms)


NewsCategoriesAndTopicsVocabulary = NewsCategoriesAndTopicsVocabularyFactory()


class NewsFoldersUIDsVocabularyFactory:
    def __call__(self, context=None):
        portal = api.portal.get()
        brains = api.content.find(
            context=portal,
            portal_type="imio.news.NewsFolder",
            sort_on="sortable_title",
        )
        terms = [
            SimpleTerm(value=b.UID, token=b.UID, title=b.breadcrumb) for b in brains
        ]
        return SimpleVocabulary(terms)


NewsFoldersUIDsVocabulary = NewsFoldersUIDsVocabularyFactory()


class UserNewsFoldersVocabularyFactory:

    def __call__(self, context=None):
        site = api.portal.get()
        user = site.portal_membership.getAuthenticatedMember()
        terms = []
        permission = "imio.news.core: Add NewsItem"
        brains = api.content.find(object_provides=[INewsFolder])
        for brain in brains:
            obj = brain.getObject()
            try:
                # Display only news fodlers where user has the permission to add a news
                if user.has_permission(permission, obj):
                    terms.append(SimpleTerm(value=brain.UID, title=brain.breadcrumb))
            except Unauthorized:
                pass
        sorted_terms = sorted(terms, key=lambda x: x.title)
        return SimpleVocabulary(sorted_terms)


UserNewsFoldersVocabulary = UserNewsFoldersVocabularyFactory()
