# -*- coding: utf-8 -*-

from imio.news.core.testing import IMIO_NEWS_CORE_INTEGRATION_TESTING  # noqa: E501
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from Products.CMFPlone.utils import get_installer

import unittest


class TestSetup(unittest.TestCase):
    """Test that imio.news.core is properly installed."""

    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])

    def test_product_installed(self):
        """Test if imio.news.core is installed."""
        self.assertTrue(self.installer.is_product_installed("imio.news.core"))

    def test_browserlayer(self):
        """Test that IImioNewsCoreLayer is registered."""
        from imio.news.core.interfaces import IImioNewsCoreLayer
        from plone.browserlayer import utils

        self.assertIn(IImioNewsCoreLayer, utils.registered_layers())

    def test_profile_version(self):
        portal_setup = api.portal.get_tool("portal_setup")
        self.assertEqual(
            portal_setup.getVersionForProfile("imio.news.core:default"), "1021"
        )

    def test_contact_metadata_columns(self):
        catalog = api.portal.get_tool("portal_catalog")
        columns = catalog.schema()
        for name in (
            "contact_name",
            "contact_email",
            "contact_phone",
            "directory_linked_contact",
        ):
            self.assertIn(name, columns)

    def test_edit_bundle_points_at_the_shared_script(self):
        self.assertEqual(
            api.portal.get_registry_record(
                "plone.bundles/imio-news-core-edit.jscompilation"
            ),
            "++plone++imio.smartweb.common/directory_contact_autofill.js",
        )


class TestUninstall(unittest.TestCase):
    layer = IMIO_NEWS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstall_product("imio.news.core")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if imio.news.core is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed("imio.news.core"))

    def test_browserlayer_removed(self):
        """Test that IImioNewsCoreLayer is removed."""
        from imio.news.core.interfaces import IImioNewsCoreLayer
        from plone.browserlayer import utils

        self.assertNotIn(IImioNewsCoreLayer, utils.registered_layers())


# <audit>
#   <file>test_setup.py</file>
#   <requirements_applied>Task 7 step 1</requirements_applied>
#   <deviations>
#     test_profile_version: the brief's literal assertion
#     (self.installer.get_product_version("imio.news.core") == "1021") cannot
#     pass. Products.CMFPlone.controlpanel.browser.quickinstaller.InstallerView
#     .get_product_version() returns the package's setuptools distribution
#     version (e.g. "1.2.29.dev0"), not the GenericSetup default profile
#     version. Verified empirically: the assertion fails with
#     '1.2.29.dev0' != '1021'. Replaced with
#     portal_setup.getVersionForProfile("imio.news.core:default"), which reads
#     the <version> declared in profiles/default/metadata.xml and is the
#     correct API to check the profile bump this test is meant to guard.
#   </deviations>
#   <questions>None</questions>
# </audit>
