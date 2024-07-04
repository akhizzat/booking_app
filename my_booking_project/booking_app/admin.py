from django.contrib import admin
from .models import Booking, Room, Review, Payment, MealPlan, User, Partner, Commission
# Register your models here.
admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(Review)
admin.site.register(Payment)
admin.site.register(MealPlan)
admin.site.register(User)
admin.site.register(Partner)
admin.site.register(Commission)