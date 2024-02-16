from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Partner, Review

User = get_user_model()

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Здесь предполагается, что username не используется или дублирует email
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

class PartnerProfileForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ['company_name', 'phone_number']
        labels = {
            'company_name': 'Название компании',
            'phone_number': 'Телефон компании',
        }
        help_texts = {
            'company_name': 'Введите название вашей компании.',
            'phone_number': 'Введите контактный телефон вашей компании.',
        }
        error_messages = {
            'company_name': {
                'max_length': "Это название слишком длинное.",
            },
            'phone_number': {
                'max_length': "Этот номер телефона слишком длинный.",
            },
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        user = instance.user
        user.phone_number = self.cleaned_data.get('phone_number')
        user.save()

        if commit:
            instance.save()
        return instance


