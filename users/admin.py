from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Users, Address, Doctors, Patients, Specialty, Nurses

def make_doctor(modeladmin, request, queryset):
    for user in queryset:
        # Đánh dấu user là bác sĩ
        user.is_doctor = True
        user.save()
        
        # Kiểm tra nếu chưa có bác sĩ với user này
        if not Doctors.objects.filter(user=user).exists():
            # Lấy specialty đầu tiên nếu có
            specialty = Specialty.objects.first()
            if specialty:
                Doctors.objects.create(user=user, specialty=specialty, bio="")
make_doctor.short_description = "Mark selected users as doctors"

def make_nurse(modeladmin, request, queryset):
    for user in queryset:
        user.is_staff = True
        user.save()
        
        # Kiểm tra nếu chưa có y tá với user này
        if not Nurses.objects.filter(user=user).exists():
            Nurses.objects.create(user=user, department="Pharmacy")
make_nurse.short_description = "Mark selected users as nurses"

class UsersAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_doctor', 'is_staff')
    list_filter = ('is_doctor', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('gender', 'birthday', 'profile_avatar', 'id_address', 'is_doctor')}),
    )
    actions = [make_doctor, make_nurse]

admin.site.register(Users, UsersAdmin)
admin.site.register(Address)
admin.site.register(Doctors)
admin.site.register(Patients)
admin.site.register(Specialty)
admin.site.register(Nurses)