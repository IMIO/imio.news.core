# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from Acquisition import aq_parent
from imio.news.core.contents import IEntity
from imio.smartweb.locales import SmartwebMessageFactory as _
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class NewsCategoriesVocabularyFactory:
    def __call__(self, context=None):
        values = [
            (u"job_offer", _(u"Job offer")),
            (u"presse", _(u"Presse")),
            (u"city_project", _(u"City project")),
            (u"works", _(u"Works")),
        ]
        terms = [SimpleTerm(value=t[0], token=t[0], title=t[1]) for t in values]
        return SimpleVocabulary(terms)


NewsCategoriesVocabulary = NewsCategoriesVocabularyFactory()


class NewsLocalCategoriesVocabularyFactory:
    def __call__(self, context=None):
        obj = context
        while not IEntity.providedBy(obj):
            obj = aq_parent(aq_inner(obj))
        if not obj.local_categories:
            return SimpleVocabulary([])

        values = obj.local_categories.split("\n")
        terms = [SimpleTerm(value=t, token=t, title=t) for t in values]
        return SimpleVocabulary(terms)


NewsLocalCategoriesVocabulary = NewsLocalCategoriesVocabularyFactory()
