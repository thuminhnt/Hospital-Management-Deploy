from django.urls import path
from . import views

urlpatterns = [
    path('medicine_list/', views.medicine_list, name='medicine_list'),
    path('add_medicine/', views.add_medicine, name='add_medicine'),
    path('edit_medicine/<int:medicine_id>/', views.edit_medicine, name='edit_medicine'),
    path('create_prescription/', views.create_prescription, name='create_prescription'),
    path('doctor_prescriptions/', views.doctor_prescriptions, name='doctor_prescriptions'),
    path('pending_prescriptions/', views.pending_prescriptions, name='pending_prescriptions'),
    path('prescription_history/', views.prescription_history, name='prescription_history'),  # Đường dẫn mới
    path('process_prescription/<int:prescription_id>/', views.process_prescription, name='process_prescription'),
    path('view_prescription/<int:prescription_id>/', views.view_prescription, name='view_prescription'),
    path('patient_prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('vnpay-payment-return/', views.vnpay_payment_return, name='vnpay_payment_return'),
    
    # Nurse-specific pharmacy URLs
    path('medicine-import/', views.medicine_import, name='medicine_import'),
    path('medicine-import-report/', views.medicine_import_report, name='medicine_import_report'),
]