from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from .models import Partner, Review

User = get_user_model()


# 🔹 Создание формы для первичной регистрации новых партнеров в системе
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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        user.last_name = self.cleaned_data['surname']
        user.passport_details = self.cleaned_data['passport_details']
        user.phone_number = self.cleaned_data['phone_number']
        user.is_guest = False
        if commit:
            user.save()
            Partner.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                phone_number=self.cleaned_data['phone_number'],
            )
        return user


# 🔹 Редактирования существующих данных о компании партнера
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
        instance = super().save(commit=False)
        user = instance.user
        user.phone_number = self.cleaned_data.get('phone_number')
        user.save()
        if commit:
            instance.save()
        return instance


# 🔹 Форма отзыва
class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    title = forms.CharField(label='Заголовок')
    review = forms.CharField(label='Отзыв', widget=forms.Textarea)
    rating = forms.ChoiceField(choices=RATING_CHOICES, label='Рейтинг')
    user_email = forms.EmailField(label='Ваша электронная почта', required=False)

    class Meta:
        model = Review
        fields = ['title', 'review', 'rating']

    def __init__(self, *args, **kwargs):
        show_email = kwargs.pop('show_email', False)
        super().__init__(*args, **kwargs)
        if not show_email:
            self.fields.pop('user_email')

    def get_user_email(self):
        return self.cleaned_data.get('user_email')


# 🔹 🔥 Новая: форма редактирования профиля пользователя
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['display_name', 'email', 'birth_date', 'avatar', 'phone_number']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
