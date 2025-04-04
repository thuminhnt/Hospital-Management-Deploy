from django.db import models
from users.models import Users, Doctors
from datetime import datetime
from patients.models import Appointment

class Remainder(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField()
    comments = models.TextField()
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title