from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile, Appointment

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='必須')
    last_name = forms.CharField(max_length=30, required=True, help_text='必須')
    email = forms.EmailField(max_length=254, required=True, help_text='必須')

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # メールアドレスをユーザー名として設定
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    birth_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[('male', '男性'), ('female', '女性')], required=True)
    PAYMENT_METHOD_CHOICES = [
        ('card', 'クレジットカード'),
        ('alipay', 'Alipay'),
    ]
    #payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Profile
        fields = [
            'first_name_kana', 
            'last_name_kana', 
            'birth_date', 
            'gender', 
            'phone_number', 
            'postal_code', 
            'address_1', 
            'address_2', 
            'insurance_card_front', 
            'insurance_card_back', 
            'id_card_front', 
            'id_card_back',
            #'payment_method'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'insurance_card_front': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'insurance_card_back': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'id_card_front': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'id_card_back': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'doctor', 
            'appointment_type', 
            'appointment_date', 
            'appointment_time', 
            'symptom_description', 
            'prescription_needed', 
            'medications', 
            'past_illnesses', 
            'allergies'
        ]

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile  # プロフィールモデルを使用します
        fields = ['birth_date', 'gender']  # 必要なフィールドを指定します
