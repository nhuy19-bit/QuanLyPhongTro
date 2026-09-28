from django.contrib import admin
from .models import (
    Phong,
    NguoiThue,
    HopDong,
    DienNuoc,
    ThanhToan,
    TaiKhoan,
)


@admin.register(Phong)
class PhongAdmin(admin.ModelAdmin):
    list_display = (
        'ten_phong',
        'gia_phong',
        'dien_tich',
        'trang_thai',
        'ngay_tao',
    )
    list_filter = ('trang_thai',)
    search_fields = ('ten_phong',)


@admin.register(NguoiThue)
class NguoiThueAdmin(admin.ModelAdmin):
    list_display = (
        'ho_ten',
        'so_cccd',
        'so_dien_thoai',
        'email',
        'ngay_tao',
    )
    search_fields = (
        'ho_ten',
        'so_cccd',
        'so_dien_thoai',
    )


@admin.register(HopDong)
class HopDongAdmin(admin.ModelAdmin):
    list_display = (
        'phong',
        'nguoi_thue',
        'ngay_bat_dau',
        'ngay_ket_thuc',
        'tien_coc',
        'trang_thai',
    )
    list_filter = ('trang_thai',)
    search_fields = (
        'phong__ten_phong',
        'nguoi_thue__ho_ten',
    )


@admin.register(DienNuoc)
class DienNuocAdmin(admin.ModelAdmin):
    list_display = (
        'phong',
        'thang',
        'chi_so_dien_cu',
        'chi_so_dien_moi',
        'chi_so_nuoc_cu',
        'chi_so_nuoc_moi',
    )
    list_filter = ('thang',)


@admin.register(ThanhToan)
class ThanhToanAdmin(admin.ModelAdmin):
    list_display = (
        'phong',
        'thang',
        'tien_phong',
        'tien_dien',
        'tien_nuoc',
        'tong_tien',
        'trang_thai',
    )
    list_filter = ('trang_thai', 'thang')
    search_fields = ('phong__ten_phong',)

@admin.register(TaiKhoan)
class TaiKhoanAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'vai_tro',
        'so_dien_thoai',
    )

    list_filter = ('vai_tro',)

    search_fields = (
        'user__username',
        'user__email',
        'so_dien_thoai',
    )