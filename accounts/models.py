from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )
    
    email = models.EmailField(unique=True)
    username = models.EmailField(unique=True)  # Username will be the email address
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username
    
class Profile(models.Model):
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE)
    first_name_kana = models.CharField(max_length=30, default="")
    last_name_kana = models.CharField(max_length=30, default="")
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', '男性'), ('female', '女性')])
    phone_number = models.CharField(max_length=15, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    address_1 = models.CharField(max_length=255, blank=True)
    address_2 = models.CharField(max_length=255, blank=True)
    insurance_card_front = models.ImageField(upload_to='insurance_cards/', blank=True)
    insurance_card_back = models.ImageField(upload_to='insurance_cards/', blank=True)
    id_card_front = models.ImageField(upload_to='id_cards/', blank=True)
    id_card_back = models.ImageField(upload_to='id_cards/', blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    default_payment_method_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

class DoctorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    introduction = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='doctor_photos/', null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', '男性'), ('female', '女性')])

    def __str__(self):
        return self.user.username

class Department(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='department_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Appointment(models.Model):

    STATUS_CHOICES = [
        ('completed', '完了'),
        ('in_progress', '予約中'),
        ('cancelled', '取消'),
        ('expired', '期限切れ'),
        ('examined', '診察済み'),
    ]

    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='user_appointments')
    doctor = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_type = models.CharField(max_length=50)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    symptom_or_medicine_categoryid = models.IntegerField(null=True, blank=True)
    symptom_or_medicine_id = models.IntegerField(null=True, blank=True)
    symptom_description = models.TextField(null=True, blank=True)
    prescription_needed = models.BooleanField(default=False)
    medications = models.CharField(max_length=255, null=True, blank=True)
    past_illnesses = models.CharField(max_length=255, null=True, blank=True)
    allergies = models.CharField(max_length=255, null=True, blank=True)
    meet_link = models.URLField(max_length=255, null=True, blank=True)  # ここでGoogle Meetリンクを保存するフィールドを追加
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    event_id = models.CharField(max_length=255, null=True, blank=True)  # Google CalendarイベントID
    payment_intent_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.appointment_type} - {self.appointment_date} - {self.user}"

class MedicalHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    doctor = models.CharField(max_length=100)
    appointment_type = models.CharField(max_length=10, choices=[('revisit', '再診'), ('first', '初診')])
    date = models.DateField()
    time = models.TimeField()
    symptoms = models.TextField(blank=True, null=True)
    prescription_needed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.date} {self.time}"
    
class MedicineCategory(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class SymptomCategory(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Medicine(models.Model):
    category = models.ForeignKey(MedicineCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Symptom(models.Model):
    category = models.ForeignKey(SymptomCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    

class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True, blank=True)
    medicine_name = models.CharField(max_length=255, blank=True)  # カスタム入力された薬名を保存
    days = models.PositiveIntegerField(default=1)  # 処方の日数
    price = models.DecimalField(max_digits=10, decimal_places=2)  # 価格
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medicine_name or self.medicine.name} - {self.appointment.user.get_full_name()} ({self.days} days)"



class MedicalRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='medical_records'  # 患者のカルテを取得するためのリレーション
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_medical_records'  # 医師が担当したカルテを取得するためのリレーション
    )
    appointment = models.ForeignKey(
        'Appointment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    record_content = models.TextField()  # カルテの内容を保存
    created_at = models.DateTimeField(auto_now_add=True)  # カルテが作成された日時を保存

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
from django.db import models
from django.conf import settings

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.start_time} - {self.end_time})"