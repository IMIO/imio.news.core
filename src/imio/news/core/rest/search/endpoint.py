# -*- coding: utf-8 -*-

from plone.restapi.services.search.get import SearchGet as BaseSearchGet


class SearchGet(BaseSearchGet):
    def reply(self):
        self.request.form.pop("wcatoken", None)
        return super(SearchGet, self).reply()
