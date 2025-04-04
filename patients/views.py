from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from datetime import datetime
import json
from django.urls import reverse
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
from django.db.models import Q
from users.models import Doctors, Specialty, Patients
from patients.models import Appointment, Time, Status
from doctors.models import Remainder  # Import model Remainder

User = get_user_model()


@login_required(login_url='/login')
def patient_dashboard(request):
    patient = request.user.patients  # Lấy thông tin bệnh nhân hiện tại

    # Lấy ngày hiện tại và ngày cuối tuần
    today = now().date()
    end_of_week = today + timedelta(days=7)

    # Lấy danh sách các reminder liên quan đến bệnh nhân trong tuần
    # Chỉ hiển thị các cuộc hẹn từ ngày hiện tại trở đi
    remainders = Remainder.objects.filter(
        appointment__patient=patient,
        date__range=[today, end_of_week],
        date__gte=today  # Chỉ lấy những cuộc hẹn từ ngày hiện tại trở đi
    )

    return render(request, 'patients/patient_dashboard.html', {
        'remainders': remainders,  # Truyền danh sách reminder vào template
    })


@login_required(login_url='/login')
def my_appointments(request):
    app = Appointment.objects.filter(patient__user=request.user)

    filter_status = request.GET.get('filter_status')
    filter_date = request.GET.get('filter_date')
    filter_doctor_name = request.GET.get('filter_doctor_name')
    appointment_id = request.GET.get('appointment_id')

    if filter_status and filter_status != 'All':
        app = app.filter(status__status=filter_status)

    if filter_date:
        app = app.filter(start_date=filter_date)

    if filter_doctor_name:
        app = app.filter(doctor__user__first_name__icontains=filter_doctor_name)

    # Nếu có appointment_id được truyền vào từ URL (khi click "View" từ remainder)
    highlighted_appointment = None
    if appointment_id:
        try:
            highlighted_appointment = int(appointment_id)
        except ValueError:
            highlighted_appointment = None

    return render(request, "patients/my_appointments.html", {
        'appointments': app,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'filter_doctor_name': filter_doctor_name,
        'highlighted_appointment': highlighted_appointment
    })


@login_required(login_url='/login')
def book_appointment(request):
    specialities = Specialty.objects.all()
    doctors = Doctors.objects.all()

    filter_speciality = request.GET.get('filter_speciality')
    filter_city = request.GET.get('filter_city')
    filter_doctor_name = request.GET.get('filter_doctor_name')

    if filter_speciality and filter_speciality != 'All':
        doctors = doctors.filter(specialty__name=filter_speciality)

    if filter_doctor_name:
        doctors = doctors.filter(user__first_name__icontains=filter_doctor_name)

    if filter_city:
        doctors = doctors.filter(user__id_address__city__icontains=filter_city)

    return render(request, "patients/book_appointment.html", {
        'doctors': doctors,
        'specialities': specialities,
        'filter_speciality': filter_speciality,
        'filter_doctor_name': filter_doctor_name,
        'filter_city': filter_city,
    })


@login_required(login_url='/login')
def patient_confirm_book(request, doctor):
    try:
        # Get the doctor object
        doctor_obj = Doctors.objects.get(user__username=doctor)
        
        # Handle POST request (booking appointment)
        if request.method == 'POST':
            # Get form data
            date = request.POST.get("date")
            summary = request.POST.get("summary")
            description = request.POST.get("description")
            time_str = request.POST.get("time")
            
            # Validate input
            if not all([date, summary, time_str]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('patient_confirm_book', doctor=doctor)
            
            # Convert date
            try:
                selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                return redirect('patient_confirm_book', doctor=doctor)
            
            # Check if selected date is in the past
            if selected_date < datetime.now().date():
                messages.error(request, "Cannot book an appointment in the past. Please select a future date.")
                return redirect('patient_confirm_book', doctor=doctor)
            
            # If date is today, check if time is in the past
            if selected_date == datetime.now().date():
                # Convert time string to datetime.time object
                try:
                    selected_time = datetime.strptime(time_str, "%H:%M").time()
                    current_time = datetime.now().time()
                    
                    if selected_time < current_time:
                        messages.error(request, "Cannot book an appointment for a time that has already passed. Please select a future time.")
                        return redirect('patient_confirm_book', doctor=doctor)
                except ValueError:
                    # If time format is different, let it pass - this will be handled by other validations
                    pass
            
            # Get patient, time, and status objects
            try:
                patient = Patients.objects.get(user=request.user)
                time_obj = Time.objects.get(time=time_str)
                status = Status.objects.get(status="Waited")
                
                # Check for existing appointments
                existing_appointment = Appointment.objects.filter(
                    doctor=doctor_obj,
                    start_date=selected_date,
                    time=time_obj
                ).exists()
                
                if existing_appointment:
                    messages.error(request, f"The time slot {time_str} on {date} is already booked.")
                    return redirect('patient_confirm_book', doctor=doctor)
                
                # Create appointment
                appointment = Appointment.objects.create(
                    summary=summary,
                    description=description,
                    start_date=selected_date,
                    time=time_obj,
                    doctor=doctor_obj,
                    patient=patient,
                    status=status
                )
                
                messages.success(request, "Appointment booked successfully!")
                return redirect(f"{reverse('my_appointments')}?appointment_id={appointment.id}")
            
            except (Patients.DoesNotExist, Time.DoesNotExist, Status.DoesNotExist) as e:
                messages.error(request, "An error occurred. Please try again.")
                return redirect('patient_confirm_book', doctor=doctor)
        
        # GET request - show booking form
        # Get all times
        all_times = Time.objects.all()
        
        # Find booked times for this doctor on selected date
        booked_times = Appointment.objects.filter(
            doctor=doctor_obj,
            start_date__gte=datetime.now().date()
        ).values_list('time__time', 'start_date')
        
        # Convert booked times for this doctor on selected date
        booked_time_slots = {}
        for time, date in booked_times:
            # Convert date to string to make it JSON serializable
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in booked_time_slots:
                booked_time_slots[date_str] = []
            booked_time_slots[date_str].append(time)  # Append time directly to the list

        return render(request, 'patients/patient_confirm_book.html', {
            'times': all_times, 
            'doctor': doctor_obj,
            'booked_time_slots': json.dumps(booked_time_slots)  # Serialize to JSON
        })
    
    except Doctors.DoesNotExist:
        messages.error(request, "Doctor not found.")
        return redirect('book_appointment')


@login_required(login_url='/login')
def send_reminders(request):
    # Lấy thời gian hiện tại
    current_time = now()
    # Lấy các lịch hẹn trong vòng 24 giờ tới và chưa được nhắc nhở
    upcoming_appointments = Appointment.objects.filter(
        start_date__gte=current_time.date(),
        start_date__lte=(current_time + timedelta(days=1)).date(),
        reminder_sent=False
    )

    for appointment in upcoming_appointments:
        # Gửi email nhắc nhở
        send_mail(
            subject='Reminder: Upcoming Appointment',
            message=f'Dear {appointment.patient.user.first_name},\n\n'
                    f'You have an appointment with Dr. {appointment.doctor.user.first_name} '
                    f'on {appointment.start_date} at {appointment.time.time}.\n\n'
                    f'Please make sure to attend on time.\n\nThank you!',
            from_email='hospital@example.com',
            recipient_list=[appointment.patient.user.email],
            fail_silently=False,
        )

        # Đánh dấu đã gửi nhắc nhở
        appointment.reminder_sent = True
        appointment.save()

    messages.success(request, "Reminders sent successfully!")
    return redirect('patient_dashboard')  


@login_required(login_url='/login')
def create_appointment(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        patient = request.user.patients
        summary = request.POST.get('summary')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        time_id = request.POST.get('time_id')

        doctor = Doctors.objects.get(id=doctor_id)
        time = Time.objects.get(id=time_id)

        # Tạo Appointment
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            summary=summary,
            description=description,
            start_date=start_date,
            time=time
        )
        messages.success(request, "Appointment created successfully!")
        return redirect('patient_dashboard')

    return render(request, 'patients/create_appointment.html')