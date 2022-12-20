Changelog
=========


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
