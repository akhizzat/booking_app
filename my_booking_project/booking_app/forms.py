from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator

from .models import Partner, Review

User = get_user_model()


# Создание формы для первичной регистрации новых партнеров в системе

class PartnerRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=255, required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=100, required=True)
    surname = forms.CharField(max_length=100, required=True)
    passport_details = forms.CharField(max_length=11, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'name', 'surname', 'passport_details', 'phone_number', 'password1', 'password2')

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['password1'].help_text = None
    #     self.fields['password2'].help_text = None

    # Проверка: не зарегистрирован ли уже пользователь с таким же адресом электронной почты
    def clean_email(self):
        email = self.cleaned_data.get('email')  # Получение значение email из формы для электронной почты
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    # Сохранение нового пользователя (Партнера) в базе данных

    def save(self, commit=True):
        user = super().save(commit=False)  # Cоздание объекта пользователя без сохранения его в базу данных
        # Значения из формы используются для заполнения полей объекта пользователя
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        user.last_name = self.cleaned_data['surname']
        user.passport_details = self.cleaned_data['passport_details']
        user.phone_number = self.cleaned_data['phone_number']
        user.is_guest = False  # Указывает, что пользователь не является гостем

        if commit:
            user.save()
            Partner.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                phone_number=self.cleaned_data['phone_number'],
            )
        return user


#  Редактирования существующих данных о компании партнера

class PartnerProfileForm(forms.ModelForm):
    company_name = forms.CharField(
        label='Название компании',
        error_messages={'max_length': "Это название слишком длинное."},
        validators=[MinLengthValidator(2, message="Имя компании должно быть не менее 2 символов")],
        max_length=255
    )
    phone_number = forms.CharField(
        label='Телефон компании',
        error_messages={'max_length': "Этот номер телефона слишком длинный."},
        validators=[MinLengthValidator(10, message="Номер телефона должен содержать не менее 10 цифр")],
        max_length=20
    )

    class Meta:
        model = Partner
        fields = ['company_name', 'phone_number']

    def save(self, commit=True):
        # Создание объекта модели Partner из данных формы, но пока без сохранения в БД
        instance = super().save(commit=False)
        # Получаем связанный объект пользователя из текущего экземпляра модели Partner
        user = instance.user
        # Обновляем номер телефона пользователя данными из формы
        user.phone_number = self.cleaned_data.get('phone_number')
        user.save()

        if commit:
            instance.save()
        return instance


class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    title = forms.CharField(label='Заголовок')
    review = forms.CharField(label='Отзыв')
    rating = forms.ChoiceField(choices=RATING_CHOICES, label='Рейтинг')
    user_email = forms.EmailField(label='Ваша электронная почта')

    class Meta:
        model = Review
        fields = ['title', 'review', 'rating', 'user_email']
        exclude = ['user_email']  # Исключаем user_email из сохраняемых полей модели

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.fields['user_email'].required = True
