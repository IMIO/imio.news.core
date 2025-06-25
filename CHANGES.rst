Changelog
=========


1.2.16 (2025-06-25)
-------------------

- WEB-4279 : Fix a bug when subscripting news folder to another
  Sometimes, removed/missing local categories failed when reindexing objects
  [boulch]

- WEB-4278 : Create translated (de) news categories vocabulary for e-guichet (citizen project)
  [boulch]


1.2.15 (2025-05-14)
-------------------

- Update Python classifiers to be compatible with Python 3.13
  [remdub]

- Upgrade dev environment to Plone 6.1-latest
  [remdub]

- Update Python classifiers to be compatible with Python 3.12
  [remdub]

- Migrate to Plone 6.0.14
  [boulch]

- WEB-4119 : Prevent removing news folder if there is at least 1 news in it
  [boulch]


1.2.14 (2025-01-09)
-------------------

- WEB-4153 : Add a new cacheRuleset to use with our custom rest endpoints
  [remdub]

- GHA tests on Python 3.8 3.9 and 3.10
  [remdub]


1.2.13 (2024-06-20)
-------------------

- WEB-4088 : Use one state workflow for imio.news.NewsFolder / imio.news.Folder
  [boulch]


1.2.12 (2024-06-19)
-------------------

- Add news lead image (preview scale) for odwb
  [boulch]


1.2.11 (2024-06-06)
-------------------

- WEB-4113 : Use `TranslatedAjaxSelectWidget` to fix select2 values translation
  [laulaz]


1.2.10 (2024-05-31)
-------------------

- WEB-4088 : Fix missing include in zcml for ODWB endpoints
  [laulaz]


1.2.9 (2024-05-27)
------------------

- WEB-4101 : Add index for local category search
  [laulaz]

- Fix bad permission name
  [laulaz]

- WEB-4088 : Cover use case for sending data in odwb for a staging environment
  [boulch]

- WEB-4088 : Add some odwb endpoints (for news , for entities)
  [boulch]


1.2.8 (2024-05-02)
------------------

- WEB-4101 : Use local category (if any) instead of category in `category_title` indexer
  [laulaz]


1.2.7 (2024-04-04)
------------------

- Fix : serializer and message "At least one of these parameters must be supplied: path, UID"
  [boulch]


1.2.6 (2024-03-28)
------------------

- MWEBPM-9 : Add container_uid as metadata_field to retrieve news folder id/title in news serializer and set it in our json dataset
  [boulch]


1.2.5 (2024-03-25)
------------------

- Fix template for translations
  [boulch]


1.2.4 (2024-03-20)
------------------

- WEB-4068 : Add field to limit the new feature "adding news in any news folders" to some entities
  [boulch]


1.2.3 (2024-03-12)
------------------

- WEB-4068 : Adding news in any news folders where user have rights
  [boulch]


1.2.2 (2024-02-28)
------------------

- WEB-4072, WEB-4073 : Enable solr.fields behavior on some content types
  [remdub]

- WEB-4006 : Exclude some content types from search results
  [remdub]

- MWEBRCHA-13 : Add versioning on imio.news.NewsItem
  [boulch]


1.2.1 (2024-01-09)
------------------

- WEB-4041 : Handle new "carre" scale
  [boulch]


1.2 (2023-10-25)
----------------

- WEB-3985 : Use new portrait / paysage scales & logic
  [boulch, laulaz]

- WEB-3985 : Remove old cropping information when image changes
  [boulch, laulaz]


1.1.4 (2023-09-21)
------------------

- WEB-3989 : Fix infinite loop on object deletion
  [laulaz]

- Migrate to Plone 6.0.4
  [boulch]


1.1.3 (2023-03-13)
------------------

- Add warning message if images are too small to be cropped
  [laulaz]

- Migrate to Plone 6.0.2
  [boulch]

- Fix reindex after cut / copy / paste in some cases
  [laulaz]


1.1.2 (2023-02-20)
------------------

- Remove unused title_fr and description_fr metadatas
  [laulaz]

- Remove SearchableText_fr (Solr will use SearchableText for FR)
  [laulaz]


1.1.1 (2023-01-12)
------------------

- Add new descriptions metadatas and SearchableText indexes for multilingual
  [laulaz]


1.1 (2022-12-20)
----------------

- Update to Plone 6.0.0 final
  [boulch]


1.0.1 (2022-11-15)
------------------

- Fix SearchableText index for multilingual
  [laulaz]


1.0 (2022-11-15)
----------------

- Add multilingual features: New fields, vocabularies translations, restapi serializer
  [laulaz]


1.0a5 (2022-10-30)
------------------

- WEB-3757 : Automaticaly create some defaults newsfolders (with newsfolder subscription) when creating a new entity
- Fix deprecated get_mimetype_icon
- WEB-3757 : Automaticaly create some defaults newsfolders (with newsfolder subscription) when creating a new entity
- Fix deprecated get_mimetype_icon
  [boulch]

- Add eea.faceted.navigable behavior on Entity & NewsFolder types
  [laulaz]


1.0a4 (2022-08-10)
------------------

- WEB-3726 : Add subjects (keyword) in SearchableText
  [boulch]


1.0a3 (2022-07-14)
------------------

- Add serializer to get included items when you request an imio.news.NewsItem fullbobjects
  [boulch]

- Ensure objects are marked as modified after appending to a list attribute
  [laulaz]

- Fix selected_news_folders on newsitems after creating a "linked" newsfolder
  [boulch]


1.0a2 (2022-05-03)
------------------

- Use unique urls for images scales to ease caching
  [boulch]

- Use common.interfaces.ILocalManagerAware to mark a locally manageable content
  [boulch]

- Update buildout to use Plone 6.0.0a3 packages versions
  [boulch]


1.0a1 (2022-01-25)
------------------

- Initial release.
  [boulch]
