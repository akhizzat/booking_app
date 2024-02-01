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
    guests = models.IntegerField()  # Максимальное количество гостей
    available = models.BooleanField(default=True)  # доступен ли номер для бронирования
    price = models.DecimalField(max_digits=8, decimal_places=2)  # Цена за ночь в номере
    image = models.ImageField(
        upload_to='room_images',  # Подпапка в MEDIA_ROOT, где будут сохраняться изображения
        verbose_name='Image',
        null=True,  # Разрешаем значение NULL в базе данных
        blank=True  # Разрешаем поле быть пустым в формах
    )

    def __str__(self):
        return f'Номер комнаты {self.number}'


class User(models.Model):
    name = models.CharField(max_length=10)
    surname = models.CharField(max_length=10)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)


class Review(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)  # Покупатель
    review = models.TextField()  # Отзыв покупателя
    rating = models.IntegerField()  # Рейтинг отеля
    review_date = models.DateField(auto_now_add=True)  # Дата написания отзыва

    def __str__(self):
        return f'Id номер покупателя {self.customer}'


class Booking(models.Model):
    id_user = models.ForeignKey(User, on_delete=models.CASCADE)  # id покупателя
    room_number = models.ForeignKey(Room, to_field='number', on_delete=models.CASCADE)  # Номер комнаты
    check_in_date = models.DateField(auto_now_add=True)  #
    check_out_date = models.DateField(auto_now_add=True)  #
    total_cost = models.DecimalField(max_digits=12, decimal_places=1)  # Стоимость

    def __str__(self):
        return f'Id номер покупателя {self.id_user}'


class Payment(models.Model):
    booking_id = models.ForeignKey(Booking, on_delete=models.CASCADE)  # Внешний ключ номера комнаты
    amount = models.DecimalField(max_digits=12, decimal_places=1)  # Сумма
    date = models.DateField(auto_now_add=True)  # Дата заказа
    pay_method = models.CharField(max_length=50)  # Метод оплачивания

    def __str__(self):
        return f'Id номер таблицы Booking {self.booking_id}'
