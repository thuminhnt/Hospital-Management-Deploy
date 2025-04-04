from django.urls import path
from .views import patient_dashboard, book_appointment, my_appointments, patient_confirm_book, send_reminders
from doctors.views import profile

urlpatterns = [
    path('patient_dashboard/', patient_dashboard, name='patient_dashboard'),
    path('profile/', profile, name='patient_profile'),
    path('book_appointment/', book_appointment, name='book_appointment'),
    path('my_appointments/', my_appointments, name='my_appointments'),
    path('patient_confirm_book/<str:doctor>/', patient_confirm_book, name='patient_confirm_book'),
    path('send-reminders/', send_reminders, name='send_reminders'),
]