# -*- coding: utf-8 -*-
from contextlib import contextmanager
from unittest.mock import patch

import os


def make_named_image(filename="plone.png"):
    path = os.path.join(os.path.dirname(__file__), f"resources/{filename}")
    with open(path, "rb") as f:
        image_data = f.read()
    return {"filename": filename, "data": image_data}


@contextmanager
def mock_odwb(ok_response='{"ok": true}'):
    with patch(
        "imio.smartweb.common.rest.odwb.OdwbBaseEndpointGet.odwb_query",
        return_value=ok_response,
    ) as mocked:
        yield mocked
