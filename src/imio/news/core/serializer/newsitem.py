from imio.news.core.contents import INewsItem
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.dxcontent import SerializeFolderToJson
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer


@implementer(ISerializeToJson)
@adapter(INewsItem, Interface)
class NewsItemSerializer(SerializeFolderToJson):
    """ """

    def __call__(self, version=None, include_items=True):
        return super(NewsItemSerializer, self).__call__(
            version=version, include_items=True
        )
