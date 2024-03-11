from datetime import date, timedelta, datetime, timezone
from decimal import Decimal

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse
from django.contrib.auth import get_user_model
from booking_app.models import Room, Booking, User, MealPlan, Partner, Payment, Commission, Review
from django.core.files.uploadedfile import SimpleUploadedFile

from booking_app.views import calculate_commission


@pytest.mark.django_db
def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'booking_app/index.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_about_page(client):
    response = client.get('/about/')
    assert response.status_code == 200
    assert 'booking_app/about.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_contact_page(client):
    response = client.get('/contact/')
    assert response.status_code == 200
    assert 'booking_app/contact.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_spa_page(client):
    response = client.get('/spa/')
    assert response.status_code == 200
    assert 'booking_app/spa.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_stocks_page(client):
    response = client.get('/stocks/')
    assert response.status_code == 200
    assert 'booking_app/stocks.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_restaurant_page(client):
    response = client.get('/restaurant/')
    assert response.status_code == 200
    assert 'booking_app/restaurant.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_reviews_page(client):
    response = client.get('/reviews/')
    assert response.status_code == 200
    assert 'booking_app/reviews.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_search_rooms(client):
    # Создание мокового изображения
    mock_image = SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg')
    # Подготовка данных
    User = get_user_model()
    user = User.objects.create_user(email='test@example.com', password='password123')
    room1 = Room.objects.create(number='101', category='single', guests=1, price=100, image=mock_image)
    room2 = Room.objects.create(number='102', category='double', guests=2, price=200, image=mock_image)
    room3 = Room.objects.create(number='103', category='single', guests=1, price=150, image=mock_image)
    MealPlan.objects.create(type='breakfast', price=50)
    MealPlan.objects.create(type='half-board', price=100)
    MealPlan.objects.create(type='full-board', price=150)

    # Создаем бронирование, которое перекрывает запрашиваемые даты, для комнаты room1
    booking = Booking.objects.create(
        user=user,
        room_number=room1,
        check_in_date=datetime.today().date(),
        check_out_date=datetime.today().date() + timedelta(days=3),
        total_cost=300,
        is_paid=True,
    )

    # Выполняем GET запрос с параметрами поиска
    checkin_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    checkout_date = (datetime.today() + timedelta(days=2)).strftime('%Y-%m-%d')
    response = client.get(reverse('search_rooms'), {
        'checkin-date': checkin_date,
        'checkout-date': checkout_date,
        'room-type': 'single',
        'adults': '1',
        'children': '0'
    })

    # Проверяем статус ответа и контекст, переданный в шаблон
    assert response.status_code == 200
    rooms_with_meals = response.context['rooms_with_meals']
    # Проверяем, что комната room1 не в списке доступных, так как она забронирована, а room3 доступна
    assert room1 not in [room['room'] for room in rooms_with_meals]
    assert room3 in [room['room'] for room in rooms_with_meals]
    # Проверяем, что комната room2 не возвращается, так как ищем комнаты типа 'single'
    assert room2 not in [room['room'] for room in rooms_with_meals]


@pytest.mark.django_db
def test_successful_booking(client):
    # Подготовка данных
    mock_image = SimpleUploadedFile(name='test_room.jpg', content=b'test_image_content', content_type='image/jpeg')
    room = Room.objects.create(number='101', category='single', guests=1, price=Decimal('100.00'), image=mock_image)
    MealPlan.objects.create(type='breakfast', price=50)

    # Генерируем уникальный email для пользователя
    User = get_user_model()
    user_email = f'user_{datetime.now().strftime("%Y%m%d%H%M%S%f")}@example.com'

    # Параметры для бронирования
    booking_data = {
        'name': 'Test',
        'surname': 'User',
        'email': user_email,
        'passport_details': '1234567890',
        'phone_number': '1234567890',
        'check_in_date': (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'check_out_date': (datetime.today() + timedelta(days=4)).strftime('%Y-%m-%d'),
        'meal_plan': 'breakfast',
    }

    # Выполнение POST запроса для бронирования
    response = client.post(reverse('booking', kwargs={'room_id': room.id}), booking_data, follow=True)
    # Проверка перенаправления на страницу подтверждения оплаты
    assert response.status_code == 200
    assert 'booking' in response.context
    booking = response.context['booking']
    assert booking.user.email == user_email
    assert booking.room_number == room


@pytest.mark.django_db
def test_successful_booking_with_discount(client):
    # Создаем тестовые данные: комнату и план питания
    mock_image = SimpleUploadedFile(name='test_room.jpg', content=b'test_image_content', content_type='image/jpeg')
    room = Room.objects.create(number='101', category='single', guests=1, price=Decimal('200.00'), image=mock_image)
    MealPlan.objects.create(type='breakfast', price=50)

    # Генерируем уникальный email для пользователя
    user_email = f'user_{datetime.now().strftime("%Y%m%d%H%M%S%f")}@example.com'

    # Параметры для бронирования
    booking_data = {
        'name': 'Test',
        'surname': 'User',
        'email': user_email,
        'passport_details': '1234567890',
        'phone_number': '1234567890',
        'check_in_date': (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'check_out_date': (datetime.today() + timedelta(days=3)).strftime('%Y-%m-%d'),
        'meal_plan': 'breakfast',
        'children': '3',  # Добавляем информацию о детях для скидки
    }

    # Предварительная настройка сессии для скидки
    session = client.session
    session['discount'] = {'value': 0.15, 'message': "У Вас скидка 15% по акции 'Большая семья'!", 'children': 5}
    session.save()

    # Выполнение POST запроса для бронирования с follow=True для перехода по redirect
    response = client.post(reverse('booking', kwargs={'room_id': room.id}), booking_data, follow=True)

    # Проверка, что скидка была применена и информация о ней отображается в контексте ответа
    assert response.status_code == 200
    assert 'discount_message' in response.context
    assert response.context['discount_message'] == "У Вас скидка 15% по акции 'Большая семья'!"

    # Проверка, что бронирование было создано с учетом скидки
    booking = Booking.objects.get(user__email=user_email)
    expected_total_cost = Decimal('425.00')  # Исходя из условий скидки
    assert booking.total_cost == expected_total_cost


@pytest.mark.django_db
def test_payment_success(client):
    # Создание необходимых объектов
    user = User.objects.create_user(email='test@example.com', password='password123')
    room = Room.objects.create(number='101', category='single', guests=1, price=100)
    meal_plan = MealPlan.objects.create(type='breakfast', price=50)
    check_in_date = date.today()
    check_out_date = date.today() + timedelta(days=2)
    booking = Booking.objects.create(
        user=user,
        room_number=room,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        total_cost=150,
        is_paid=False,
        meal_plan=meal_plan
    )

    # Выполнение GET запроса на страницу успешной оплаты
    response = client.get(f'/payment_success/{booking.id}/')
    assert response.status_code == 200
    assert 'booking' in response.context
    assert response.context['booking'].id == booking.id


@pytest.mark.django_db
def test_calculate_commission():
    User = get_user_model()
    # Создание пользователя-партнера и партнера
    user = User.objects.create_user(email='partner@example.com', password='testpass123', is_guest=False)
    partner = Partner.objects.create(user=user, company_name='Test Company', phone_number='1234567890')

    # Создание комнаты и тарифного плана
    room = Room.objects.create(number="101", category="single", guests=1, price=Decimal('100.00'))
    meal_plan = MealPlan.objects.create(type='breakfast', price=Decimal('10.00'))

    # Создание бронирования, связанного с партнером
    booking = Booking.objects.create(
        user=user,
        room_number=room,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        total_cost=Decimal('110.00'),
        meal_plan=meal_plan,
        is_paid=True
    )

    # Создание записей о комиссии и платежах, связанных с бронированием
    Commission.objects.create(partner=partner, sales_volume=Decimal('1000.00'), commission_percentage=Decimal('10.00'))
    Payment.objects.create(booking=booking, amount=Decimal('1500.00'), pay_method='Card')

    # Расчет комиссии
    total_sales, commission_percentage, commission_earned = calculate_commission(user)

    assert total_sales == Decimal('1500.00'), "Общий объем продаж должен быть равен 1500.00"
    assert commission_percentage == Decimal('10.00'), "Процент комиссии должен быть равен 10.00"
    assert commission_earned == Decimal('150.00'), "Заработанная комиссия должна быть равна 150.00"


@pytest.mark.django_db
def test_review_successfully_added(client):
    user = User.objects.create_user(email='user@example.com', password='password123')
    # Создание комнаты и тарифного плана
    room = Room.objects.create(number="101", category="single", guests=1, price=Decimal('100.00'))
    meal_plan = MealPlan.objects.create(type='breakfast', price=Decimal('10.00'))
    booking = Booking.objects.create(
        user=user,
        room_number=room,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=1),
        total_cost=Decimal('110.00'),
        meal_plan=meal_plan,
        is_paid=True
    )

    # Данные для отправки через форму
    review_data = {
        'user_email': 'user@example.com',
        'title': 'Отличный отель',
        'review': 'Очень понравилось, обязательно вернусь!',
        'rating': 5
    }

    # URL, по которому доступно представление reviews
    url = reverse('reviews')

    response = client.post(url, review_data, follow=True)

    # Проверяем, статус
    assert response.status_code == 200

    # Проверяем, что отзыв был успешно добавлен в базу данных
    assert Review.objects.filter(title=review_data['title']).exists()

    # Проверяем, что пользователю показывается сообщение об успехе
    messages = [msg.message for msg in get_messages(response.wsgi_request)]
    assert 'Ваш отзыв успешно добавлен.' in messages


@pytest.mark.django_db
def test_booking_from_search_session_and_dates(client):
    today_str = datetime.now().strftime('%Y-%m-%d')
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    url = reverse('booking_from_search')  # Убедитесь, что это правильный путь к вашему представлению
    response = client.get(url, {
        'checkin_date': today_str,
        'checkout_date': tomorrow_str,
        'room_type': 'single',
        'adults': '2',
        'children': '1'
    })

    # Проверка сохранения дат в сессии
    assert response.wsgi_request.session['checkin_date'] == today_str
    assert response.wsgi_request.session['checkout_date'] == tomorrow_str

    # Проверка статуса ответа
    assert response.status_code == 200

    # Проверка отсутствия сообщения об ошибке даты
    assert 'Даты не должны быть раньше сегодняшней.' not in response.content.decode()


@pytest.mark.django_db
def test_booking_search_with_valid_dates(client):
    mock_image = SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg')
    # Предположим, что у нас уже есть зарегистрированный пользователь
    user = User.objects.create_user(email='test@example.com', password='password')
    # Создаем комнату и тарифный план
    room = Room.objects.create(number="101", category="single", guests=2, price=Decimal('100.00'), image=mock_image)
    meal_plan = MealPlan.objects.create(type='breakfast', price=Decimal('10.00'))
    # Задаем даты заезда и выезда
    checkin_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    checkout_date = (datetime.today() + timedelta(days=2)).strftime('%Y-%m-%d')

    # Формируем URL и отправляем GET-запрос
    url = reverse('booking_from_search')
    response = client.get(url, {
        'checkin_date': checkin_date,
        'checkout_date': checkout_date,
        'room_type': 'single',
        'adults': '1',
        'children': '0'
    })

    # Проверяем статус ответа и содержание ответа
    assert response.status_code == 200
    assert 'rooms_with_meals' in response.context  # Убедитесь, что это правильный ключ в вашем контексте
    assert len(response.context['rooms_with_meals']) > 0  # Должны быть доступные номера


@pytest.mark.django_db
def test_booking_search_with_invalid_dates(client):
    # Задаем невалидные даты заезда и выезда (выезд раньше заезда)
    checkin_date = (datetime.today() + timedelta(days=3)).strftime('%Y-%m-%d')
    checkout_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

    url = reverse('booking_from_search')
    response = client.get(url, {
        'checkin_date': checkin_date,
        'checkout_date': checkout_date,
        'room_type': 'double',
        'adults': '1',
        'children': '1'
    })

    # Проверяем статус ответа и наличие сообщения об ошибке
    assert response.status_code == 200
    assert 'error_message' in response.context
    assert 'Дата выезда должна быть позже даты заезда.' == response.context['error_message']


@pytest.mark.django_db
def test_booking_search_exceeding_guests_limit(client):
    # Устанавливаем даты для будущего бронирования
    checkin_date = (datetime.today() + timedelta(days=10)).strftime('%Y-%m-%d')
    checkout_date = (datetime.today() + timedelta(days=12)).strftime('%Y-%m-%d')

    # Пытаемся забронировать одноместную комнату для двух взрослых
    response = client.get(reverse('booking_from_search'), {
        'checkin_date': checkin_date,
        'checkout_date': checkout_date,
        'room_type': 'single',
        'adults': '2',
        'children': '0'
    })

    # Проверяем статус ответа
    assert response.status_code == 200

    # Проверяем наличие сообщения об ошибке о превышении количества гостей
    expected_error_message = f'Превышено максимальное количество гостей для типа single.'
    assert expected_error_message in response.context['error_message']


@pytest.mark.django_db
def test_form_has_csrf_token_reviews(client):
    response = client.get(reverse('reviews'))
    assert 'csrfmiddlewaretoken' in response.content.decode()


@pytest.mark.django_db
def test_form_has_csrf_token_login(client):
    response = client.get(reverse('login_or_register'))
    assert 'csrfmiddlewaretoken' in response.content.decode()


