from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    CoSo,
    Phong,
    NguoiThue,
    HopDong,
    DienNuoc,
    ThanhToan,
    TaiKhoan,
)


@admin.display(description='Ngày tạo', ordering='ngay_tao')
def ngay_tao_hien_thi(obj):
    return obj.ngay_tao.strftime('%d/%m/%Y %H:%M')


class PhongInline(admin.TabularInline):
    model = Phong
    extra = 0
    fields = (
        'ten_phong',
        'trang_thai',
    )


@admin.register(CoSo)
class CoSoAdmin(admin.ModelAdmin):
    change_list_template = 'admin/quanly/change_list.html'
    change_form_template = 'admin/quanly/coso/change_form.html'
    list_display = (
        'ten_co_so',
        'dia_chi',
        'so_phong',
        'ngay_tao_hien_thi',
    )
    search_fields = ('ten_co_so', 'dia_chi')
    ordering = ('ten_co_so',)

    @admin.display(description='Số phòng')
    def so_phong(self, obj):
        return obj.phong.count()

    @admin.display(description='Ngày tạo', ordering='ngay_tao')
    def ngay_tao_hien_thi(self, obj):
        return obj.ngay_tao.strftime('%d/%m/%Y %H:%M')


@admin.register(Phong)
class PhongAdmin(admin.ModelAdmin):
    change_list_template = 'admin/quanly/change_list.html'

    list_display = (
        'co_so',
        'ten_phong',
        'gia_phong',
        'dien_tich',
        'hien_thi_trang_thai',
        'mo_ta',
        'ngay_tao',
    )

    list_filter = (
        'co_so',
        'trang_thai',
    )

    search_fields = (
        'co_so__ten_co_so',
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
        'co_so',
        'ten_phong',
        'gia_phong_hien_thi',
        'dien_tich',
        'trang_thai',
        'mo_ta_hien_thi',
        ngay_tao_hien_thi,
    )

    list_filter = (
        'co_so',
        'trang_thai',
    )

    search_fields = (
        'co_so__ten_co_so',
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


class NguoiThueAdminForm(forms.ModelForm):
    tai_khoan = forms.ModelChoiceField(
        queryset=TaiKhoan.objects.none(),
        label='Tài khoản đăng nhập',
    )

    class Meta:
        model = NguoiThue
        exclude = ('tai_khoan',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = TaiKhoan.objects.filter(
            vai_tro='nguoi_thue',
            ho_so_nguoi_thue__isnull=True,
        ).select_related('user').order_by('so_dien_thoai')

        if self.instance.pk and self.instance.tai_khoan_id:
            queryset = TaiKhoan.objects.filter(
                Q(pk=self.instance.tai_khoan_id)
                | Q(
                    vai_tro='nguoi_thue',
                    ho_so_nguoi_thue__isnull=True,
                )
            ).select_related('user').order_by('so_dien_thoai')
            self.initial['tai_khoan'] = self.instance.tai_khoan_id

        self.fields['tai_khoan'].queryset = queryset

    def clean(self):
        cleaned_data = super().clean()
        tai_khoan = cleaned_data.get('tai_khoan')
        so_dien_thoai = cleaned_data.get('so_dien_thoai', '').strip()

        if tai_khoan and tai_khoan.so_dien_thoai != so_dien_thoai:
            self.add_error(
                'so_dien_thoai',
                'Số điện thoại phải trùng với tài khoản đã cấp.'
            )

        return cleaned_data

    def clean_so_dien_thoai(self):
        so_dien_thoai = self.cleaned_data['so_dien_thoai'].strip()

        if not so_dien_thoai:
            raise ValidationError('Số điện thoại là bắt buộc để cấp tài khoản.')

        return so_dien_thoai


@admin.register(NguoiThue)
class NguoiThueAdmin(admin.ModelAdmin):
    change_list_template = 'admin/quanly/change_list.html'
    form = NguoiThueAdminForm

    list_display = (
        'ho_ten',
        'so_cccd',
        'so_dien_thoai',
        'email',
        'phong_hien_thi',
        'dia_chi_co_so_hien_thi',
        ngay_tao_hien_thi,
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

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'hop_dong__phong__co_so'
        )

    def _hop_dong_hien_hanh(self, obj):
        return next(
            (
                hop_dong
                for hop_dong in obj.hop_dong.all()
                if hop_dong.trang_thai == 'hieu_luc'
            ),
            None,
        )

    @admin.display(description='Phòng')
    def phong_hien_thi(self, obj):
        hop_dong = self._hop_dong_hien_hanh(obj)
        return hop_dong.phong.ten_phong if hop_dong else 'Chưa thuê phòng'

    @admin.display(description='Địa chỉ cơ sở')
    def dia_chi_co_so_hien_thi(self, obj):
        hop_dong = self._hop_dong_hien_hanh(obj)
        if not hop_dong:
            return 'Chưa thuê phòng'
        if not hop_dong.phong.co_so:
            return 'Chưa gán cơ sở'
        return hop_dong.phong.co_so.dia_chi or 'Chưa cập nhật'

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        obj.tai_khoan = form.cleaned_data['tai_khoan']
        super().save_model(request, obj, form, change)

        tai_khoan = obj.tai_khoan
        user = tai_khoan.user
        user.email = obj.email or ''
        user.first_name = obj.ho_ten
        user.save(update_fields=['email', 'first_name'])


@admin.register(HopDong)
class HopDongAdmin(admin.ModelAdmin):
    change_list_template = 'admin/quanly/change_list.html'
    list_display = (
        'phong',
        'nguoi_thue',
        'ngay_bat_dau',
        'ngay_ket_thuc',
        'tien_coc_hien_thi',
        'trang_thai',
        ngay_tao_hien_thi,
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
    change_list_template = 'admin/quanly/change_list.html'
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
        ngay_tao_hien_thi,
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
    change_list_template = 'admin/quanly/change_list.html'
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
        ngay_tao_hien_thi,
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



class TaiKhoanAdminForm(forms.ModelForm):
    nguoi_thue = forms.ModelChoiceField(
        queryset=NguoiThue.objects.none(),
        required=False,
        label='Người thuê',
    )
    dang_hoat_dong = forms.BooleanField(
        label='Tài khoản đang hoạt động',
        required=False,
    )

    class Meta:
        model = TaiKhoan
        exclude = ('user',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = NguoiThue.objects.filter(tai_khoan__isnull=True)

        if self.instance.pk:
            current = NguoiThue.objects.filter(tai_khoan=self.instance).first()
            if current:
                queryset = NguoiThue.objects.filter(
                    pk__in=list(queryset.values_list('pk', flat=True))
                    + [current.pk]
                )
                self.initial['nguoi_thue'] = current.pk

        self.fields['nguoi_thue'].queryset = queryset.order_by('ho_ten')
        if self.instance.user_id:
            self.initial['dang_hoat_dong'] = self.instance.user.is_active

    def clean_so_dien_thoai(self):
        so_dien_thoai = self.cleaned_data['so_dien_thoai'].strip()

        if not so_dien_thoai:
            raise ValidationError('Số điện thoại là bắt buộc để đăng nhập.')

        user_query = User.objects.filter(username=so_dien_thoai)
        if self.instance.user_id:
            user_query = user_query.exclude(pk=self.instance.user_id)

        existing_user = user_query.first()
        if existing_user and hasattr(existing_user, 'tai_khoan'):
            raise ValidationError(
                'Số điện thoại này đã được sử dụng cho tài khoản khác.'
            )

        return so_dien_thoai


@admin.register(TaiKhoan)
class TaiKhoanAdmin(admin.ModelAdmin):
    change_list_template = 'admin/quanly/change_list.html'
    form = TaiKhoanAdminForm

    list_display = (
        'ten_dang_nhap_hien_thi',
        'ho_ten_hien_thi',
        'email_hien_thi',
        'vai_tro',
        'so_dien_thoai',
        'trang_thai_hien_thi',
        'ngay_tao_tai_khoan_hien_thi',
    )

    actions = ('khoa_tai_khoan', 'mo_tai_khoan')

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

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        nguoi_thue = form.cleaned_data.get('nguoi_thue')
        nguoi_thue_cu = None
        if obj.pk:
            nguoi_thue_cu = NguoiThue.objects.filter(
                tai_khoan_id=obj.pk
            ).first()

        if obj.user_id:
            user = obj.user
            user.username = obj.so_dien_thoai
            user.is_active = form.cleaned_data['dang_hoat_dong']
            if nguoi_thue:
                user.first_name = nguoi_thue.ho_ten
                user.email = nguoi_thue.email or ''
            user.set_password(obj.so_dien_thoai)
            user.save()
        else:
            user = User.objects.filter(
                username=obj.so_dien_thoai,
                is_staff=False,
                is_superuser=False,
            ).first()
            if user is None:
                user = User.objects.create_user(
                    username=obj.so_dien_thoai,
                    password=obj.so_dien_thoai,
                    first_name=nguoi_thue.ho_ten if nguoi_thue else '',
                    email=nguoi_thue.email if nguoi_thue else '',
                )
            else:
                user.set_password(obj.so_dien_thoai)
                user.save()

            obj.user = user

        obj.user.is_active = form.cleaned_data['dang_hoat_dong']
        obj.user.save(update_fields=['is_active'])
        super().save_model(request, obj, form, change)

        if nguoi_thue_cu and nguoi_thue_cu != nguoi_thue:
            nguoi_thue_cu.tai_khoan = None
            nguoi_thue_cu.save(update_fields=['tai_khoan'])

        if nguoi_thue and nguoi_thue.tai_khoan_id != obj.pk:
            nguoi_thue.tai_khoan = obj
            nguoi_thue.save(update_fields=['tai_khoan'])

    @admin.display(description='Trạng thái', ordering='user__is_active')
    def trang_thai_hien_thi(self, obj):
        return 'Đang hoạt động' if obj.user.is_active else 'Đã khóa'

    @admin.action(description='Khóa tài khoản đã chọn')
    def khoa_tai_khoan(self, request, queryset):
        user_ids = queryset.values_list('user_id', flat=True)
        updated = User.objects.filter(pk__in=user_ids).update(is_active=False)
        self.message_user(request, f'Đã khóa {updated} tài khoản.')

    @admin.action(description='Mở tài khoản đã chọn')
    def mo_tai_khoan(self, request, queryset):
        user_ids = queryset.values_list('user_id', flat=True)
        updated = User.objects.filter(pk__in=user_ids).update(is_active=True)
        self.message_user(request, f'Đã mở {updated} tài khoản.')

    @admin.display(description='Tài khoản')
    def ten_dang_nhap_hien_thi(self, obj):
        if obj.so_dien_thoai:
            return obj.so_dien_thoai
        return obj.user.username

    @admin.display(description='Ngày tạo', ordering='user__date_joined')
    def ngay_tao_tai_khoan_hien_thi(self, obj):
        return obj.user.date_joined.strftime('%d/%m/%Y %H:%M')

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