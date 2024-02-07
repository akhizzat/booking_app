import logging
from datetime import datetime


from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect

from django.views.decorators.http import require_POST
from rest_framework import routers

from rest_framework import routers, viewsets

from .models import Review, Payment, User

from .serializer import RoomSerializer, BookingSerializer, PaymentSerializer, ReviewSerializer, AllSerializer



from .models import Room, Booking
from django.db.models import Q

logger = logging.getLogger(__name__)

MAX_GUESTS_PER_ROOM_TYPE = {
    'single': 1,
    'double': 2,
    'family': 4,
    'luxury': 5,
}


def index(request):
    return render(request, 'booking_app/index.html')


def about(request):
    return HttpResponse('О нас')


def payment_success(request, booking_id):
    # Получаем объект бронирования по переданному ID
    booking = get_object_or_404(Booking, pk=booking_id)
    # Отрисовываем шаблон, передавая в него объект бронирования
    return render(request, 'booking_app/payment_success.html', {'booking': booking})


def rooms(request):
    # Получаем все комнаты из базы данных
    rooms_db = Room.objects.all()

    rooms = [
        {
            'id': room.id,  # Идентификатор комнаты
            'number': room.number,
            'image_url': room.image,  # Путь к изображению комнаты
            'type': room.category,  # Получаем отображаемое имя категории
            'price': room.price,  # Цена
            'available': room.available  # Доступность

        }
        for room in rooms_db
    ]
    return render(request, 'booking_app/rooms.html', {'rooms': rooms})


def search_rooms(request):
    checkin_date = request.GET.get('checkin-date')
    checkout_date = request.GET.get('checkout-date')
    room_type = request.GET.get('room-type')
    guests = int(request.GET.get('guests', 0))  # Преобразование в число, 0 по умолчанию

    # Проверка корректности дат
    if checkin_date and checkout_date:
        checkin_date_parsed = datetime.strptime(checkin_date, '%Y-%m-%d').date()
        checkout_date_parsed = datetime.strptime(checkout_date, '%Y-%m-%d').date()
        if checkout_date_parsed <= checkin_date_parsed:
            context = {
                'error_message': 'Дата выезда должна быть позже даты заезда.',
            }

            return render(request, 'booking_app/index.html', context)

    # Проверка на максимальное количество гостей для выбранного типа комнаты
    if room_type in MAX_GUESTS_PER_ROOM_TYPE and guests > MAX_GUESTS_PER_ROOM_TYPE[room_type]:
        # Если есть ошибка, добавляем сообщение об ошибке в контекст шаблона
        context = {
            'error_message': f'Превышено максимальное количество гостей для типа {room_type}.',
        }

        return render(request, 'booking_app/index.html', context)

    # Фильтрация доступных номеров по дате и оплате
    booked_rooms = Booking.objects.filter(
        Q(check_in_date__lte=checkout_date, check_out_date__gte=checkin_date),
        is_paid=True
    ).values_list('room_number', flat=True)

    available_rooms_query = Room.objects.exclude(
        number__in=booked_rooms
    ).filter(
        available=True,
        category=room_type if room_type else Room.objects.none(),
        guests__gte=guests
    )

    available_rooms = available_rooms_query.all()

    return render(request, 'booking_app/search.html', {'rooms': available_rooms})


def booking(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if request.method == 'POST':
        # Извлекаем данные формы
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        age = request.POST.get('age')
        phone = request.POST.get('phone')
        check_in_date = request.POST.get('check_in_date')
        check_out_date = request.POST.get('check_out_date')

        # Конвертация дат
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d").date()
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d").date()

        # Проверка корректности дат
        if check_in >= check_out:
            return render(request, 'booking_app/booking.html', {
                'room': room,
                'error_message': 'Дата выезда должна быть позже даты въезда.',
            })

        # Расчет общей стоимости
        delta = check_out - check_in
        total_cost = (delta.days) * room.price

        # Проверка наличия брони на выбранные даты
        if Booking.objects.filter(room_number=room,
                                  check_in_date__lte=check_out,
                                  check_out_date__gte=check_in,
                                  is_paid=True
                                  ).exists():
            # Отображение ошибки, если номер занят
            return render(request, 'booking_app/booking.html', {
                'room': room,
                'error_message': 'Выбранный номер недоступен на указанные даты.',
            })

        # Создание бронирования
        booking = Booking.objects.create(
            id_user=User.objects.create(name=name, surname=surname, age=age, phone=phone),
            room_number=room,
            check_in_date=check_in,
            check_out_date=check_out,
            total_cost=total_cost,
        )

        # Сохранение ID бронирования в сессии
        request.session['booking_id'] = booking.id

        # Перенаправление на страницу подтверждения оплаты
        return redirect('payment_confirmation')

    return render(request, 'booking_app/booking.html', {'room': room})


def payment_confirmation(request):
    booking_id = request.session.get('booking_id')
    if not booking_id:
        # Обработка случая, когда booking_id отсутствует в сессии
        return HttpResponse("Ошибка: Нет данных о бронировании.", status=400)

    # Получите общую стоимость из объекта бронирования или другого источника, если это необходимо
    booking = get_object_or_404(Booking, id=booking_id)
    total_cost = booking.total_cost

    context = {
        'total_cost': total_cost,
        'booking_id': booking_id,  # Добавление booking_id в контекст
    }
    return render(request, 'booking_app/payment_confirmation.html', context)


@require_POST
def process_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        # Создание записи об оплате
        Payment.objects.create(
            booking_id=booking,  # Используйте 'booking_id' для ссылки на модель Booking
            amount=booking.total_cost,  # Значение из поля 'total_cost' бронирования
            pay_method=payment_method  # Используйте 'pay_method' согласно вашей модели
        )

        # Обновление статуса бронирования как оплаченного (если есть такое поле в модели Booking)
        booking.is_paid = True
        booking.save()

        # Сохранение информации о бронировании в сессии для последующего использования (если необходимо)
        request.session['booking_info'] = {
            'booking_id': booking.id,
            'room_number': booking.room_number.number,  # Предполагается, что в модели Booking есть поле 'room_number'
            'check_in_date': booking.check_in_date.strftime("%Y-%m-%d"),  # Форматируем дату для хранения в сессии
            'check_out_date': booking.check_out_date.strftime("%Y-%m-%d"),
            'total_nights': (booking.check_out_date - booking.check_in_date).days,
            'total_cost': str(booking.total_cost)  # Преобразуем Decimal в строку для хранения в сессии
        }

        # Перенаправление на страницу успешной оплаты
        return redirect('payment_success', booking_id=booking_id)
    else:
        logger.error(f"Недопустимый тип запроса: {request.method} для process_payment для бронирования ID {booking_id}")
        raise SuspiciousOperation("Ожидался POST-запрос")


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

#router.register('api', BookingAPIView, basename='api')

router.register('api/booking', BookingAPIView, basename='api_booking')
router.register('api/room', RoomAPIView, basename='api_room')
router.register('api/review', ReviewAPIView, basename='api_review')
router.register('api/payment', PaymentAPIView, basename='api_payment')





