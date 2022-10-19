.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.


.. image:: https://github.com/IMIO/imio.news.core/workflows/Tests/badge.svg
    :target: https://github.com/IMIO/imio.news.core/actions?query=workflow%3ATests
    :alt: CI Status

.. image:: https://coveralls.io/repos/github/IMIO/imio.news.core/badge.svg?branch=main
    :target: https://coveralls.io/github/IMIO/imio.news.core?branch=main
    :alt: Coveralls

.. image:: https://img.shields.io/pypi/v/imio.news.core.svg
    :target: https://pypi.python.org/pypi/imio.news.core/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/status/imio.news.core.svg
    :target: https://pypi.python.org/pypi/imio.news.core
    :alt: Egg Status

.. image:: https://img.shields.io/pypi/pyversions/imio.news.core.svg?style=plastic   :alt: Supported - Python Versions

.. image:: https://img.shields.io/pypi/l/imio.news.core.svg
    :target: https://pypi.python.org/pypi/imio.news.core/
    :alt: License


==================
imio.news.core
==================

Core product for iMio news websites

Features
--------

This products contains:
 - Content types: Folder, News, ...


Examples
--------

- https://actualites.enwallonie.be


Documentation
-------------

TODO


Translations
------------

This product has been translated into

- French

The translation domain is ``imio.smartweb`` and the translations are stored in `imio.smartweb.locales <https://github.com/IMIO/imio.smartweb.locales>`_ package.


Known issues
------------

- Dexterity Plone site & multilingual roots are not yet handled.


Installation
------------

Install imio.news.core by adding it to your buildout::

    [buildout]

    ...

    eggs =
        imio.news.core


and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/imio/imio.news.core/issues
- Source Code: https://github.com/imio/imio.news.core


License
-------

The project is licensed under the GPLv2.
