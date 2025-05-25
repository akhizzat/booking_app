import logging
from datetime import datetime, date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.urls import reverse  # добавлено
from django.utils.timezone import now  # добавлено

from rest_framework import routers, viewsets

from .forms import PartnerRegistrationForm, PartnerProfileForm, ReviewForm
from .models import Review, Payment, User, MealPlan, Partner, Commission
from .models import Room, Booking
from .serializer import RoomSerializer, BookingSerializer, PaymentSerializer, ReviewSerializer

from django.db.models import Q, Sum
from django.db.models import Avg

from .forms import UserProfileForm

# Переменная для сегодняшней даты (если используется)
TODAY = now().date()


logger = logging.getLogger(__name__)

# Модель User
User = get_user_model()

MAX_GUESTS_PER_ROOM_TYPE = {
    'single': 1,
    'double': 2,
    'family': 4,
    'luxury': 5,
}

TODAY = date.today()


from .models import MealPlan  # убедись, что импорт есть сверху

def index(request):
    meal_plans = MealPlan.objects.all().order_by('price')
    return render(request, 'booking_app/index.html', {
        'meal_plans': meal_plans
    })


def about(request):
    return render(request, 'booking_app/about.html')


def restaurant(request):
    return render(request, 'booking_app/restaurant.html')


def entertainment(request):
    return render(request, 'booking_app/entertainment.html')


def spa(request):
    return render(request, 'booking_app/spa.html')


def stocks(request):
    return render(request, 'booking_app/stocks.html')


def contact(request):
    return render(request, 'booking_app/contact.html')


# booking_app/views.py
def reviews(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST or None)
        if form.is_valid():
            user_email = form.get_user_email()
            try:
                user = User.objects.get(email=user_email)
                paid_bookings = Booking.objects.filter(user=user, is_paid=True)
                if paid_bookings.exists():
                    review = form.save(commit=False)
                    review.customer = user
                    review.save()
                    messages.success(request, 'Ваш отзыв успешно добавлен.')
                else:
                    messages.error(request, 'Вы не можете оставить отзыв без успешно оплаченного бронирования.')
            except User.DoesNotExist:
                messages.error(request, 'Вы не совершали бронирование, оставить отзыв нельзя.')
            return redirect('reviews')
    else:
        form = ReviewForm()

    # Получение всех отзывов с пользователями
    reviews = Review.objects.all().select_related('customer')

    # Подсчёт среднего рейтинга (округляем до одного знака)
    average_rating = Review.objects.aggregate(avg_rating=Avg('rating'))['avg_rating']
    average_rating = round(average_rating, 1) if average_rating else 0

    # Подготовка звёзд для каждого отзыва
    for review in reviews:
        review.stars_full = range(review.rating)
        review.stars_empty = range(5 - review.rating)

    return render(request, 'booking_app/reviews.html', {
        'form': form,
        'reviews': reviews,
        'average_rating': average_rating,
    })




def rooms(request):
    # Получаем все комнаты из базы данных
    rooms_db = Room.objects.all().order_by('number')

    rooms = [
        {
            'id': room.id,
            'number': room.number,
            'image_url': room.image,
            'type': room.category,
            'price': room.price,
            'description': room.description,

        }
        for room in rooms_db
    ]
    meal_plan = MealPlan.objects.all()

    return render(request, 'booking_app/rooms.html', {'rooms': rooms, 'meal_plan': meal_plan})


# Поиск доступных номеров для неавторизованных пользователей с учетом введенных пользователем критериев поиска
def search_rooms(request):
    checkin_date = request.GET.get('checkin-date')
    checkout_date = request.GET.get('checkout-date')
    room_type = request.GET.get('room-type')
    adults = int(request.GET.get('adults', 0))
    children = int(request.GET.get('children', 0))
    total_guests = adults + children

    if checkin_date and checkout_date:
        checkin_date_parsed = datetime.strptime(checkin_date, '%Y-%m-%d').date()
        checkout_date_parsed = datetime.strptime(checkout_date, '%Y-%m-%d').date()

        # Проверка корректности дат
        if checkout_date_parsed <= checkin_date_parsed:
            return render(request, 'booking_app/index.html', {
                'error_message': 'Дата выезда должна быть позже даты заезда.'
            })

        if TODAY > checkout_date_parsed or TODAY > checkin_date_parsed:
            return render(request, 'booking_app/index.html', {
                'error_message': 'Даты не должны быть раньше сегодняшней.'
            })

        if room_type in MAX_GUESTS_PER_ROOM_TYPE and total_guests > MAX_GUESTS_PER_ROOM_TYPE[room_type]:
            return render(request, 'booking_app/index.html', {
                'error_message': f'Превышено максимальное количество гостей для типа {room_type}.',
            })

    # Скидка за 3+ детей
    discount = Decimal('0.15') if children >= 3 else Decimal('0')
    discount_message = "У Вас скидка 15% по акции 'Большая семья'!" if discount > 0 else None

    booked_rooms = Booking.objects.filter(
        Q(check_in_date__lte=checkout_date, check_out_date__gte=checkin_date),
        is_paid=True
    ).values_list('room_number', flat=True)

    available_rooms = Room.objects.exclude(
        number__in=booked_rooms
    ).filter(
        category=room_type if room_type else None,
        guests__gte=total_guests
    ).order_by('number')

    meal_plans = MealPlan.objects.all().order_by('price')
    rooms_with_meals = []

    for room in available_rooms:
        room_meals = {}  # ключ: meal_plan.type, значение: {'name': ..., 'price': ...}
        for meal_plan in meal_plans:
            original_price = room.calculate_total_price(meal_plan.type)
            discounted_price = original_price - (original_price * discount) if discount > 0 else original_price
            room_meals[meal_plan.type] = {
            'name': meal_plan.get_type_display(),  # ✅ правильно: достаёт 'Завтрак', 'Всё включено' и т.д.
            'price': round(discounted_price, 2)
        }
        rooms_with_meals.append({
            'room': room,
            'meals': room_meals
        })

    context = {
    'rooms_with_meals': rooms_with_meals,
    'discount_message': discount_message,
    'showing_alternatives': False,
}


    request.session['discount'] = {
        'value': float(discount),
        'message': discount_message,
        'children': children
    }
    request.session.modified = True

    return render(request, 'booking_app/search_rooms.html', context)


# Бронирование номера для неавторизованного пользователя
def booking(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    meal_plans = MealPlan.objects.all().order_by('price')

    error_message = None
    discount_info = request.session.get('discount', {'value': 0, 'message': None, 'children': 0})
    discount = Decimal(discount_info['value'])
    children = discount_info['children']

    # Получаем или сохраняем даты в сессии
    check_in_date = request.GET.get('check_in_date') or request.session.get('check_in_date')
    check_out_date = request.GET.get('check_out_date') or request.session.get('check_out_date')

    # Сохраняем их в сессии
    if check_in_date and check_out_date:
        request.session['check_in_date'] = check_in_date
        request.session['check_out_date'] = check_out_date

    if request.method == 'POST':
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        email = request.POST.get('email')
        passport_details = request.POST.get('passport_details')
        phone_number = request.POST.get('phone_number')
        check_in_date = request.POST.get('check_in_date')
        check_out_date = request.POST.get('check_out_date')
        meal_plan_type = request.POST.get('meal_plan')

        try:
            check_in = datetime.strptime(check_in_date, "%Y-%m-%d").date()
            check_out = datetime.strptime(check_out_date, "%Y-%m-%d").date()
        except ValueError:
            return render(request, 'booking_app/booking.html', {
                'room': room,
                'meal_plans': meal_plans,
                'error_message': 'Неверный формат даты.',
                'selected_meal': meal_plan_type,
                'check_in_date': check_in_date,
                'check_out_date': check_out_date
            })

        if check_in >= check_out:
            error_message = 'Дата выезда должна быть позже даты заезда.'
        else:
            try:
                meal_plan = MealPlan.objects.get(type=meal_plan_type)
            except MealPlan.DoesNotExist:
                error_message = 'Выбранный тип питания недоступен.'
                meal_plan = None

        if not error_message and meal_plan:
            # ⛔ Проверка — существует ли пользователь и прошёл ли он регистрацию
            try:
                user = User.objects.get(email=email)
                if user.is_guest:
                    error_message = (
                        "Для бронирования необходимо зарегистрироваться. "
                        f"Пожалуйста, <a href='{reverse('login_or_register')}'>перейдите на страницу регистрации</a>."
                    )
            except User.DoesNotExist:
                error_message = (
                    "Такой email не зарегистрирован. "
                    f"Пожалуйста, <a href='{reverse('login_or_register')}'>создайте аккаунт</a>, чтобы продолжить бронирование."
                )

        if not error_message and meal_plan:
            if Booking.objects.filter(
                room_number=room,
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
                is_paid=True
            ).exists():
                error_message = 'Выбранный номер недоступен на указанные даты.'
            else:
                total_days = (check_out - check_in).days
                total_cost = room.calculate_total_price(meal_plan.type) * total_days

                if children >= 3:
                    total_cost -= total_cost * discount
                    total_cost = round(total_cost, 2)

                booking = Booking.objects.create(
                    user=user,
                    room_number=room,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    total_cost=total_cost,
                    meal_plan=meal_plan,
                    is_paid=False
                )

                request.session['booking_info'] = {
                    'booking_id': booking.id,
                    'discount_message': discount_info['message'],
                    'total_cost': str(total_cost)
                }
                request.session.modified = True
                return redirect('payment_confirmation')

    return render(request, 'booking_app/booking.html', {
        'room': room,
        'meal_plans': meal_plans,
        'error_message': error_message,
        'selected_meal': request.GET.get('meal_plan'),
        'check_in_date': check_in_date,
        'check_out_date': check_out_date
    })

# Авторизация или регистрация для Партнера
def login_or_register(request):
    context = {'registration_form': PartnerRegistrationForm()}

    if request.method == 'POST':
        action = request.POST.get('action')  # Определение действия 'login' или 'register'

        if action == 'login':
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, username=email, password=password)  # Аутентификация пользователя
            if user is not None and not user.is_guest:
                login(request, user)  # Вход пользователя в систему
                return redirect('partner_dashboard')
            else:
                context[
                    'login_error'] = "Неверный логин или пароль, либо учетная запись не предназначена для доступа к партнерскому кабинету."

        elif action == 'register':
            form = PartnerRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_guest = False
                user.save()
                form.save_m2m()  # Сохраняем ManyToMany данные, если есть (groups, user_permissions), но пока не используются
                Partner.objects.create(user=user, company_name=form.cleaned_data['company_name'],
                                       phone_number=form.cleaned_data['phone_number'])
                login(request, user)
                return redirect('partner_dashboard')
            else:
                context['registration_form'] = form  # Чтобы не вводить все данные заново при ошибке
                context['registration_error'] = "Ошибка при заполнении формы регистрации."

    return render(request, 'booking_app/login_or_register.html', context)


# Отображение личного кабинета Партнера
@login_required
def partner_dashboard(request):
    if not request.user.is_partner:
        messages.error(request, 'Доступ разрешен только для партнеров.')
        return redirect('home')

    total_sales, commission_percentage, commission_earned = calculate_commission(request.user)
    bookings = Booking.objects.filter(user__partner=request.user.partner)

    context = {
        'bookings': bookings,
        'total_sales': total_sales,
        'commission_percentage': commission_percentage,
        'commission_earned': commission_earned,
    }

    return render(request, 'booking_app/partner_dashboard.html', context)


# Отображение всех бронирований Партнера
@login_required
def booking_by_partner(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'booking_app/booking_by_partner.html', {'bookings': bookings})


# Редактирование профиля Партнера
@login_required
def edit_partner_profile(request):
    if request.method == 'POST':
        form = PartnerProfileForm(request.POST, instance=request.user.partner)
        if form.is_valid():
            form.save()
            # Перенаправление на страницу панели управления партнера после успешного сохранения
            return redirect('partner_dashboard')
    else:
        # Инициализация формы данными из объекта партнера, связанного с текущим пользователем
        form = PartnerProfileForm(instance=request.user.partner)

    # Отрисовка страницы редактирования с формой
    return render(request, 'booking_app/edit_partner_profile.html', {'form': form})


# Форма поиска номеров для Партнеров
def search_rooms_partner(request):
    return render(request, 'booking_app/search_rooms_partner.html')


def booking_from_search(request):
    # Проверка: показать альтернативы?
    if request.GET.get("alternative") == "1":
        checkin_date = request.session.get('checkin_date')
        checkout_date = request.session.get('checkout_date')

        meal_plans = MealPlan.objects.all().order_by('price')

        if checkin_date and checkout_date:
            checkin_date = datetime.strptime(checkin_date, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout_date, '%Y-%m-%d').date()

            booked_rooms = Booking.objects.filter(
                Q(check_in_date__lte=checkout_date),
                Q(check_out_date__gte=checkin_date),
                is_paid=True
            ).values_list('room_number', flat=True)

            alternative_rooms = Room.objects.exclude(number__in=booked_rooms).order_by('number')
        else:
            alternative_rooms = Room.objects.all().order_by('number')

        alternative_with_meals = []
        for room in alternative_rooms:
            meal_prices = {}
            for plan in meal_plans:
                meal_prices[plan.type] = round(room.calculate_total_price(plan.type), 2)
            alternative_with_meals.append({
                'room': room,
                'meals': meal_prices
            })

        return render(request, 'booking_app/booking_from_search.html', {
            'rooms_with_meals': [],
            'alternative_rooms_with_meals': alternative_with_meals,
            'showing_alternatives': True,
            'meal_plans': meal_plans,
        })

    # Получаем и сохраняем даты в сессии
    request.session['checkin_date'] = request.GET.get('checkin_date')
    request.session['checkout_date'] = request.GET.get('checkout_date')
    request.session['adults'] = int(request.GET.get('adults', '1'))
    request.session['children'] = int(request.GET.get('children', '0'))

    room_type = request.GET.get('room_type')
    checkin_date = request.session.get('checkin_date')
    checkout_date = request.session.get('checkout_date')
    children = request.session.get('children')
    total_guests = request.session['adults'] + request.session['children']

    if checkin_date and checkout_date:
        checkin_date_parsed = datetime.strptime(checkin_date, '%Y-%m-%d').date()
        checkout_date_parsed = datetime.strptime(checkout_date, '%Y-%m-%d').date()

        if checkout_date_parsed <= checkin_date_parsed:
            return render(request, 'booking_app/search_rooms_partner.html', {
                'error_message': 'Дата выезда должна быть позже даты заезда.',
            })

        if TODAY > checkout_date_parsed or TODAY > checkin_date_parsed:
            return render(request, 'booking_app/search_rooms_partner.html', {
                'error_message': 'Даты не должны быть раньше сегодняшней.'
            })

    if room_type in MAX_GUESTS_PER_ROOM_TYPE and total_guests > MAX_GUESTS_PER_ROOM_TYPE[room_type]:
        return render(request, 'booking_app/search_rooms_partner.html', {
            'error_message': f'Превышено максимальное количество гостей для типа {room_type}.',
        })

    discount = Decimal('0.15') if children >= 3 else Decimal('0')
    discount_message = "У Вас скидка 15% по акции 'Большая семья'!" if discount > 0 else None

    booked_rooms = Booking.objects.filter(
        Q(check_in_date__lte=checkout_date, check_out_date__gte=checkin_date),
        is_paid=True
    ).values_list('room_number', flat=True)

    available_rooms = Room.objects.exclude(
        number__in=booked_rooms
    ).filter(
        category=room_type if room_type else None,
        guests__gte=total_guests
    ).order_by('number')

    meal_plans = MealPlan.objects.all().order_by('price')
    rooms_with_meals = []

    for room in available_rooms:
        room_meals = {}
        for meal_plan in meal_plans:
            original_price = room.calculate_total_price(meal_plan.type)
            discounted_price = original_price - (original_price * discount) if discount > 0 else original_price
            room_meals[meal_plan.type] = round(discounted_price, 2)
        rooms_with_meals.append({
            'room': room,
            'meals': room_meals
        })

    context = {
        'rooms_with_meals': rooms_with_meals,
        'discount_message': discount_message,
        'showing_alternatives': False,
    }

    request.session['discount'] = {
        'value': float(discount),
        'message': discount_message,
        'children': children
    }
    request.session.modified = True

    return render(request, 'booking_app/booking_from_search.html', context)

#  Создание бронирования для Партнеров и перенаправление  на страницу подтверждения оплаты
@login_required
def create_booking_and_redirect_to_payment(request):
    discount_info = request.session.get('discount', {'value': 0, 'message': None, 'children': 0})
    discount = Decimal(discount_info['value'])
    # Получение количества детей из сессии
    children = discount_info['children']

    try:
        room_id = request.GET.get('room_id')
        check_in_date = request.GET.get('check_in_date')
        check_out_date = request.GET.get('check_out_date')
        meal_plan_type = request.GET.get('meal_plan')
        total_guests = int(request.GET.get('children', 0)) + int(request.GET.get('adults', 0))

        # Преобразование строк дат в объекты даты
        check_in_date_parsed = datetime.strptime(check_in_date, '%Y-%m-%d').date() if check_in_date else None
        check_out_date_parsed = datetime.strptime(check_out_date, '%Y-%m-%d').date() if check_out_date else None

        if not all([check_in_date_parsed, check_out_date_parsed, room_id, meal_plan_type]):
            # Возвращаем ошибку, если один из параметров отсутствует
            return render(request, 'booking_app/error.html', {'error_message': 'Все поля должны быть заполнены.'})

        # Проверка корректности дат
        if check_out_date_parsed <= check_in_date_parsed:
            return render(request, 'booking_app/error.html',
                          {'error_message': 'Дата выезда должна быть позже даты заезда.'})

        room = get_object_or_404(Room, pk=room_id)

        # Проверка на максимальное количество гостей для выбранного типа комнаты
        room_type = room.category
        if total_guests > MAX_GUESTS_PER_ROOM_TYPE[room_type]:
            return render(request, 'booking_app/error.html',
                          {'error_message': f'Превышено максимальное количество гостей для типа {room_type}.'})

        meal_plan = get_object_or_404(MealPlan, type=meal_plan_type)
        room = get_object_or_404(Room, pk=room_id)
        total_days = (check_out_date_parsed - check_in_date_parsed).days
        total_cost = room.calculate_total_price(meal_plan.type) * total_days

        # Применяем скидку, если количество детей 3 и более
        if children >= 3:
            total_cost -= total_cost * discount
            total_cost = round(total_cost, 2)

        # Создание объекта бронирования
        booking = Booking.objects.create(
            user=request.user,
            room_number=room,
            check_in_date=check_in_date_parsed,
            check_out_date=check_out_date_parsed,
            meal_plan=meal_plan,
            total_cost=total_cost,
            is_paid=False
        )
        request.session['booking_info'] = {
            'booking_id': booking.id,
            'discount_message': discount_info['message'],
            'total_cost': str(total_cost)
        }

        # Перенаправление на страницу подтверждения оплаты
        return redirect('payment_confirmation')
    except Exception as e:
        # Обработка ошибок и перенаправление на страницу с ошибкой
        return render(request, 'booking_app/error.html', {'error_message': str(e)})


# Подтверждение оплаты бронирования
def payment_confirmation(request):
    booking_info = request.session.get('booking_info', {})
    if not booking_info:
        # Обработка случая, когда информация о бронировании отсутствует в сессии
        return HttpResponse("Ошибка: Нет данных о бронировании.", status=400)

    booking_id = booking_info.get('booking_id')
    total_cost = booking_info.get('total_cost')
    discount_message = booking_info.get('discount_message', None)
    # Получение объекта модели Booking из базы данных по его идентификатору id
    booking = get_object_or_404(Booking,
                                id=booking_id)

    context = {
        'booking': booking,
        'booking_id': booking_id,
        'total_cost': total_cost,
        'discount_message': discount_message,
    }
    return render(request, 'booking_app/payment_confirmation.html', context)


# Обработка логики оплаты бронирования
@require_POST
def process_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking_info = request.session.get('booking_info', {})
    discount_message = booking_info.get('discount_message', None)
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        # Создание записи об оплате
        Payment.objects.create(
            booking=booking,
            amount=booking.total_cost,
            pay_method=payment_method
        )

        # Обновление статуса бронирования как оплаченного
        booking.is_paid = True
        booking.save()

        # Сохранение информации о бронировании в сессии (в JSON) для последующего использования (если необходимо)
        request.session['booking_info'] = {
            'booking_id': booking.id,
            'room_number': booking.room_number.number,
            'check_in_date': booking.check_in_date.strftime("%Y-%m-%d"),  # Форматируем дату для хранения в сессии
            'check_out_date': booking.check_out_date.strftime("%Y-%m-%d"),
            'total_nights': (booking.check_out_date - booking.check_in_date).days,
            'total_cost': str(booking.total_cost),  # Преобразуем Decimal в строку для хранения в сессии
            'meal_plan': str(booking.meal_plan),
            'discount_message': discount_message,

        }

        # Перенаправление на страницу успешной оплаты
        return redirect('payment_success', booking_id=booking_id)
    else:
        logger.error(f"Недопустимый тип запроса: {request.method} для process_payment для бронирования ID {booking_id}")
        raise SuspiciousOperation("Ожидался POST-запрос")


# Отображение страницы успешной оплаты бронирования
def payment_success(request, booking_id):
    # Получаем объект бронирования по переданному id
    booking = get_object_or_404(Booking, pk=booking_id)
    booking_info = request.session.get('booking_info', {})

    # Проверяем, есть ли информация о скидке в сессии
    discount_message = booking_info.get('discount_message', None)
    return render(request, 'booking_app/payment_success.html', {
        'booking': booking,
        'discount_message': discount_message
    })


# Расчета комиссии, которую заработал Партнер на основе его общего объема продаж
def calculate_commission(user):
    if not user.is_partner:
        return 0, 0, 0  # Возвращаем 0 для всех значений, если пользователь не является Партнером
    partner = user.partner
    #  Расчет общего объема продаж для конкретного Партнера
    total_sales = Payment.objects.filter(
        booking__user__partner=partner).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    # Поиск в модели Commission, чтобы найти соответствующую запись комиссии для определенного
    # Партнера на основе общего объема продаж
    commission_rate = Commission.objects.filter(
        partner=partner,
        sales_volume__lte=total_sales).order_by('-sales_volume').first()

    if commission_rate:
        # Вычисляет комиссию, которую заработал Партнер
        commission_earned = total_sales * commission_rate.commission_percentage / 100
        # Процентная ставка комиссии
        commission_percentage = commission_rate.commission_percentage
    else:
        commission_earned = 0
        commission_percentage = 0

    return total_sales, commission_percentage, commission_earned


# -------------api--------------------#

from drf_multiple_model.viewsets import ObjectMultipleModelAPIViewSet


# class BookingAPIView(ObjectMultipleModelAPIViewSet):
#     querylist = [
#         {'queryset': Room.objects.all(), 'serializer_class': RoomSerializer},
#         {'queryset': Booking.objects.all(), 'serializer_class': BookingSerializer},
#         {'queryset': Review.objects.all(), 'serializer_class': ReviewSerializer},
#         {'queryset': Payment.objects.all(), 'serializer_class': PaymentSerializer},
#     ]
#
#
# router = routers.DefaultRouter()
# router.register('api', BookingAPIView, basename='api')

class BookingAPIView(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class RoomAPIView(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class ReviewAPIView(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class PaymentAPIView(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


router = routers.DefaultRouter()

# router.register('api', BookingAPIView, basename='api')

router.register('api/booking', BookingAPIView, basename='api_booking')
router.register('api/room', RoomAPIView, basename='api_room')
router.register('api/review', ReviewAPIView, basename='api_review')
router.register('api/payment', PaymentAPIView, basename='api_payment')

from django.contrib.auth.decorators import login_required
from .forms import ReviewForm

@login_required
def leave_review(request):
    if request.method == "POST":
        form = ReviewForm(request.POST, show_email=True)
        if form.is_valid():
            review = form.save(commit=False)
            review.customer = request.user
            review.save()
            messages.success(request, "Спасибо за ваш отзыв!")
            return redirect('reviews')
    else:
        form = ReviewForm()
    return render(request, 'booking_app/leave_review.html', {'form': form})

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'booking_app/profile.html', {'form': form, 'user': user})