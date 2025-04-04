from django.db import models
from users.models import Doctors, Patients, Nurses
from django.utils import timezone

class Medicine(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên thuốc")
    description = models.TextField(verbose_name="Mô tả", blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá bán")
    import_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá nhập", default=0)
    quantity = models.PositiveIntegerField(default=0, verbose_name="Số lượng trong kho")
    
    # Thêm các trường mới
    supplier = models.CharField(max_length=100, verbose_name="Nhà cung cấp", blank=True, null=True)
    manufacturing_date = models.DateField(verbose_name="Ngày sản xuất", null=True, blank=True)
    expiry_date = models.DateField(verbose_name="Ngày hết hạn", null=True, blank=True)
    minimum_stock = models.PositiveIntegerField(default=10, verbose_name="Số lượng tồn tối thiểu")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MedicineImportLog(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity_imported = models.PositiveIntegerField()
    import_date = models.DateTimeField(auto_now_add=True)
    nurse = models.ForeignKey('users.Nurses', on_delete=models.SET_NULL, null=True)
    total_import_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.medicine.name} - {self.quantity_imported} - {self.import_date}"


class Prescription(models.Model):
    """
    Model for storing prescriptions created by doctors for patients
    """
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE, verbose_name="Bệnh nhân")
    doctor = models.ForeignKey(Doctors, on_delete=models.CASCADE, verbose_name="Bác sĩ")
    date_prescribed = models.DateTimeField(default=timezone.now, verbose_name="Ngày kê đơn")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Tổng tiền")
    is_paid = models.BooleanField(default=False, verbose_name="Đã thanh toán")
    paid_date = models.DateTimeField(blank=True, null=True, verbose_name="Ngày thanh toán")
    notes = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    
    class Meta:
        ordering = ['-date_prescribed']
    
    def __str__(self):
        return f"Đơn thuốc {self.id} - {self.patient.user.first_name} {self.patient.user.last_name}"
    
    def save(self, *args, **kwargs):
        # Save first to make sure the prescription exists
        super().save(*args, **kwargs)
        # Then update total price
        self.update_total_price()
    
    def update_total_price(self):
        """Calculate the total price of all items in the prescription"""
        total = sum(item.item_price for item in self.items.all())
        if self.total_price != total:
            self.total_price = total
            # Use update to avoid infinite recursion
            Prescription.objects.filter(id=self.id).update(total_price=total)


class PrescriptionItem(models.Model):
    """
    Model for storing individual medicine items in a prescription
    """
    prescription = models.ForeignKey(Prescription, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, verbose_name="Thuốc")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    instructions = models.TextField(verbose_name="Hướng dẫn sử dụng", blank=True, null=True)
    item_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá tiền")
    
    def save(self, *args, **kwargs):
        # Calculate item price based on medicine price and quantity
        self.item_price = self.medicine.price * self.quantity
        super().save(*args, **kwargs)
        
        # Update the prescription's total price
        self.prescription.update_total_price()
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"