from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from datetime import datetime, date, timedelta
from django.utils.timezone import now
from django.db.models import Q, Count

from patients.models import Appointment, Status
from .models import Remainder
from users.models import Doctors, Specialty

User = get_user_model()

@login_required(login_url='/login')
def doctor_dashboard(request):
    doctor = request.user.doctors  # Get current doctor info

    # Get current date and end of week
    today = now().date()
    end_of_week = today + timedelta(days=7)

    # Get "Cancel" status
    cancel_status = Status.objects.get(status="Cancel")

    # Get remainders related to current doctor
    # Only show appointments from current date to future
    remainders = Remainder.objects.filter(
        appointment__doctor=doctor,
        date__range=[today, end_of_week],
        date__gte=today  # Only get appointments from current date forward
    ).exclude(appointment__status=cancel_status)

    return render(request, 'doctors/doctor_dashboard.html', {
        'remainders': remainders,  # Only remainders for current doctor
    })


@login_required(login_url='/login')
def profile(request):
    specialities = Specialty.objects.all()
    updated_profile_successfully = False
    base_template = 'patients/base.html'
    if request.user.is_doctor:
      base_template = 'doctors/base.html'
    
    if request.method == 'POST':
      # Only handle profile updates, no password changes
      if 'update_profile' in request.POST:
        user = request.user
        user.first_name = request.POST.get('user_firstname')
        user.last_name = request.POST.get('user_lastname')
        user.gender = request.POST.get('user_gender')
        user.birthday = request.POST.get('birthday')
        
        # Handle address updates
        if hasattr(user, 'id_address') and user.id_address:
            user.id_address.address_line = request.POST.get('address_line')
            user.id_address.region = request.POST.get('region')
            user.id_address.city = request.POST.get('city')
            user.id_address.code_postal = request.POST.get('code_postal')
            user.id_address.save()
        
        if(user.is_doctor):
          specialty = request.POST.get('Speciality')
          specialty_name = Specialty.objects.get(name=specialty)

          doctor_profile = user.doctors
          doctor_profile.specialty = specialty_name
          doctor_profile.bio = request.POST.get('bio')
          doctor_profile.save()
        else:
          patient_profile = user.patients
          patient_profile.insurance = request.POST.get('insurance')
          patient_profile.save()

        if 'profile_pic' in request.FILES:
          user.profile_avatar = request.FILES['profile_pic']

        user.save()
        updated_profile_successfully = True
        
    curruser = request.user.username
    data = User.objects.get(username=curruser)
    return render(request, 'doctors/profile.html', context={
            "basicdata": data,
            "updated_profile_successfully": updated_profile_successfully,
            'base_template': base_template,
            "specialities": specialities
        })


@login_required(login_url='/login')
def view_appointments(request):
    if request.method == 'POST':
        status = request.POST.get("status")
        app_id = request.POST.get("app")

        app = Appointment.objects.get(id=app_id)
        status_id = Status.objects.get(status=status)
        app.status = status_id
        app.save()
        
        # If status is "Cancel", delete corresponding remainder
        if status == "Cancelled":
            Remainder.objects.filter(appointment=app).delete()
            
        return redirect('view_appointments')  # Redirect to avoid form resubmission

    app = Appointment.objects.filter(doctor__user=request.user)

    filter_status = request.GET.get('filter_status')
    filter_date = request.GET.get('filter_date')
    filter_patient_name = request.GET.get('filter_patient_name')
    appointment_id = request.GET.get('appointment_id')

    if filter_status and filter_status != 'All':
        app = app.filter(status__status=filter_status)

    if filter_date:
        app = app.filter(start_date=filter_date)

    if filter_patient_name:
        app = app.filter(patient__user__first_name__icontains=filter_patient_name)
        
    # If appointment_id is passed from URL (when clicking "View" from remainder)
    highlighted_appointment = None
    if appointment_id:
        try:
            highlighted_appointment = int(appointment_id)
        except ValueError:
            highlighted_appointment = None

    return render(request, "doctors/viewappointments.html", {
        'appointments': app,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'filter_patient_name': filter_patient_name,
        'highlighted_appointment': highlighted_appointment
    })


@login_required(login_url='/login')
def cancel_appointment(request, appointment_id):
    # Get appointment to cancel
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Update appointment status to "Cancel"
    cancel_status = Status.objects.get(status="Cancel")
    appointment.status = cancel_status
    appointment.save()

    # Delete corresponding reminder (if needed)
    Remainder.objects.filter(appointment=appointment).delete()

    messages.success(request, "Appointment has been canceled successfully.")
    return redirect('doctor_dashboard')