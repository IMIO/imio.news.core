# -*- coding: utf-8 -*-
from imio.smartweb.common.utils import get_vocabulary
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.app.z3cform.widget import AjaxSelectFieldWidget
from zope import schema
from z3c.form import button
from z3c.form import form
from z3c.form.button import buttonAndHandler
from plone.supermodel import model

import transaction


class IBringNewsIntoNewsFoldersForm(model.Schema):
    """ """

    directives.widget(
        "news_folders",
        AjaxSelectFieldWidget,
        source="imio.news.vocabulary.UserNewsFolders",
        pattern_options={"multiple": True},
    )
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

    def updateWidgets(self):
        news_folders_to_display = []
        vocabulary = get_vocabulary("imio.news.vocabulary.UserNewsFolders")
        # Loop to display only news folders where user has the permission (ex : to remove these news folders out of news)
        for news_folder_uid in self.context.selected_news_folders:
            if vocabulary.by_token.get(news_folder_uid) is None:
                # user can't remove this news folders because he has no permission on it so we don't display it
                pass
            news_folders_to_display.append(news_folder_uid)
        self.fields["news_folders"].field.default = news_folders_to_display
        super(BringNewsIntoNewsFoldersForm, self).updateWidgets()

    @buttonAndHandler(_("Submit"))
    def handle_submit(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        if len(data.get("news_folders")) < len(
            self.fields["news_folders"].field.default
        ):
            # we want to remove news folder(s) out of this news
            news_folders_to_remove = list(
                set(self.fields["news_folders"].field.default)
                - set(data.get("news_folders"))
            )
            for news_folder in news_folders_to_remove:
                self.context.selected_news_folders.remove(news_folder)
            success_message = _("News folder(s) correctly removed.")
        else:
            # we want to add news folder(s) in this news
            for new_news_folder in data.get("news_folders"):
                if new_news_folder not in self.context.selected_news_folders:
                    self.context.selected_news_folders.append(new_news_folder)
            success_message = _("News folder(s) correctly added.")
        self.context.reindexObject(idxs=["selected_news_folders"])
        transaction.commit()
        self.status = success_message
        api.portal.show_message(_(self.status), self.request)
        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(_("Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())
