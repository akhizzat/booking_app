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
] + router.urls





