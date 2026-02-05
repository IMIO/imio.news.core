from imio.news.core.utils import ENDPOINT_CACHE_KEY
from plone.memoize import ram
from plone.restapi.services.search.get import SearchGet as BaseSearchGet
from zope.annotation.interfaces import IAnnotations
from zope.component.hooks import getSite


def _cachekey(method, self):
    req = self.request
    site = getSite()
    ann = IAnnotations(site)
    gen = ann.get(ENDPOINT_CACHE_KEY, 0)

    params = tuple(sorted(req.form.items()))
    lang = req.get("LANGUAGE", "")
    return (site.getId(), gen, params, lang)


class SearchGet(BaseSearchGet):

    @ram.cache(_cachekey)
    def _cached_reply(self):
        return super().reply()

    def reply(self):
        return self._cached_reply()
