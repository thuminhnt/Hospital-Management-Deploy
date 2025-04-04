from django.urls import path
from . import views

urlpatterns = [
    path('nurse_dashboard/', views.nurse_dashboard, name='nurse_dashboard'),
    path('nurse_profile/', views.nurse_profile, name='nurse_profile'),
    path('nurse/appointments/', views.nurse_view_appointments, name='nurse_view_appointments'),
]