from django.shortcuts import render
from django.http import HttpResponse
from .models import Room, Booking
from django.db.models import Q



def index(request):
    return render(request, 'booking_app/index.html')


def about(request):
    return HttpResponse('О нас')


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
    guests = request.GET.get('guests')


    # Найти все бронирования, которые перекрывают запрашиваемые даты
    booked_rooms = Booking.objects.filter(
        Q(check_in_date__lte=checkout_date, check_out_date__gte=checkin_date)
    ).values_list('room_number', flat=True)

    # Исключить забронированные номера из доступных
    available_rooms_query = Room.objects.exclude(
        number__in=booked_rooms
    ).filter(
        available=True
    )

    # Применяем фильтрацию по типу комнаты и количеству гостей, если они указаны
    if room_type:
        available_rooms_query = available_rooms_query.filter(category=room_type, guests__gte=guests)

    available_rooms = available_rooms_query.all()

    return render(request, 'booking_app/search.html', {'rooms': available_rooms})