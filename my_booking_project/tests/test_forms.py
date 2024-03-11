import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from booking_app.forms import User, ReviewForm


@pytest.mark.django_db
def test_login_or_register(client):
    registration_data = {
        'action': 'register',
        'email': 'newuser@example.com',
        'password1': 'testpassword123',
        'password2': 'testpassword123',
        'company_name': 'Test Company',
        'phone_number': '1234567890',
        'name': 'John',
        'surname': 'Doe',
        'passport_details': '12345678901',
    }
    response = client.post(reverse('login_or_register'), registration_data, follow=True)
    assert response.status_code == 200  # Проверка успешного статуса после регистрации
    assert User.objects.filter(email='newuser@example.com').exists()  # Проверка создания пользователя


@pytest.mark.django_db
def test_login_redirects_to_dashboard(client):
    User = get_user_model()

    # Создание пользователя
    test_email = 'testuser@example.com'
    test_password = 'password123'
    User.objects.create_user(email=test_email, password=test_password, is_guest=False)

    # Попытка входа
    response = client.post(reverse('login_or_register'), {
        'action': 'login',
        'email': test_email,
        'password': test_password,
    }, follow=True)

    # Проверка, что пользователь был аутентифицирован и перенаправлен на нужную страницу
    assert response.status_code == 200  # Проверяем финальный статус после всех перенаправлений
    assert response.context['user'].is_authenticated
    assert '/partner/dashboard/' in [redirect[0] for redirect in response.redirect_chain]


@pytest.mark.django_db
def test_review_form_valid():
    # Создаем словарь с данными, которые имитируют валидный ввод пользователя
    valid_data = {
        'title': 'Отличный отель',
        'review': 'Это был замечательный отдых, спасибо!',
        'rating': '5',
        'user_email': 'user@example.com',
    }

    form = ReviewForm(data=valid_data)

    # Проверяем, что форма валидна
    assert form.is_valid()


@pytest.mark.django_db
def test_review_form_invalid_missing_fields():
    # Создаем данные без обязательного поля 'title'
    invalid_data_missing_title = {
        'review': 'Забыл заголовок, но отель хороший.',
        'rating': '4',
        'user_email': 'user@example.com',
    }

    form_missing_title = ReviewForm(data=invalid_data_missing_title)

    # Проверяем, что форма невалидна
    assert not form_missing_title.is_valid()
    # Проверяем, что ошибка валидации вызвана отсутствием 'title'
    assert 'title' in form_missing_title.errors


@pytest.mark.django_db
def test_review_form_invalid_email():
    # Создаем данные с некорректным форматом электронной почты
    invalid_data_email = {
        'title': 'Проблема с почтой',
        'review': 'Отель был отличный, но ввел неправильную почту.',
        'rating': '5',
        'user_email': 'not_an_email',
    }

    form_invalid_email = ReviewForm(data=invalid_data_email)

    # Проверяем, что форма невалидна
    assert not form_invalid_email.is_valid()
    # Проверяем, что ошибка валидации вызвана некорректным 'user_email'
    assert 'user_email' in form_invalid_email.errors