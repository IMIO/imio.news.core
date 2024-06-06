# -*- coding: utf-8 -*-

from imio.news.core.viewlets.news import (
    user_is_contributor_in_entity_which_authorize_to_bring_news,
)
from imio.smartweb.common.utils import get_vocabulary
from imio.smartweb.common.widgets.select import TranslatedAjaxSelectWidget
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from zope import schema
from z3c.form import button
from z3c.form import form
from z3c.form.button import buttonAndHandler
from plone.supermodel import model


class IBringNewsIntoNewsFoldersForm(model.Schema):
    """ """

    directives.widget(
        "news_folders",
        TranslatedAjaxSelectWidget,
        vocabulary="imio.news.vocabulary.UserNewsFolders",
        pattern_options={"multiple": True},
    )
    directives.write_permission(news_folders="cmf.SetOwnProperties")
    news_folders = schema.List(
        title=_("Available news folders"),
        value_type=schema.Choice(source="imio.news.vocabulary.UserNewsFolders"),
        required=True,
    )


class BringNewsIntoNewsFoldersForm(AutoExtensibleForm, form.Form):
    """ """

    schema = IBringNewsIntoNewsFoldersForm
    ignoreContext = True
    enable_autofocus = False
    label = _("Add/Remove news folder(s)")

    def update(self):
        super(BringNewsIntoNewsFoldersForm, self).update()
        if user_is_contributor_in_entity_which_authorize_to_bring_news is False:
            api.portal.show_message(
                _("You don't have rights to access this page."), self.request
            )
            self.request.response.redirect(self.context.absolute_url())
            return False

    def updateWidgets(self):
        super(BringNewsIntoNewsFoldersForm, self).updateWidgets()
        selectedItems = {}
        self.selectedUID = []
        vocabulary = get_vocabulary("imio.news.vocabulary.UserNewsFolders")

        for term in vocabulary:
            if term.value in self.context.selected_news_folders:
                self.selectedUID.append(term.value)
                selectedItems[term.value] = term.title
        self.widgets["news_folders"].value = ";".join(self.selectedUID)

    @buttonAndHandler(_("Submit"))
    def handle_submit(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        if len(data.get("news_folders")) < len(self.selectedUID):
            # we want to remove news folder(s) out of this event
            news_folders_to_remove = list(
                set(self.selectedUID) - set(data.get("news_folders"))
            )
            for news_folder in news_folders_to_remove:
                self.context.selected_news_folders.remove(news_folder)
            success_message = _("News folder(s) correctly removed.")
        else:
            # we want to add an news folder in this event
            for news_folder in data.get("news_folders"):
                if news_folder not in self.context.selected_news_folders:
                    self.context.selected_news_folders.append(news_folder)
            success_message = _("News folder(s) correctly added.")

        self.context.reindexObject()
        self.status = success_message
        api.portal.show_message(_(self.status), self.request)

        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(_("Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())
