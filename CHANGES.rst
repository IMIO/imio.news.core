Changelog
=========


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
