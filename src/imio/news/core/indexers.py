from plone.indexer import indexer
from imio.news.core.contents.newsitem.content import INewsItem


@indexer(INewsItem)
def category_and_topics_indexer(obj):
    list = []
    if obj.topics is not None:
        list = obj.topics

    list.append(obj.category)

    return list
