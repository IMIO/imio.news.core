from imio.news.core.contents import IFolder
from imio.news.core.contents import INewsFolder
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.app.content.browser.actions import (
    DeleteConfirmationForm as BaseDeleteConfirmationForm,
)
from plone.app.content.browser.contents.delete import (
    DeleteActionView as BaseDeleteActionView,
)
from zope.i18n import translate


class DeleteConfirmationForm(BaseDeleteConfirmationForm):

    @property
    def items_to_delete(self):
        """Delete from action in left menu"""

        obj = self.context
        count = len(obj.items())
        if not INewsFolder.providedBy(obj) and not IFolder.providedBy(obj):
            return count
        if count >= 1:
            container_to_delete = (
                _("News folder") if INewsFolder.providedBy(obj) else _("Folder")
            )
            txt = _(
                "${val1} ${val2} can't be removed because it contains ${val3} element(s)",
                mapping={
                    "val1": container_to_delete,
                    "val2": obj.Title(),
                    "val3": count,
                },
            )
            msg = translate(txt, context=self.request)
            api.portal.show_message(msg, self.request, type="warn")
            self.request.response.redirect(obj.absolute_url())
            return 0
        return count


class DeleteActionView(BaseDeleteActionView):

    def action(self, obj):
        """Delete from trash icon in folder_contents view"""

        if not INewsFolder.providedBy(obj) and not IFolder.providedBy(obj):
            return super(DeleteActionView, self).action(obj)
        else:
            count = len(obj.items())
            if count >= 1:
                container_to_delete = (
                    _("News folder") if INewsFolder.providedBy(obj) else _("Folder")
                )
                txt = _(
                    "${val1} ${val2} can't be removed because it contains ${val3} element(s)",
                    mapping={
                        "val1": container_to_delete,
                        "val2": obj.Title(),
                        "val3": count,
                    },
                )
                msg = translate(txt, context=self.request)
                self.errors.append(msg)
                return
            return super(DeleteActionView, self).action(obj)
