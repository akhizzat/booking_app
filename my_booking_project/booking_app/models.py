from django.db import models


class Room(models.Model):
    ROOM_CATEGORIES = (
        ('SGL', 'Single'),
        ('DBL', 'Double'),  # двуспальной кровать
        ('FM', 'Family'),  # это трехместный номер
        ('LX', 'Luxury'),  # это «королевский сьют»

    )

    number = models.CharField(max_length=5, unique=True)  # Уникальный номер комнаты
    category = models.CharField(max_length=7, choices=ROOM_CATEGORIES)  # Категория комнаты
    beds = models.IntegerField()  # Количество кроватей в номере
    capacity = models.IntegerField()  # Максимальное количество гостей
    available = models.BooleanField(default=True)  # доступен ли номер для бронирования
    price = models.DecimalField(max_digits=8, decimal_places=2)  # Цена за ночь в номере
    image = models.ImageField(
        upload_to='room_images',  # Подпапка в MEDIA_ROOT, где будут сохраняться изображения
        verbose_name='Image',
        null=True,  # Разрешаем значение NULL в базе данных
        blank=True  # Разрешаем поле быть пустым в формах
    )
