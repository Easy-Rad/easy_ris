import pytest


@pytest.mark.django_db
def test_index_page_has_login_and_search_buttons(django_app):
    response = django_app.get("/")
    assert "login" in response.text.lower()
    assert "search" in response.text.lower()
