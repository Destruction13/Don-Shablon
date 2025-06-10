import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.user_templates import UserTemplates


def test_add_and_remove(tmp_path):
    path = tmp_path / "t.json"
    ut = UserTemplates(path)
    ut.add_template("tag", "text")
    assert {"tag": "tag", "text": "text"} in ut.templates
    ut.remove_template(0)
    assert ut.templates == []


def test_filter_layout(tmp_path):
    path = tmp_path / "t.json"
    data = [{"tag": "Встреча", "text": "x"}]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    ut = UserTemplates(path)
    assert ut.filter_by_tag("dcnhtxf") == data
