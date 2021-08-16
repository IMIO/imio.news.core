# -*- coding: utf-8 -*-

from imio.smartweb.locales import SmartwebMessageFactory as _
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class NewsCategoriesVocabularyFactory:
    def __call__(self, context=None):
        values = [
            (u"presse", _(u"Presse")),
            (u"works", _(u"Works")),
            (u"job_offer", _(u"Job offer")),
            (u"city_project", _(u"City project")),
        ]
        terms = [SimpleTerm(value=t[0], token=t[0], title=t[1]) for t in values]
        return SimpleVocabulary(terms)


NewsCategoriesVocabulary = NewsCategoriesVocabularyFactory()
