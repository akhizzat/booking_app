
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
    path('booking_by_partner/', views.booking_by_partner, name='booking_by_partner'),
    path('edit-profile/', views.edit_partner_profile, name='edit_partner_profile'),
    path('partner/dashboard/', views.partner_panel, name='partner_dashboard'),
    path('login_or_register/', views.login_or_register, name='login_or_register'),
    path('booking_from_search/', views.booking_from_search, name='booking_from_search'),
    path('search_rooms_partner/', views.search_rooms_partner, name='search_rooms_partner'),
    path('create_booking/', views.create_booking_and_redirect_to_payment, name='create_booking'),
    path('restaurant/', views.restaurant, name='restaurant'),
    path('entertainment/', views.entertainment, name='entertainment'),
    path('spa/', views.spa, name='spa'),
    path('stocks/', views.stocks, name='stocks'),
    path('contact/', views.contact, name='contact'),
    path('reviews/', views.reviews, name='reviews'),



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


