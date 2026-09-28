import os


def test_history_pagination_reset_in_js():
    js_path = os.path.join("static", "js", "dashboard.js")
    assert os.path.exists(js_path), "dashboard.js must exist"

    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "window.resetHistoryPagination" in content, "resetHistoryPagination function must be defined"
    assert "window.historyState.currentPage = 1" in content, "Pagination reset to page 1 must be implemented"
    assert "historyDocSelect" in content, "historyDocSelect event handler must exist"
