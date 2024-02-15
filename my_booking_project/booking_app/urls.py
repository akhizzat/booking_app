
from django.urls import path, include
from . import views

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)
from .views import router

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('rooms/', views.rooms, name='rooms'),
    path('search/', views.search_rooms, name='search_rooms'),
    path('booking/<int:room_id>/', views.booking, name='booking'),
    path('payment_success/<int:booking_id>/', views.payment_success, name='payment_success'),
    path('process_payment/<int:booking_id>/', views.process_payment, name='process_payment'),
    path('payment_confirmation/', views.payment_confirmation, name='payment_confirmation'),



] + router.urls


urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path(
        'api/schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),
    path(
        'api/schema/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]


