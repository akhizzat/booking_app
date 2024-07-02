from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User, AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from booking_app.managers import CustomUserManager


class User(AbstractUser):
    email = models.EmailField('email address', unique=True)

    # Ваши дополнительные поля
    passport_details = models.CharField(max_length=11, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    is_guest = models.BooleanField(default=False, help_text='Designates whether this user is a guest or a partner.')

    USERNAME_FIELD = 'email'  # Указывает, что поле email используется в качестве основного идентификатора пользователя вместо стандартного username
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        self.username = self.email  # Копируем значение email в username перед сохранением
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    # Добавляем аргумент related_name для каждого поля
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="user_set_custom",
        related_query_name="user_custom",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="user_set_custom",
        related_query_name="user_custom",
    )

    @property
    def is_partner(self):
        # Проверяем, связан ли с пользователем объект Partner через related_name 'partner'
        return hasattr(self, 'partner')


# Модель Partner теперь связана напрямую с моделью User
class Partner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="partner")
    company_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return self.company_name


# Модель комиссии для Партнёров
class Commission(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='commissions')
    sales_volume = models.DecimalField(max_digits=10, decimal_places=2)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.sales_volume} - {self.commission_percentage}%"


# Модель типов питания
class MealPlan(models.Model):
    TYPE_CHOICES = [
        ('breakfast', 'Завтрак'),
        ('half_board', 'Полупансион'),
        ('full_board', 'Полный пансион'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.get_type_display()


class Room(models.Model):
    ROOM_CATEGORIES = (
        ('single', 'SGL'),
        ('double', 'DBL'),  # двуспальной кровать
        ('family', 'FM'),  # это трехместный номер
        ('luxury', 'LX'),  # это «королевский сьют»

    )

    number = models.CharField(max_length=5, unique=True)  # Уникальный номер комнаты
    category = models.CharField(max_length=7, choices=ROOM_CATEGORIES)  # Категория комнаты
    description = models.TextField(null=True)
    guests = models.IntegerField()  # Максимальное количество гостей
    price = models.DecimalField(max_digits=8, decimal_places=2)  # Цена за ночь в номере
    image = models.ImageField(
        upload_to='room_images',  # Подпапка в MEDIA_ROOT, где будут сохраняться изображения
        verbose_name='Image',
        null=True,  # Разрешаем значение NULL в базе данных
        blank=True  # Разрешаем поле быть пустым в формах
    )

    def __str__(self):
        return f'Номер комнаты {self.number}'

    # Метод предназначен для вычисления общей стоимости номера в отеле, включая стоимость выбранного
    # тарифа питания за один день
    def calculate_total_price(self, meal_plan_type=None):
        total_price = self.price
        if meal_plan_type:
            meal_plan = MealPlan.objects.get(type=meal_plan_type)
            total_price += meal_plan.price
        return total_price


class Review(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)  # Покупатель
    title = models.CharField(max_length=100, null=True)  # Новое поле для заголовка отзыва
    review = models.TextField()  # Отзыв покупателя
    rating = models.IntegerField(validators=[MaxValueValidator(5)])  # Рейтинг отеля
    review_date = models.DateField(auto_now_add=True)  # Дата написания отзыва

    def __str__(self):
        return f'{self.title} - Id номер покупателя {self.customer}'


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', null=True)
    room_number = models.ForeignKey(Room, to_field='number', on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Бронирование {self.id} для {self.user}'


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments', null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    pay_method = models.CharField(max_length=50)

    def __str__(self):
        return f'Оплата {self.id} для бронирования {self.booking.id}'
