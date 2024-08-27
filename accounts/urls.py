from django.urls import path
from .views import user_signup_view, user_login_view, doctor_login_view, user_mypage_view, doctor_mypage_view, logout_view, admin_login_view, admin_mypage_view
from . import views

urlpatterns = [
    path('user-login/', user_login_view, name='user_login'),
    path('doctor-login/', doctor_login_view, name='doctor_login'),
    path('admin-login/', admin_login_view, name='admin_login'),

    path('user-mypage/', user_mypage_view, name='user_mypage'),
    path('doctor-mypage/', doctor_mypage_view, name='doctor_mypage'),
    path('admin-mypage/', admin_mypage_view, name='admin_mypage'),
    
    path('user-signup/', user_signup_view, name='user_signup'),
    path('logout/', logout_view, name='logout'),

    path('basic_info/', views.basic_info_view, name='basic_info'),
    path('basic_info/edit/', views.edit_basic_info_view, name='edit_basic_info'),
    path('appointments/', views.appointment_list_view, name='appointment_list'),

    path('doctor_appointments/', views.doctor_appointment_list_view, name='doctor_appointment_list'),
    path('medical-records/<int:user_id>/<int:appointment_id>/', views.medical_record_list_view, name='medical_record_list'),
    path('medical-record-detail/<int:user_id>/<int:record_id>/', views.medical_record_detail_view, name='medical_record_detail'),
    path('patient-list/', views.patient_list_view, name='patient_list_view'),

    path('medical-records/create/<int:user_id>/<int:appointment_id>/', views.create_medical_record_view, name='create_medical_record'),
    path('doctor-schedule/', views.doctor_schedule_view, name='doctor_schedule'),
    path('save-schedule/', views.save_schedule_view, name='save_schedule'),
    path('delete-schedule/', views.delete_schedule_view, name='delete_schedule'),


    path('cancel-appointment/', views.cancel_appointment, name='cancel_appointment'),

    path('admin_appointments/', views.admin_appointment_list_view, name='admin_appointment_list'),


    path('save_prescription/', views.save_prescription, name='save_prescription'),
]
