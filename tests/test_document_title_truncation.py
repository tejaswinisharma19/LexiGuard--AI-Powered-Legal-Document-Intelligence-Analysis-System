import os


def test_document_title_truncation_css_rules():
    css_path = os.path.join("static", "css", "legal_tech.css")
    assert os.path.exists(css_path), "legal_tech.css must exist"

    with open(css_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "text-overflow: ellipsis" in content, "text-overflow: ellipsis must be present in CSS"
    assert "overflow: hidden" in content, "overflow: hidden must be present in CSS"
    assert "white-space: nowrap" in content, "white-space: nowrap must be present in CSS"


def test_document_select_option_title_attributes():
    js_path = os.path.join("static", "js", "dashboard.js")
    assert os.path.exists(js_path), "dashboard.js must exist"

    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'title="' in content and 'aria-label="' in content, "Option elements must include title and aria-label attributes for long titles"
