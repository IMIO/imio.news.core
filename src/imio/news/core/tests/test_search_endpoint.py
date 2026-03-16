# -*- coding: utf-8 -*-
"""Tests for WEB-4366: @search caching endpoint refactoring.

The commit refactors the cache key strategy to use entity_uid directly
(instead of resolving it from any UID) and introduces three dedicated
cached endpoint classes: SearchEntity, SearchNewsFolderForEntity,
SearchNewsItems.
"""
from imio.news.core.rest.search.endpoint import _first
from imio.news.core.rest.search.endpoint import _items_from_req
from imio.news.core.rest.search.endpoint import _norm
from imio.news.core.rest.search.endpoint import _query_from_req
from imio.news.core.rest.search.endpoint import _cachekey_entity
from imio.news.core.rest.search.endpoint import _cachekey_newsfolder_for_entity
from imio.news.core.rest.search.endpoint import _cachekey_newsitems
from imio.news.core.rest.search.endpoint import SearchEntity
from imio.news.core.rest.search.endpoint import SearchNewsFolderForEntity
from imio.news.core.rest.search.endpoint import SearchNewsItems
from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING
from imio.news.core.tests.utils import mock_odwb
from imio.news.core.utils import ENDPOINT_CACHE_KEY
from plone import api
from plone.app.dexterity.behaviors.metadata import IBasic
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest.mock import MagicMock
from unittest.mock import patch
from zope.annotation.interfaces import IAnnotations
from zope.component.hooks import setSite
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import modified

import unittest


# ---------------------------------------------------------------------------
# Pure unit tests – no Plone machinery required
# ---------------------------------------------------------------------------


class TestNorm(unittest.TestCase):
    """_norm() is used to make request form values hashable so they can be
    included in a tuple-based RAM cache key.  Lists and tuples become tuples;
    any other value is returned as-is."""

    def test_list_becomes_tuple(self):
        # Lists are not hashable; they must be converted to tuples for use in
        # cache keys.
        self.assertEqual(_norm([1, 2, 3]), (1, 2, 3))

    def test_tuple_unchanged(self):
        # Tuples are already hashable, no conversion needed.
        self.assertEqual(_norm((1, 2)), (1, 2))

    def test_scalar_unchanged(self):
        # Scalars (str, int, None …) pass through untouched.
        self.assertEqual(_norm("hello"), "hello")
        self.assertEqual(_norm(42), 42)
        self.assertIsNone(_norm(None))


class TestFirst(unittest.TestCase):
    """_first() extracts the first element of a list/tuple, or returns the
    value itself when it is a scalar.  It is used throughout the endpoint to
    normalise parameters that Zope may deliver as either a single value or a
    list (e.g. ``UID`` or ``entity_uid`` in the query string)."""

    def test_list_returns_first(self):
        # The most common case: a repeated query-string key arrives as a list.
        self.assertEqual(_first(["a", "b"]), "a")

    def test_empty_list_returns_none(self):
        # An empty list means the parameter was provided but has no value.
        self.assertIsNone(_first([]))

    def test_tuple_returns_first(self):
        self.assertEqual(_first(("x", "y")), "x")

    def test_scalar_returned_as_is(self):
        # A single value (not wrapped in a list) is returned unchanged.
        self.assertEqual(_first("abc"), "abc")
        self.assertIsNone(_first(None))


class TestItemsFromReq(unittest.TestCase):
    """_items_from_req() serialises the request form into a stable, sorted
    tuple of (key, value) pairs that can be embedded in a RAM cache key.
    Volatile/irrelevant keys are excluded so they don't cause spurious cache
    misses."""

    def _make_req(self, form):
        req = MagicMock()
        req.form = form
        return req

    def test_items_sorted_by_key(self):
        # Sorting guarantees that two requests with the same parameters in
        # different order produce the same cache key.
        req = self._make_req({"z": "last", "a": "first"})
        items = _items_from_req(req)
        self.assertEqual(items, (("a", "first"), ("z", "last")))

    def test_ignored_keys_excluded(self):
        # cache_key, _ (jQuery timestamp) and authenticator are request-level
        # noise; they must not pollute the cache key.
        req = self._make_req(
            {
                "cache_key": "xxx",
                "_": "timestamp",
                "authenticator": "token",
                "portal_type": "imio.news.NewsItem",
            }
        )
        items = _items_from_req(req)
        self.assertEqual(items, (("portal_type", "imio.news.NewsItem"),))

    def test_list_value_normalized_to_tuple(self):
        # List values would make the cache key unhashable; they are converted
        # to tuples via _norm().
        req = self._make_req({"ids": ["a", "b"]})
        items = _items_from_req(req)
        self.assertEqual(items, (("ids", ("a", "b")),))

    def test_empty_form_returns_empty_tuple(self):
        req = self._make_req({})
        self.assertEqual(_items_from_req(req), ())


class TestQueryFromReq(unittest.TestCase):
    """_query_from_req() converts the request form into a catalog query dict.
    It removes internal parameters that must not reach the catalog, and
    optionally appends a wildcard to SearchableText for prefix-search."""

    def _make_req(self, form):
        req = MagicMock()
        # Use a copy so mutations inside _query_from_req don't affect the
        # original dict (the function must not mutate req.form).
        req.form = form.copy()
        return req

    def test_pop_keys_removed_from_query(self):
        # Parameters like entity_uid, u, batch_size are routing/pagination
        # hints that must be stripped before the query hits the catalog.
        req = self._make_req({"entity_uid": "abc", "portal_type": "imio.news.NewsItem"})
        query = _query_from_req(req, pop_keys=("entity_uid",))
        self.assertNotIn("entity_uid", query)
        self.assertIn("portal_type", query)

    def test_searchabletext_wildcard_appended_by_default(self):
        # Prefix search is enabled by default: "hello" becomes "hello*" so
        # the catalog returns results that start with the typed string.
        req = self._make_req({"SearchableText": "hello"})
        query = _query_from_req(req)
        self.assertEqual(query["SearchableText"], "hello*")

    def test_searchabletext_already_wildcard_left_unchanged(self):
        # If the caller already added a trailing *, don't double it.
        req = self._make_req({"SearchableText": "hello*"})
        query = _query_from_req(req)
        self.assertEqual(query["SearchableText"], "hello*")

    def test_searchabletext_empty_string_left_unchanged(self):
        # An empty SearchableText means "no full-text filter"; don't add a
        # bare "*" which would match everything and slow down the query.
        req = self._make_req({"SearchableText": ""})
        query = _query_from_req(req)
        self.assertEqual(query["SearchableText"], "")

    def test_prefix_search_false_values_disable_wildcard(self):
        # Callers can opt out of prefix search by passing prefix_search=0/false/no.
        # This is useful when the caller already handles wildcard expansion.
        for falsy_value in ("0", "false", "False", "no"):
            req = self._make_req(
                {"SearchableText": "hello", "prefix_search": falsy_value}
            )
            query = _query_from_req(req)
            self.assertEqual(
                query["SearchableText"],
                "hello",
                f"prefix_search={falsy_value!r} should disable wildcard",
            )

    def test_prefix_search_key_always_removed_from_query(self):
        # prefix_search is a UI hint, not a catalog index; it must never reach
        # the catalog query regardless of its value.
        req = self._make_req({"SearchableText": "hello", "prefix_search": "1"})
        query = _query_from_req(req)
        self.assertNotIn("prefix_search", query)

    def test_original_request_form_not_mutated(self):
        # CRITICAL: _query_from_req works on a copy of req.form.  The original
        # form dict must stay intact because _items_from_req() reads it later
        # to build the RAM cache key.  Mutating it would corrupt the cache key.
        form = {"entity_uid": "abc", "SearchableText": "test"}
        req = self._make_req(form)
        _query_from_req(req, pop_keys=("entity_uid",))
        self.assertIn("entity_uid", req.form)
        self.assertEqual(req.form["SearchableText"], "test")


# ---------------------------------------------------------------------------
# Integration tests – require a Plone site
# ---------------------------------------------------------------------------


class TestCacheKey(unittest.TestCase):
    """Tests for _cachekey_by_entity_uid and the three public wrappers.

    The cache key is a tuple: (site_id, class_name, entity_uid, generation,
    sorted_params, language).  Each component must discriminate correctly so
    that two logically different requests never share the same cached result,
    and two logically identical requests always share it.
    """

    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Cache Key Test Entity",
        )
        # setSite() is required so that getSite() inside _cachekey_by_entity_uid
        # can resolve the portal and read its annotations.
        setSite(self.portal)

    def _make_service(self, cls, form, language="fr"):
        """Return a minimal service-like object suitable for cache key computation.

        We bypass __init__ with object.__new__ to avoid the full Zope machinery
        while still having the correct class identity (needed for the type_key
        component of the cache key).
        """
        svc = object.__new__(cls)
        svc.request = MagicMock()
        svc.request.form = form.copy()
        # req.get("LANGUAGE", "") is called inside the cache key function.
        svc.request.get.return_value = language
        svc.request.cookies = {}
        return svc

    def test_cachekey_with_uid_includes_entity_uid(self):
        # When the required UID param is present, the key embeds the entity UID
        # so that different entities produce different cache buckets.
        uid = self.entity.UID()
        svc = self._make_service(SearchEntity, {"UID": uid})
        key = _cachekey_entity(None, svc)
        self.assertIn(uid, key)
        self.assertNotIn("__no_entity__", key)

    def test_cachekey_without_uid_returns_no_entity_sentinel(self):
        # Without a UID the function falls back to a global "__no_entity__"
        # bucket so that un-scoped requests can still be cached together.
        svc = self._make_service(SearchEntity, {})
        key = _cachekey_entity(None, svc)
        self.assertIn("__no_entity__", key)

    def test_cachekey_includes_portal_id(self):
        # The portal ID discriminates between multi-site setups sharing the
        # same in-memory cache.
        uid = self.entity.UID()
        svc = self._make_service(SearchEntity, {"UID": uid})
        key = _cachekey_entity(None, svc)
        self.assertIn(self.portal.getId(), key)

    def test_cachekey_changes_after_generation_increment(self):
        # The "generation" counter stored in site annotations is the
        # invalidation mechanism: bumping it changes the cache key, which
        # forces a cache miss on the next request even if all other parameters
        # are identical.
        uid = self.entity.UID()
        svc = self._make_service(SearchNewsItems, {"entity_uid": uid})
        key_before = _cachekey_newsitems(None, svc)
        # Simulate a cache invalidation (normally triggered by a content event).
        ann = IAnnotations(self.portal)
        ann_key = f"{ENDPOINT_CACHE_KEY}{uid}"
        ann[ann_key] = int(ann.get(ann_key, 0)) + 1
        key_after = _cachekey_newsitems(None, svc)
        self.assertNotEqual(
            key_before,
            key_after,
            "Generation change must produce a different cache key",
        )

    def test_different_endpoint_classes_produce_different_keys(self):
        # SearchNewsFolderForEntity and SearchNewsItems serve different data
        # for the same entity.  The class name is part of the key so they
        # never share a cache entry.
        uid = self.entity.UID()
        svc_nf = self._make_service(SearchNewsFolderForEntity, {"entity_uid": uid})
        svc_ni = self._make_service(SearchNewsItems, {"entity_uid": uid})
        key_nf = _cachekey_newsfolder_for_entity(None, svc_nf)
        key_ni = _cachekey_newsitems(None, svc_ni)
        self.assertNotEqual(key_nf, key_ni)

    def test_different_languages_produce_different_keys(self):
        # The UI language is included in the key because translated content
        # may differ between languages.
        uid = self.entity.UID()
        svc_fr = self._make_service(SearchNewsItems, {"entity_uid": uid}, language="fr")
        svc_nl = self._make_service(SearchNewsItems, {"entity_uid": uid}, language="nl")
        key_fr = _cachekey_newsitems(None, svc_fr)
        key_nl = _cachekey_newsitems(None, svc_nl)
        self.assertNotEqual(key_fr, key_nl)

    def test_cachekey_newsfolder_for_entity_reads_entity_uid_param(self):
        # SearchNewsFolderForEntity expects its scope via the "entity_uid"
        # query parameter (not "UID").
        uid = self.entity.UID()
        svc = self._make_service(SearchNewsFolderForEntity, {"entity_uid": uid})
        key = _cachekey_newsfolder_for_entity(None, svc)
        self.assertIn(uid, key)

    def test_cachekey_newsitems_reads_entity_uid_param(self):
        # Same as above for SearchNewsItems.
        uid = self.entity.UID()
        svc = self._make_service(SearchNewsItems, {"entity_uid": uid})
        key = _cachekey_newsitems(None, svc)
        self.assertIn(uid, key)


class TestInvalidateEndpointSearchCache(unittest.TestCase):
    """Tests for invalidate_endpoint_search_cache() and the event subscribers
    that call it.

    The invalidation strategy stores an integer "generation" counter per
    entity in the site's IAnnotations.  Every time content inside an entity
    changes, the counter is incremented.  The cache key includes this counter,
    so the next request automatically misses the cache and fetches fresh data.
    """

    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="Invalidation Test Entity",
        )
        self.news_folder = api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            title="News Folder",
        )

    def _get_generation(self):
        """Read the current cache generation counter for self.entity."""
        ann = IAnnotations(self.portal)
        return ann.get(f"{ENDPOINT_CACHE_KEY}{self.entity.UID()}", 0)

    def test_direct_call_increments_generation(self):
        # Calling invalidate_endpoint_search_cache() directly must bump the
        # counter by exactly 1.
        from imio.news.core.subscribers import invalidate_endpoint_search_cache

        gen_before = self._get_generation()
        invalidate_endpoint_search_cache(self.news_folder)
        self.assertEqual(self._get_generation(), gen_before + 1)

    def test_does_not_raise_when_no_entity_parent(self):
        # During entity removal, the object being deleted has no IEntity
        # parent anymore.  The function must silently do nothing instead of
        # crashing, so that the removal can complete cleanly.
        from imio.news.core.subscribers import invalidate_endpoint_search_cache

        gen_before = self._get_generation()
        # The portal itself sits above any entity; it has no IEntity parent.
        invalidate_endpoint_search_cache(self.portal)
        # No exception raised and the generation counter is untouched.
        self.assertEqual(self._get_generation(), gen_before)

    def test_adding_newsfolder_triggers_invalidation(self):
        # Creating a new news folder fires IObjectAddedEvent → added_news_folder
        # → invalidate_endpoint_search_cache.
        gen_before = self._get_generation()
        api.content.create(
            container=self.entity,
            type="imio.news.NewsFolder",
            title="Another News Folder",
        )
        self.assertGreater(self._get_generation(), gen_before)

    def test_modifying_newsfolder_triggers_invalidation(self):
        # IObjectModifiedEvent → modified_newsfolder → invalidation.
        gen_before = self._get_generation()
        modified(self.news_folder)
        self.assertGreater(self._get_generation(), gen_before)

    def test_removing_newsfolder_triggers_invalidation(self):
        # IObjectRemovedEvent → removed_newsfolder → invalidation.
        # The newsfolder is still accessible (its __parent__ attribute is still
        # set) when the event fires, so the entity can be resolved.
        gen_before = self._get_generation()
        api.content.delete(obj=self.news_folder)
        self.assertGreater(self._get_generation(), gen_before)

    def test_adding_newsitem_triggers_invalidation(self):
        # IObjectAddedEvent on a NewsItem → added_news_item → invalidation.
        gen_before = self._get_generation()
        api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="News Item",
        )
        self.assertGreater(self._get_generation(), gen_before)

    def test_modifying_newsitem_triggers_invalidation(self):
        # modified_news_item only calls invalidate_endpoint_search_cache when
        # the event carries descriptions (early return otherwise).  We pass an
        # IBasic title attribute to satisfy that condition.
        # mock_odwb prevents an outbound ODWB call that would otherwise be
        # triggered if the item were published (it is not here, but we keep the
        # mock as a safety net).
        news_item = api.content.create(
            container=self.news_folder,
            type="imio.news.NewsItem",
            title="News Item",
        )
        gen_before = self._get_generation()
        with mock_odwb():
            modified(news_item, Attributes(IBasic, "IBasic.title"))
        self.assertGreater(self._get_generation(), gen_before)


class TestCachedEndpointRAMCache(unittest.TestCase):
    """Tests the MISS/HIT/MISS-after-invalidation cycle of the three cached
    endpoint classes using plone.memoize.ram.

    How the cache header protocol works
    ------------------------------------
    * On a cache MISS the decorated _cached_reply() body executes and sets
      ``X-RAM-Cache: MISS`` on the response.
    * On a cache HIT the body is skipped entirely so no header is set by
      _cached_reply().  reply() then detects the absent header and sets
      ``X-RAM-Cache: HIT``.
    * Without the REQUIRED_PARAM the endpoint bypasses the cache altogether
      and calls _search() directly; no X-RAM-Cache header is set at all.

    Each test method creates a fresh entity (hence a unique UID) in setUp,
    so test runs are isolated in the global RAM cache even though that cache
    is not reset between tests.
    """

    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.news.Entity",
            title="RAM Cache Test Entity",
        )
        self.entity_uid = self.entity.UID()
        # setSite() is required so the cache key function can resolve the portal.
        setSite(self.portal)

    def _make_response(self):
        """Return a mock response with a real header store.

        MagicMock's default behaviour would silently accept any setHeader call
        but getHeader would always return a new MagicMock (truthy), making
        the HIT/MISS detection in reply() unreliable.  We back the mock with
        a plain dict instead.
        """
        response = MagicMock()
        headers = {}
        response.setHeader.side_effect = lambda k, v: headers.__setitem__(k.lower(), v)
        response.getHeader.side_effect = lambda k: headers.get(k.lower())
        return response

    def _call_reply(self, cls, form, language="fr"):
        """Instantiate *cls* with a fresh request/response and call reply().

        A fresh request is used for every call so the response headers start
        empty, which is what a real WSGI server would give us.

        _search() is patched out to avoid catalog access: we are testing the
        caching layer, not the catalog query itself.
        """
        req = MagicMock()
        req.form = form.copy()
        req.get.return_value = language
        req.cookies = {}
        req.response = self._make_response()
        svc = object.__new__(cls)
        svc.context = self.portal
        svc.request = req
        with patch.object(
            cls, "_search", return_value={"items": [], "@id": "http://nohost/plone"}
        ):
            result = svc.reply()
        return result, req.response

    # --- SearchEntity -------------------------------------------------------

    def test_search_entity_first_call_is_miss(self):
        # The very first call for this entity UID has no cached result yet.
        _, resp = self._call_reply(SearchEntity, {"UID": self.entity_uid})
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "MISS")

    def test_search_entity_second_call_is_hit(self):
        # The second call with the same UID and params hits the in-memory cache.
        self._call_reply(SearchEntity, {"UID": self.entity_uid})
        _, resp = self._call_reply(SearchEntity, {"UID": self.entity_uid})
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "HIT")

    def test_search_entity_miss_again_after_cache_invalidation(self):
        # After incrementing the generation counter the cache key changes, so
        # the next call must be a MISS even though the params are identical.
        self._call_reply(SearchEntity, {"UID": self.entity_uid})
        ann = IAnnotations(self.portal)
        ann_key = f"{ENDPOINT_CACHE_KEY}{self.entity_uid}"
        ann[ann_key] = int(ann.get(ann_key, 0)) + 1
        _, resp = self._call_reply(SearchEntity, {"UID": self.entity_uid})
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "MISS")

    def test_search_entity_no_cache_header_without_uid(self):
        # Without the UID param, reply() bypasses the cache and calls _search()
        # directly.  No X-RAM-Cache header is set in that path.
        _, resp = self._call_reply(SearchEntity, {})
        self.assertIsNone(resp.getHeader("X-RAM-Cache"))

    # --- SearchNewsFolderForEntity ------------------------------------------

    def test_search_newsfolder_for_entity_first_call_is_miss(self):
        _, resp = self._call_reply(
            SearchNewsFolderForEntity, {"entity_uid": self.entity_uid}
        )
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "MISS")

    def test_search_newsfolder_for_entity_second_call_is_hit(self):
        self._call_reply(SearchNewsFolderForEntity, {"entity_uid": self.entity_uid})
        _, resp = self._call_reply(
            SearchNewsFolderForEntity, {"entity_uid": self.entity_uid}
        )
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "HIT")

    def test_search_newsfolder_for_entity_no_cache_without_entity_uid(self):
        # entity_uid is the REQUIRED_PARAM for this endpoint.
        _, resp = self._call_reply(SearchNewsFolderForEntity, {})
        self.assertIsNone(resp.getHeader("X-RAM-Cache"))

    # --- SearchNewsItems ----------------------------------------------------

    def test_search_newsitems_first_call_is_miss(self):
        _, resp = self._call_reply(SearchNewsItems, {"entity_uid": self.entity_uid})
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "MISS")

    def test_search_newsitems_second_call_is_hit(self):
        self._call_reply(SearchNewsItems, {"entity_uid": self.entity_uid})
        _, resp = self._call_reply(SearchNewsItems, {"entity_uid": self.entity_uid})
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "HIT")

    def test_search_newsitems_miss_again_after_cache_invalidation(self):
        self._call_reply(SearchNewsItems, {"entity_uid": self.entity_uid})
        ann = IAnnotations(self.portal)
        ann_key = f"{ENDPOINT_CACHE_KEY}{self.entity_uid}"
        ann[ann_key] = int(ann.get(ann_key, 0)) + 1
        _, resp = self._call_reply(SearchNewsItems, {"entity_uid": self.entity_uid})
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "MISS")

    def test_search_newsitems_no_cache_without_entity_uid(self):
        # entity_uid is the REQUIRED_PARAM for this endpoint.
        _, resp = self._call_reply(SearchNewsItems, {})
        self.assertIsNone(resp.getHeader("X-RAM-Cache"))

    def test_different_query_params_produce_independent_cache_entries(self):
        # The sorted param tuple is part of the cache key.  Two requests that
        # differ only in portal_type must not share a cached result.
        self._call_reply(
            SearchNewsItems,
            {"entity_uid": self.entity_uid, "portal_type": "imio.news.NewsItem"},
        )
        _, resp = self._call_reply(
            SearchNewsItems,
            {"entity_uid": self.entity_uid, "portal_type": "imio.news.NewsFolder"},
        )
        # Different params → different cache key → new MISS, not a HIT.
        self.assertEqual(resp.getHeader("X-RAM-Cache"), "MISS")
