from django.urls import path
from .views import doctor_dashboard, profile, view_appointments, cancel_appointment

urlpatterns = [
  path('doctor_dashboard/', doctor_dashboard, name='doctor_dashboard'),
  path('profile/', profile, name='doctor_profile'),
  path('doctor_view_appointments/', view_appointments, name='view_appointments'),
  path('cancel-appointment/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),
]