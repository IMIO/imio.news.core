from imio.smartweb.common.ia.browser.views import BaseProcessCategorizeContentView

import json


class ProcessCategorizeContentView(BaseProcessCategorizeContentView):

    def _get_all_text(self):
        all_text = ""
        raw = self.request.get("BODY")
        data = json.loads(raw)
        event_title = data.get("formdata").get("form-widgets-IIASmartTitle-title", "")
        event_richtext = data.get("formdata").get(
            "form-widgets-IRichTextBehavior-text", ""
        )
        all_text = f"{event_title} {event_richtext}"
        return all_text.strip()

    def _process_specific(self, all_text, results):
        """Must be impleted"""
        ia_category = self._process_category(all_text, results)
        results["form-widgets-category"] = ia_category

        ia_local_category = self._process_local_category(all_text, results)
        results["form-widgets-local_category"] = ia_local_category

        return results

    def _process_category(self, all_text, results):
        category_voc = self._get_structured_data_from_vocabulary(
            "imio.news.vocabulary.NewsCategories"
        )
        data = self._ask_categorization_to_ia(all_text, category_voc)
        if not data:
            return
        ia_categories = [
            {"title": r.get("title"), "token": r.get("token")}
            for r in data.get("result", [])
        ]
        return ia_categories

    def _process_local_category(self, all_text, results):
        category_voc = self._get_structured_data_from_vocabulary(
            "imio.news.vocabulary.NewsLocalCategories", self.context
        )
        data = self._ask_categorization_to_ia(all_text, category_voc)
        if not data:
            return
        ia_categories = [
            {"title": r.get("title"), "token": r.get("token")}
            for r in data.get("result", [])
        ]
        return ia_categories
