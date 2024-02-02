from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import routers

from .models import Room, Booking, Review, Payment
from .serializers import RoomSerializer, BookingSerializer, PaymentSerializer, ReviewSerializer
from drf_multiple_model.views import ObjectMultipleModelAPIView


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


# -------------api--------------------#

from drf_multiple_model.viewsets import ObjectMultipleModelAPIViewSet


class BookingAPIView(ObjectMultipleModelAPIViewSet):
    querylist = [
        {'queryset': Room.objects.all(), 'serializer_class': RoomSerializer},
        {'queryset': Booking.objects.all(), 'serializer_class': BookingSerializer},
        {'queryset': Review.objects.all(), 'serializer_class': ReviewSerializer},
        {'queryset': Payment.objects.all(), 'serializer_class': PaymentSerializer},
    ]


router = routers.DefaultRouter()
router.register('api', BookingAPIView, basename='api')