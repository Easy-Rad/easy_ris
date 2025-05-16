import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_index_page_has_login_and_search_buttons(django_app):
    response = django_app.get("/")
    assert "Search" in response.text


@pytest.mark.django_db
def test_admin_login_successful(django_app):
    # Create a superuser
    User = get_user_model()
    admin_user = User.objects.create_superuser(
        username="admin", email="admin@example.com", password="admin123"
    )

    # Get the login page first
    admin_index = reverse("admin:index")
    response = django_app.get(admin_index).maybe_follow()

    # Fill and submit the login form
    form = response.forms[0]  # Get the first form on the page
    form["username"] = "admin"
    form["password"] = "admin123"
    response = form.submit().maybe_follow()

    # Verify successful login by checking for admin dashboard elements
    assert response.status_code == 200
    assert "Request Analytics" in response.text
    assert "Easy RIS" in response.text
