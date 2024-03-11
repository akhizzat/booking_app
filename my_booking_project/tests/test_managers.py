import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(email='user@example.com', password='testpass123')
    assert User.objects.filter(email='user@example.com').exists()
    assert user.email == 'user@example.com'


@pytest.mark.django_db
def test_create_user_without_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email='', password='testpass123')


@pytest.mark.django_db
def test_create_superuser():
    admin_user = User.objects.create_superuser(email='admin@example.com', password='testpass123')
    assert admin_user.is_superuser is True
    assert admin_user.is_staff is True
    assert User.objects.filter(email='admin@example.com').exists()


@pytest.mark.django_db
def test_create_superuser_with_wrong_flags():
    with pytest.raises(ValueError):
        User.objects.create_superuser(email='admin2@example.com', password='testpass123', is_staff=False)
    with pytest.raises(ValueError):
        User.objects.create_superuser(email='admin3@example.com', password='testpass123', is_superuser=False)
