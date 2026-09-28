from django.db import models
from django.contrib.auth.models import User

class Phong(models.Model):
    TRANG_THAI_CHOICES = [
        ('trong', 'Phòng trống'),
        ('dang_thue', 'Đang thuê'),
        ('bao_tri', 'Đang bảo trì'),
    ]

    ten_phong = models.CharField(max_length=50, unique=True)
    gia_phong = models.DecimalField(max_digits=12, decimal_places=0)
    dien_tich = models.DecimalField(max_digits=6, decimal_places=2)
    trang_thai = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='trong'
    )
    mo_ta = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ten_phong
    
class NguoiThue(models.Model):
    ho_ten = models.CharField(max_length=100)
    ngay_sinh = models.DateField(blank=True, null=True)
    so_cccd = models.CharField(max_length=20, unique=True)
    so_dien_thoai = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    dia_chi = models.CharField(max_length=255, blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ho_ten

class HopDong(models.Model):
    TRANG_THAI_CHOICES = [
        ('hieu_luc', 'Đang hiệu lực'),
        ('het_han', 'Đã hết hạn'),
        ('huy', 'Đã hủy'),
    ]

    phong = models.ForeignKey(
        Phong,
        on_delete=models.PROTECT,
        related_name='hop_dong'
    )

    nguoi_thue = models.ForeignKey(
        NguoiThue,
        on_delete=models.PROTECT,
        related_name='hop_dong'
    )

    ngay_bat_dau = models.DateField()
    ngay_ket_thuc = models.DateField(blank=True, null=True)
    tien_coc = models.DecimalField(max_digits=12, decimal_places=0)
    trang_thai = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='hieu_luc'
    )
    ghi_chu = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nguoi_thue.ho_ten} - {self.phong.ten_phong}'

class DienNuoc(models.Model):
    phong = models.ForeignKey(
        Phong,
        on_delete=models.PROTECT,
        related_name='dien_nuoc'
    )

    thang = models.DateField()

    chi_so_dien_cu = models.PositiveIntegerField(default=0)
    chi_so_dien_moi = models.PositiveIntegerField(default=0)

    chi_so_nuoc_cu = models.PositiveIntegerField(default=0)
    chi_so_nuoc_moi = models.PositiveIntegerField(default=0)

    don_gia_dien = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=3500
    )

    don_gia_nuoc = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=15000
    )

    ghi_chu = models.TextField(
        blank=True,
        null=True
    )

    ngay_tao = models.DateTimeField(
        auto_now_add=True
    )

    def tien_dien(self):
        so_dien = max(
            0,
            self.chi_so_dien_moi - self.chi_so_dien_cu
        )
        return so_dien * self.don_gia_dien

    def tien_nuoc(self):
        so_nuoc = max(
            0,
            self.chi_so_nuoc_moi - self.chi_so_nuoc_cu
        )
        return so_nuoc * self.don_gia_nuoc

    def __str__(self):
        return f'{self.phong.ten_phong} - {self.thang.strftime("%m/%Y")}'

class ThanhToan(models.Model):
    TRANG_THAI_CHOICES = [
        ('chua_thanh_toan', 'Chưa thanh toán'),
        ('da_thanh_toan', 'Đã thanh toán'),
    ]

    phong = models.ForeignKey(
        Phong,
        on_delete=models.PROTECT,
        related_name='thanh_toan'
    )

    thang = models.DateField()

    tien_phong = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )

    tien_dien = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0
    )

    tien_nuoc = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0
    )

    tien_khac = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0
    )

    tong_tien = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0
    )

    trang_thai = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='chua_thanh_toan'
    )

    ngay_thanh_toan = models.DateTimeField(
        blank=True,
        null=True
    )

    ghi_chu = models.TextField(
        blank=True,
        null=True
    )

    ngay_tao = models.DateTimeField(
        auto_now_add=True
    )

    def tinh_tong_tien(self):
        return (
            self.tien_phong
            + self.tien_dien
            + self.tien_nuoc
            + self.tien_khac
        )

    def save(self, *args, **kwargs):
        self.tong_tien = self.tinh_tong_tien()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.phong.ten_phong} - {self.thang.strftime("%m/%Y")}'

class TaiKhoan(models.Model):
    VAI_TRO_CHOICES = [
        ('chu_tro', 'Chủ trọ'),
        ('nguoi_thue', 'Người thuê'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='tai_khoan'
    )

    vai_tro = models.CharField(
        max_length=20,
        choices=VAI_TRO_CHOICES
    )

    so_dien_thoai = models.CharField(
        max_length=15,
        blank=True
    )

    def __str__(self):
        return f'{self.user.username} - {self.get_vai_tro_display()}'