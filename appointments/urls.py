from django.urls import path
from . import views

urlpatterns = [
    path('appointment/', views.appointment_view, name='appointment'),
    path('confirm_appointment/', views.confirm_appointment, name='confirm_appointment'),
    path('appointment_confirmation/', views.appointment_confirmation_page, name='appointment_confirmation'),  # ここを修正

    path('appointment/edit/<int:appointment_id>/', views.edit_appointment_view, name='edit_appointment'),

    path('google-calendar-auth/', views.google_calendar_auth, name='google_calendar_auth'),
    path('google_login/', views.google_login, name='google_login'),

]
