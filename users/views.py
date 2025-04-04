from django.http import request
from django.http.response import HttpResponse
from multiprocessing import context
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import get_user_model
from .models import Doctors, Patients, Address , Reste_token , Specialty, Users, Nurses
from .helpers import send_email
import uuid

Users = get_user_model()

def register(request):
  specialities = Specialty.objects.all()
  if request.method == 'POST':
    # Chỉ cho phép đăng ký tài khoản bệnh nhân qua form đăng ký
    user_status = "Patient"  # Mặc định chỉ cho phép đăng ký bệnh nhân
    first_name = request.POST.get('user_firstname')
    last_name = request.POST.get('user_lastname')
    profile_pic = ""

    if "profile_pic" in request.FILES:
      profile_pic = request.FILES['profile_pic']

    username = request.POST.get('user_id')
    email = request.POST.get('email')
    gender = request.POST.get('user_gender')
    birthday = request.POST.get("birthday")
    password = request.POST.get('password')
    confirm_password = request.POST.get('conf_password')
    address_line = request.POST.get('address_line')
    region = request.POST.get('region')
    city = request.POST.get('city')
    pincode = request.POST.get('pincode')

    # Các kiểm tra về mật khẩu giữ nguyên
    if len(password) < 6:
      messages.error(request, 'Password must be at least 6 characters long.')
      return render(request, 'users/register.html', context={'specialities': specialities, 'user_firstname': first_name, 'user_lastname': last_name, 'user_id': username, 'email': email, 'user_gender': gender, 'address_line': address_line, 'region': region, 'city': city, 'pincode': pincode})

    if password != confirm_password:
      messages.error(request, 'Passwords do not match.')
      return render(request, 'users/register.html', context={'specialities': specialities, 'user_firstname': first_name, 'user_lastname': last_name, 'user_id': username, 'email': email, 'user_gender': gender, 'address_line': address_line, 'region': region, 'city': city, 'pincode': pincode})

    # Kiểm tra username đã tồn tại chưa
    if Users.objects.filter(username=username).exists():
      messages.error(request, 'Username already exists. Try again with a different username.')
      return render(request, 'users/register.html', context={'specialities': specialities, 'user_firstname': first_name, 'user_lastname': last_name, 'user_id': username, 'email': email, 'user_gender': gender, 'address_line': address_line, 'region': region, 'city': city, 'pincode': pincode})

    # Kiểm tra email đã tồn tại chưa
    if Users.objects.filter(email=email).exists():
      messages.error(request, 'Email already exists. Try again with a different email.')
      return render(request, 'users/register.html', context={'specialities': specialities, 'user_firstname': first_name, 'user_lastname': last_name, 'user_id': username, 'email': email, 'user_gender': gender, 'address_line': address_line, 'region': region, 'city': city, 'pincode': pincode})

    address = Address.objects.create(address_line=address_line, region=region, city=city, code_postal=pincode)

    user = Users.objects.create_user(
      first_name=first_name,
      last_name=last_name,
      profile_avatar=profile_pic,
      username=username,
      email=email,
      gender=gender,
      birthday=birthday,
      password=password,
      id_address=address,
      is_doctor=False  # Luôn đặt là False vì chỉ đăng ký bệnh nhân
    )
      
    user.save()

    # Chỉ xử lý đăng ký bệnh nhân
    insurance = request.POST.get('insurance')
    patient = Patients.objects.create(user=user, insurance=insurance)
    patient.save()

    messages.success(request, 'Your account has been successfully registered. Please login.', extra_tags='success')

  return render(request, 'users/register.html', {'specialities': specialities})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Đơn giản hóa quá trình đăng nhập
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Chuyển hướng dựa trên vai trò
            if hasattr(user, 'nurses'):
                return redirect('nurse_dashboard')
            elif user.is_doctor:
                return redirect('doctor_dashboard')
            elif hasattr(user, 'patients'):
                return redirect('patient_dashboard')
        else:
            messages.error(request, 'Incorrect username or password')
    
    return render(request, 'users/login.html')

def forgot_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = Users.objects.filter(email=email)
        if user:
            token = str(uuid.uuid4())
            reset = Reste_token.objects.create(
                user=user[0],
                email=user[0].email,  
                token=token  
            )
            reset.save()
            sent = send_email(user[0].email,token)
            if sent:
                return render(request, 'users/forgot.html',context={'send_email_succes': 1})
        else:
            return render(request, 'users/forgot.html', context={'errorlogin': 1})
    return render(request, 'users/forgot.html')

def reset_view(request,token):
    if request.method == 'POST':
        reste = Reste_token.objects.filter(token=token)
        print(reste)
        if reste:
            password = request.POST.get('password')
            confirm_password = request.POST.get('conf_password')
            if len(password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'users/reset.html', {'token': token} )
            print(password)
            print(confirm_password)
            if password != confirm_password:
                messages.error(request, 'password do not match')
                return render(request, 'users/reset.html', {'token': token} )
            user = Users.objects.filter(email=reste[0].email).first()
            if user:
                hashed_password = make_password(password)
                user.password = hashed_password
                user.save()
                reste.delete()
                return redirect('login')
            else:
                return render(request, 'users/reset.html', {'token': token , 'errorlogin':1} )
        return render(request, 'users/reset.html', {'token': token} )
    return render(request, 'users/reset.html',{'token': token})

@login_required(login_url='/login')
def logout_view(request):
    logout(request)
    return redirect('login')

