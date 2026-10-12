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
        'hien_thi_trang_thai',
        'mo_ta',
        'ngay_tao',
    )

    list_filter = (
        'trang_thai',
    )

    search_fields = (
        'ten_phong',
        'mo_ta',
    )

    ordering = (
        'ten_phong',
    )

    @admin.display(
        description='Trạng thái',
        ordering='trang_thai'
    )
    def hien_thi_trang_thai(self, obj):
        return obj.get_trang_thai_display()
    list_display = (
        'ten_phong',
        'gia_phong_hien_thi',
        'dien_tich',
        'trang_thai',
        'mo_ta_hien_thi',
        'ngay_tao',
    )

    list_filter = (
        'trang_thai',
    )

    search_fields = (
        'ten_phong',
        'mo_ta',
    )

    ordering = (
        '-ngay_tao',
    )

    @admin.display(description='Giá phòng')
    def gia_phong_hien_thi(self, obj):
        return f'{obj.gia_phong:,.0f} VNĐ'

    @admin.display(description='Mô tả')
    def mo_ta_hien_thi(self, obj):
        if not obj.mo_ta:
            return 'Chưa có mô tả'

        if len(obj.mo_ta) > 40:
            return obj.mo_ta[:40] + '...'

        return obj.mo_ta


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
        'email',
    )

    ordering = (
        '-ngay_tao',
    )


@admin.register(HopDong)
class HopDongAdmin(admin.ModelAdmin):
    list_display = (
        'phong',
        'nguoi_thue',
        'ngay_bat_dau',
        'ngay_ket_thuc',
        'tien_coc_hien_thi',
        'trang_thai',
    )

    list_filter = (
        'trang_thai',
    )

    search_fields = (
        'phong__ten_phong',
        'nguoi_thue__ho_ten',
        'nguoi_thue__so_cccd',
    )

    ordering = (
        '-ngay_bat_dau',
    )

    @admin.display(description='Tiền cọc')
    def tien_coc_hien_thi(self, obj):
        return f'{obj.tien_coc:,.0f} VNĐ'


@admin.register(DienNuoc)
class DienNuocAdmin(admin.ModelAdmin):
    list_display = (
        'phong',
        'thang',
        'chi_so_dien_cu',
        'chi_so_dien_moi',
        'so_dien_su_dung',
        'tien_dien_hien_thi',
        'chi_so_nuoc_cu',
        'chi_so_nuoc_moi',
        'so_nuoc_su_dung',
        'tien_nuoc_hien_thi',
    )

    list_filter = (
        'thang',
    )

    search_fields = (
        'phong__ten_phong',
    )

    ordering = (
        '-thang',
    )

    @admin.display(description='Số điện sử dụng')
    def so_dien_su_dung(self, obj):
        return max(
            0,
            obj.chi_so_dien_moi - obj.chi_so_dien_cu
        )

    @admin.display(description='Tiền điện')
    def tien_dien_hien_thi(self, obj):
        return f'{obj.tien_dien():,.0f} VNĐ'

    @admin.display(description='Số nước sử dụng')
    def so_nuoc_su_dung(self, obj):
        return max(
            0,
            obj.chi_so_nuoc_moi - obj.chi_so_nuoc_cu
        )

    @admin.display(description='Tiền nước')
    def tien_nuoc_hien_thi(self, obj):
        return f'{obj.tien_nuoc():,.0f} VNĐ'


@admin.register(ThanhToan)
class ThanhToanAdmin(admin.ModelAdmin):
    list_display = (
        'phong',
        'thang',
        'tien_phong_hien_thi',
        'tien_dien_hien_thi',
        'tien_nuoc_hien_thi',
        'tien_khac_hien_thi',
        'tong_tien_hien_thi',
        'trang_thai',
        'ngay_thanh_toan',
    )

    list_filter = (
        'trang_thai',
        'thang',
    )

    search_fields = (
        'phong__ten_phong',
    )

    ordering = (
        '-thang',
    )

    @admin.display(description='Tiền phòng')
    def tien_phong_hien_thi(self, obj):
        return f'{obj.tien_phong:,.0f} VNĐ'

    @admin.display(description='Tiền điện')
    def tien_dien_hien_thi(self, obj):
        return f'{obj.tien_dien:,.0f} VNĐ'

    @admin.display(description='Tiền nước')
    def tien_nuoc_hien_thi(self, obj):
        return f'{obj.tien_nuoc:,.0f} VNĐ'

    @admin.display(description='Tiền khác')
    def tien_khac_hien_thi(self, obj):
        return f'{obj.tien_khac:,.0f} VNĐ'

    @admin.display(description='Tổng tiền')
    def tong_tien_hien_thi(self, obj):
        return f'{obj.tong_tien:,.0f} VNĐ'


@admin.register(TaiKhoan)
class TaiKhoanAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'ho_ten_hien_thi',
        'email_hien_thi',
        'vai_tro',
        'so_dien_thoai',
    )

    list_filter = ('vai_tro',)

    search_fields = (
        'user__username',
        'user__email',
        'so_dien_thoai',
        'user__first_name',
        'user__last_name',
        'ho_so_nguoi_thue__ho_ten',
        'ho_so_nguoi_thue__email',
    )

    ordering = ('user__username',)

    @admin.display(description='Họ tên')
    def ho_ten_hien_thi(self, obj):
        try:
            return obj.ho_so_nguoi_thue.ho_ten
        except Exception:
            return obj.user.get_full_name() or 'Chưa cập nhật'

    @admin.display(description='Email')
    def email_hien_thi(self, obj):
        try:
            email = obj.ho_so_nguoi_thue.email
            if email:
                return email
        except Exception:
            pass

        return obj.user.email or 'Chưa cập nhật'


admin.site.site_header = "QUẢN LÝ PHÒNG TRỌ"
admin.site.site_title = "Quản lý phòng trọ"
admin.site.index_title = "Trang quản trị Chủ trọ"