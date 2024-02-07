from django.template.defaulttags import url
from django.urls import path, include
from . import views
from drf_multiple_model.viewsets import ObjectMultipleModelAPIViewSet
from rest_framework import routers

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





