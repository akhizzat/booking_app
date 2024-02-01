from django.contrib import admin
from .models import Booking, Room, Review, Payment
# Register your models here.
admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(Review)
admin.site.register(Payment)