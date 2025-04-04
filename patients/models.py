from django.db import models
from users.models import Patients ,Doctors
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps  # Import apps để sử dụng get_model

class Time(models.Model):
    time = models.CharField(max_length=10)
    class Meta:
        verbose_name = "Time"
        verbose_name_plural = "Times"
    def __str__(self):
        return self.time
    
class Status(models.Model):
    status = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Status"

    def __str__(self):
        return self.status

class Appointment(models.Model):
    doctor = models.ForeignKey(Doctors, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, )
    summary = models.TextField()
    description = models.TextField()
    start_date = models.DateField()
    status = models.ForeignKey(Status, on_delete=models.CASCADE, )
    time = models.ForeignKey(Time, on_delete=models.CASCADE, default=1)
    reminder_sent = models.BooleanField(default=False)  # Thêm trường này để theo dõi trạng thái nhắc nhở
    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
    def __str__(self):
        return self.summary

@receiver(post_save, sender=Appointment)
def create_or_update_remainder(sender, instance, created, **kwargs):
    """
    Tự động tạo hoặc cập nhật Remainder khi Appointment được tạo hoặc cập nhật.
    """
    Remainder = apps.get_model('doctors', 'Remainder')  # Lấy model Remainder từ app doctors

    if created:
        # Tạo mới Remainder khi Appointment được tạo
        Remainder.objects.create(
            title=f"Appointment with {instance.patient.user.first_name}",
            date=instance.start_date,
            comments=f"Appointment details: {instance.summary}",
            appointment=instance
        )
    else:
        # Cập nhật Remainder khi Appointment được cập nhật
        try:
            remainder = Remainder.objects.get(appointment=instance)
            remainder.title = f"Appointment with {instance.patient.user.first_name}"
            remainder.date = instance.start_date
            remainder.comments = f"Appointment details: {instance.summary}"
            remainder.save()
        except Remainder.DoesNotExist:
            # Nếu không tìm thấy Remainder, tạo mới
            Remainder.objects.create(
                title=f"Appointment with {instance.patient.user.first_name}",
                date=instance.start_date,
                comments=f"Appointment details: {instance.summary}",
                appointment=instance
            )


