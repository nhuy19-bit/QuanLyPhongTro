from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError

class CoSo(models.Model):
    ten_co_so = models.CharField(max_length=100, unique=True)
    dia_chi = models.CharField(max_length=255, blank=True)
    mo_ta = models.TextField(blank=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cơ sở'
        verbose_name_plural = 'Cơ sở'
        ordering = ('ten_co_so',)

    def __str__(self):
        return self.ten_co_so


class Phong(models.Model):
    TRANG_THAI_CHOICES = [
        ('trong', 'Phòng trống'),
        ('dang_thue', 'Đang thuê'),
        ('bao_tri', 'Đang bảo trì'),
    ]

    co_so = models.ForeignKey(
        CoSo,
        on_delete=models.PROTECT,
        related_name='phong',
        null=True,
        blank=True,
    )
    ten_phong = models.CharField(max_length=50)
    gia_phong = models.DecimalField(max_digits=12, decimal_places=0)
    dien_tich = models.DecimalField(max_digits=6, decimal_places=2)
    trang_thai = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='trong'
    )
    mo_ta = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Phòng'
        verbose_name_plural = 'Phòng'
        constraints = [
            models.UniqueConstraint(
                fields=['co_so', 'ten_phong'],
                name='unique_ten_phong_trong_co_so'
            )
        ]

    def __str__(self):
        return self.ten_phong
    
    def clean(self):
        super().clean()
        co_hop_dong = bool(self.pk and HopDong.objects.filter(
            phong_id=self.pk, trang_thai='hieu_luc'
        ).exists())
        if co_hop_dong and self.trang_thai != 'dang_thue':
            raise ValidationError({'trang_thai': 'Phòng đang có hợp đồng hiệu lực. Phải chọn Đang thuê.'})
        if not co_hop_dong and self.trang_thai == 'dang_thue':
            raise ValidationError({'trang_thai': 'Phòng chưa có hợp đồng hiệu lực. Không thể chọn Đang thuê.'})

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.pk:
            list(Phong.objects.select_for_update().filter(pk=self.pk))
        self.clean()
        return super().save(*args, **kwargs)


class NguoiThue(models.Model):
    tai_khoan = models.OneToOneField(
        'TaiKhoan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ho_so_nguoi_thue'
    )

    ho_ten = models.CharField(max_length=100)
    ngay_sinh = models.DateField(blank=True, null=True)
    so_cccd = models.CharField(max_length=20, unique=True)
    so_dien_thoai = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    dia_chi = models.CharField(max_length=255, blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Người thuê'
        verbose_name_plural = 'Người thuê'

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

    ngay_ket_thuc = models.DateField(
        blank=True,
        null=True
    )

    tien_coc = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )

    trang_thai = models.CharField(
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='hieu_luc'
    )

    ghi_chu = models.TextField(
        blank=True,
        null=True
    )

    ngay_tao = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Hợp đồng'
        verbose_name_plural = 'Hợp đồng'

        constraints = [
            models.UniqueConstraint(
                fields=['phong'],
                condition=models.Q(trang_thai='hieu_luc'),
                name='unique_hop_dong_hieu_luc_moi_phong'
            )
        ]

    def __str__(self):
        return f'{self.nguoi_thue.ho_ten} - {self.phong.ten_phong}'

    # ==============================================
    # KIỂM TRA HỢP ĐỒNG TRÙNG PHÒNG
    # ==============================================

    def clean(self):
        super().clean()
        if self.ngay_bat_dau and self.ngay_ket_thuc and self.ngay_ket_thuc < self.ngay_bat_dau:
            raise ValidationError({'ngay_ket_thuc': 'Ngày kết thúc không được nhỏ hơn ngày bắt đầu.'})
        if not self.phong_id or self.trang_thai != 'hieu_luc':
            return
        if Phong.objects.filter(pk=self.phong_id, trang_thai='bao_tri').exists():
            raise ValidationError('Phòng đang bảo trì, không thể tạo hợp đồng hiệu lực.')
        if HopDong.objects.filter(phong_id=self.phong_id, trang_thai='hieu_luc').exclude(pk=self.pk).exists():
            raise ValidationError('Phòng này đã có hợp đồng đang hiệu lực.')

    @transaction.atomic
    def save(self, *args, **kwargs):
        phong_cu = None
        if self.pk:
            phong_cu = HopDong.objects.filter(pk=self.pk).values_list('phong_id', flat=True).first()
        ids = {pk for pk in (phong_cu, self.phong_id) if pk is not None}
        list(Phong.objects.select_for_update().filter(pk__in=ids).order_by('pk'))
        self.clean()
        super().save(*args, **kwargs)
        for pk in ids:
            dong_bo_trang_thai_phong(pk)


def dong_bo_trang_thai_phong(phong_id):
    if HopDong.objects.filter(phong_id=phong_id, trang_thai='hieu_luc').exists():
        Phong.objects.filter(pk=phong_id).update(trang_thai='dang_thue')
    else:
        Phong.objects.filter(pk=phong_id, trang_thai='dang_thue').update(trang_thai='trong')


@receiver(post_delete, sender=HopDong)
def dong_bo_khi_xoa_hop_dong(sender, instance, **kwargs):
    dong_bo_trang_thai_phong(instance.phong_id)


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

    ghi_chu = models.TextField(blank=True, null=True)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Điện nước'
        verbose_name_plural = 'Điện nước'

    def tien_dien(self):
        so_dien = max(
            0, self.chi_so_dien_moi - self.chi_so_dien_cu
        )
        return so_dien * self.don_gia_dien

    def tien_nuoc(self):
        so_nuoc = max(
            0, self.chi_so_nuoc_moi - self.chi_so_nuoc_cu
        )
        return so_nuoc * self.don_gia_nuoc

    
    
def save(self, *args, **kwargs):
    # Lấy chỉ số điện nước của tháng trước cùng phòng
    dien_nuoc_truoc = DienNuoc.objects.filter(
        phong=self.phong,
        thang__lt=self.thang
    ).exclude(
        pk=self.pk
    ).order_by('-thang').first()

    if dien_nuoc_truoc:
        self.chi_so_dien_cu = dien_nuoc_truoc.chi_so_dien_moi
        self.chi_so_nuoc_cu = dien_nuoc_truoc.chi_so_nuoc_moi
    else:
        self.chi_so_dien_cu = 0
        self.chi_so_nuoc_cu = 0

    # Lưu thông tin điện nước
    super().save(*args, **kwargs)

    # Tạo hoặc cập nhật thanh toán
    thanh_toan, created = ThanhToan.objects.get_or_create(
        phong=self.phong,
        thang=self.thang,
        defaults={
            'tien_phong': self.phong.gia_phong,
            'tien_dien': self.tien_dien(),
            'tien_nuoc': self.tien_nuoc(),
        }
    )

    if not created:
        thanh_toan.tien_phong = self.phong.gia_phong
        thanh_toan.tien_dien = self.tien_dien()
        thanh_toan.tien_nuoc = self.tien_nuoc()
        thanh_toan.save()



    def __str__(self):
        return f'{self.phong.ten_phong} - {self.thang.strftime("%d/%m/%Y")}'


class ThanhToan(models.Model):
    TRANG_THAI_CHOICES = [
        ('chua_thanh_toan', 'Chưa thanh toán'),
        ('cho_xac_nhan', 'Chờ xác nhận'),
        ('yeu_cau_bo_sung', 'Yêu cầu bổ sung'),
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

    # Hóa đơn chuyển khoản do người thuê tải lên
    hoa_don = models.FileField(
        upload_to='hoa_don_thanh_toan/',
        blank=True,
        null=True,
        verbose_name='Hóa đơn chuyển khoản'
    )

    # Ngày người thuê gửi hóa đơn
    ngay_gui_hoa_don = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Ngày gửi hóa đơn'
    )

    # Số tiền Admin đã xác minh thực nhận
    so_tien_da_nhan = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name='Số tiền đã xác minh'
    )

    # Lý do Admin yêu cầu thanh toán bổ sung
    ly_do_bo_sung = models.TextField(
        blank=True,
        null=True,
        verbose_name='Lý do yêu cầu bổ sung'
    )

    # Admin xác nhận
    nguoi_duyet = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='thanh_toan_da_duyet',
        verbose_name='Người duyệt thanh toán'
    )

    class Meta:
        verbose_name = 'Thanh toán'
        verbose_name_plural = 'Thanh toán'

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
        return f'{self.phong.ten_phong} - {self.thang.strftime("%d/%m/%Y")}'

class TaiKhoan(models.Model):
    VAI_TRO_CHOICES = [
        ('chu_tro', 'Chủ trọ'),
        ('nguoi_thue', 'Người thuê'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='tai_khoan',
        verbose_name='Người dùng'
    )

    vai_tro = models.CharField(
        max_length=20,
        choices=VAI_TRO_CHOICES,
        verbose_name='Vai trò'
    )

    so_dien_thoai = models.CharField(
        max_length=15,
        blank=True,
        verbose_name='Số điện thoại'
    )

    class Meta:
        verbose_name = 'Tài khoản'
        verbose_name_plural = 'Tài khoản'
        
    def __str__(self):
        return f'{self.user.username} - {self.get_vai_tro_display()}'

class ThongBao(models.Model):
    LOAI_THONG_BAO_CHOICES = [
        ('tien_phong', 'Tiền phòng'),
        ('dien_nuoc', 'Điện nước'),
        ('thanh_toan', 'Thanh toán'),
        ('hop_dong', 'Hợp đồng'),
        ('thong_bao_chung', 'Thông báo chung'),
        ('khac', 'Khác'),
    ]

    nguoi_thue = models.ForeignKey(
        NguoiThue,
        on_delete=models.CASCADE,
        related_name='thong_bao',
        verbose_name='Người nhận'
    )

    tieu_de = models.CharField(
        max_length=200,
        verbose_name='Tiêu đề'
    )

    noi_dung = models.TextField(
        verbose_name='Nội dung'
    )

    loai = models.CharField(
        max_length=30,
        choices=LOAI_THONG_BAO_CHOICES,
        default='thong_bao_chung',
        verbose_name='Loại thông báo'
    )

    da_doc = models.BooleanField(
        default=False,
        verbose_name='Đã đọc'
    )

    ngay_tao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )

    class Meta:
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo'
        ordering = ['-ngay_tao']

    def __str__(self):
        return f'{self.tieu_de} - {self.nguoi_thue.ho_ten}'

# =====================================================
# CẢNH BÁO HỢP ĐỒNG SẮP HẾT HẠN DÀNH CHO ADMIN
# =====================================================
class ThongBaoAdmin(models.Model):
    hop_dong = models.ForeignKey(
        'HopDong', on_delete=models.CASCADE, related_name='canh_bao_admin'
    )
    ngay_het_han = models.DateField()
    tieu_de = models.CharField(max_length=200)
    noi_dung = models.TextField()
    da_doc = models.BooleanField(default=False)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cảnh báo Admin'
        verbose_name_plural = 'Cảnh báo Admin'
        ordering = ('-ngay_tao',)
        constraints = [
            models.UniqueConstraint(
                fields=('hop_dong', 'ngay_het_han'),
                name='unique_canh_bao_hop_dong'
            )
        ]

    def __str__(self):
        return self.tieu_de

