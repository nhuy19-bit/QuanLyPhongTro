from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from django.contrib.admin.views.main import ChangeList
from .models import (
    CoSo,
    Phong,
    NguoiThue,
    HopDong,
    DienNuoc,
    ThanhToan,
    TaiKhoan,
    ThongBao,
    dong_bo_trang_thai_phong,
)

class LocCoSoAdminMixin:
    co_so_filter_field = None
    ten_chuc_nang = ''

    def changelist_view(self, request, extra_context=None):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

        co_so_id = request.GET.get('co_so')

        # Chưa chọn cơ sở
        if not co_so_id:
            context = {
                **self.admin_site.each_context(request),
                'title': f'{self.ten_chuc_nang} theo cơ sở',
                'opts': self.model._meta,
                'co_so_list': CoSo.objects.all().order_by('ten_co_so'),
                'tieu_de': f'{self.ten_chuc_nang} theo cơ sở',
                'ten_chuc_nang': self.ten_chuc_nang.lower(),
            }

            return TemplateResponse(
                request,
                'admin/quanly/thanhtoan/co_so_list.html',
                context,
            )

        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        co_so_id = request.GET.get('co_so')

        if not co_so_id or not self.co_so_filter_field:
            return queryset

        if not co_so_id.isdigit():
            return queryset.none()

        # Người thuê
        if self.model == NguoiThue:
            return queryset.filter(
                hop_dong__phong__co_so_id=co_so_id,
                hop_dong__trang_thai='hieu_luc'
            ).distinct()

        # Tài khoản
        if self.model == TaiKhoan:
            return queryset.filter(
                ho_so_nguoi_thue__hop_dong__phong__co_so_id=co_so_id,
                ho_so_nguoi_thue__hop_dong__trang_thai='hieu_luc'
            ).distinct()

        # Thông báo
        if self.model == ThongBao:
            return queryset.filter(
                nguoi_thue__hop_dong__phong__co_so_id=co_so_id,
                nguoi_thue__hop_dong__trang_thai='hieu_luc'
            ).distinct()

        # Hợp đồng, Điện nước, Thanh toán
        return queryset.filter(
            **{self.co_so_filter_field: co_so_id}
        ).distinct()


def dinh_dang_tien(gia_tri):
    return f'{gia_tri:,.0f}VNĐ'


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

    # Ẩn trường mô tả khi thêm và sửa cơ sở
    exclude = ('mo_ta',)

    list_display = (
        'ten_co_so_link',
        'dia_chi_hien_thi',
        'so_phong',
        'ngay_tao_hien_thi',
    )

    search_fields = ('ten_co_so', 'dia_chi')
    ordering = ('ten_co_so',)

    @admin.display(description='Tên cơ sở', ordering='ten_co_so')
    def ten_co_so_link(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse

        url = (
            reverse('admin:quanly_phong_changelist')
            + f'?co_so__id__exact={obj.pk}'
        )

        return format_html('<a href="{}">{}</a>', url, obj.ten_co_so)

    @admin.display(description='Địa chỉ', ordering='dia_chi')
    def dia_chi_hien_thi(self, obj):
        return obj.dia_chi

    @admin.display(description='Số phòng')
    def so_phong(self, obj):
        return obj.phong.count()

    @admin.display(description='Ngày tạo', ordering='ngay_tao')
    def ngay_tao_hien_thi(self, obj):
        return obj.ngay_tao.strftime('%d/%m/%Y %H:%M')



class HopDongInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        active = [f for f in self.forms if f.cleaned_data
                  and not f.cleaned_data.get('DELETE')
                  and f.cleaned_data.get('trang_thai') == 'hieu_luc']
        if len(active) > 1:
            raise ValidationError('Mỗi phòng chỉ được có một hợp đồng hiệu lực.')
        if active and self.instance.trang_thai == 'bao_tri':
            raise ValidationError('Phòng đang bảo trì, không thể tạo hợp đồng hiệu lực.')


@admin.register(Phong)
class PhongAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('admin/quanly/phong/inline-forms.css',)
        }
    class DienNuocInline(admin.StackedInline):
        model = DienNuoc
        extra = 0
        template = 'admin/quanly/diennuoc/stacked.html'
        show_change_link = True

        class Media:
            css = {
                'all': ('admin/quanly/diennuoc/inline.css',)
            }
            js = (
                'admin/quanly/diennuoc/tu_dong_chi_so_cu.js',
            )

        fields = (
            'thang',
            'chi_so_dien_cu',
            'chi_so_dien_moi',
            'chi_so_nuoc_cu',
            'chi_so_nuoc_moi',
            'don_gia_dien',
            'don_gia_nuoc',
        )

    class ThanhToanInline(admin.StackedInline):
        model = ThanhToan
        extra = 0
        template = 'admin/quanly/thanhtoan/stacked.html'
        show_change_link = True
        fields = (
            'thang',
            'tien_phong',
            'tien_dien',
            'tien_nuoc',
            'tien_khac',
            'tong_tien',
            'trang_thai',
        )
        readonly_fields = ('tong_tien',)

    class HopDongInline(admin.StackedInline):
        model = HopDong
        formset = HopDongInlineFormSet
        extra = 0
        template = 'admin/quanly/hopdong/stacked.html'
        show_change_link = True
        fields = (
            'nguoi_thue',
            'ngay_bat_dau',
            'ngay_ket_thuc',
            'tien_coc',
            'trang_thai',
        )

    # Hiển thị các mục liên quan khi mở chi tiết phòng
    inlines = [DienNuocInline, ThanhToanInline, HopDongInline]

    change_list_template = 'admin/quanly/change_list.html'

    list_display = (
        'co_so_hien_thi',
        'ten_phong_hien_thi',
        'gia_phong_hien_thi',
        'dien_tich_hien_thi',
        'hien_thi_trang_thai',
        'mo_ta_hien_thi',
        'ngay_tao_hien_thi',
    )

    list_filter = ('co_so', 'trang_thai')

    search_fields = (
        'co_so__ten_co_so',
        'ten_phong',
        'mo_ta',
    )

    ordering = ('-ngay_tao',)

    @admin.display(description='Cơ sở', ordering='co_so')
    def co_so_hien_thi(self, obj):
        return str(obj.co_so) if obj.co_so else '-'

    @admin.display(description='Tên phòng', ordering='ten_phong')
    def ten_phong_hien_thi(self, obj):
        return obj.ten_phong

    @admin.display(description='Diện tích', ordering='dien_tich')
    def dien_tich_hien_thi(self, obj):
        dien_tich = f'{obj.dien_tich:f}'.rstrip('0').rstrip('.')
        return f'{dien_tich} m²'

    @admin.display(description='Trạng thái', ordering='trang_thai')
    def hien_thi_trang_thai(self, obj):
        return obj.get_trang_thai_display()

    @admin.display(description='Giá phòng', ordering='gia_phong')
    def gia_phong_hien_thi(self, obj):
        return dinh_dang_tien(obj.gia_phong)

    @admin.display(description='Mô tả')
    def mo_ta_hien_thi(self, obj):
        if not obj.mo_ta:
            return 'Chưa có mô tả'
        if len(obj.mo_ta) > 40:
            return obj.mo_ta[:40] + '...'
        return obj.mo_ta

    @admin.display(description='Ngày tạo', ordering='ngay_tao')
    def ngay_tao_hien_thi(self, obj):
        return obj.ngay_tao.strftime('%d/%m/%Y %H:%M')
    def save_related(self, request, form, formsets, change):
        # Lưu Điện nước, Thanh toán và Hợp đồng trước
        super().save_related(request, form, formsets, change)

        phong = form.instance
        dong_bo_trang_thai_phong(phong.pk)
        phong.refresh_from_db(fields=['trang_thai'])

        # Duyệt danh sách điện nước của phòng
        for dn in DienNuoc.objects.filter(phong=phong):
            # Tìm hoặc tạo thanh toán cùng phòng, cùng tháng
            thanh_toan, created = ThanhToan.objects.get_or_create(
                phong=phong,
                thang=dn.thang,
                defaults={
                    'tien_phong': phong.gia_phong,
                    'tien_dien': dn.tien_dien(),
                    'tien_nuoc': dn.tien_nuoc(),
                }
            )

            # Cập nhật tiền phòng, điện, nước
            thanh_toan.tien_phong = phong.gia_phong
            thanh_toan.tien_dien = dn.tien_dien()
            thanh_toan.tien_nuoc = dn.tien_nuoc()

            # Lưu để tự tính lại tổng tiền
            thanh_toan.save()


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


# =====================================================
# BỘ LỌC NGƯỜI THUÊ THEO CƠ SỞ
# =====================================================

class NguoiThueCoSoFilter(admin.SimpleListFilter):
    title = 'Cơ sở'
    parameter_name = 'co_so'

    def lookups(self, request, model_admin):
        return [
            (str(cs.pk), cs.ten_co_so)
            for cs in CoSo.objects.all().order_by('ten_co_so')
        ]

    def queryset(self, request, queryset):
        co_so_id = self.value()

        if co_so_id:
            return queryset.filter(
                hop_dong__phong__co_so_id=co_so_id,
                hop_dong__trang_thai='hieu_luc',
            ).distinct()

        return queryset


# =====================================================
# QUẢN LÝ NGƯỜI THUÊ
# =====================================================

@admin.register(NguoiThue)
class NguoiThueAdmin(admin.ModelAdmin):

    ten_chuc_nang = 'Người thuê'
    co_so_filter_field = 'hop_dong__phong__co_so_id'

    change_list_template = 'admin/quanly/change_list.html'
    form = NguoiThueAdminForm

    # =================================================
    # CỘT HIỂN THỊ
    # =================================================

    list_display = (
        'ho_ten_hien_thi',
        'so_cccd_hien_thi',
        'so_dien_thoai_hien_thi',
        'email',
        'phong_hien_thi',
        'dia_chi_co_so_hien_thi',
        ngay_tao_hien_thi,
    )

    # =================================================
    # BỘ LỌC
    # =================================================

    list_filter = (
        NguoiThueCoSoFilter,
    )

    # =================================================
    # TÌM KIẾM
    # =================================================

    search_fields = (
        'ho_ten',
        'so_cccd',
        'so_dien_thoai',
        'email',
    )

    ordering = (
        '-ngay_tao',
    )

    # =================================================
    # HIỂN THỊ DANH SÁCH CƠ SỞ TRƯỚC
    # =================================================


    # =================================================
    # LẤY DANH SÁCH NGƯỜI THUÊ
    # =================================================

    def get_queryset(self, request):

        return super().get_queryset(request).prefetch_related(
            'hop_dong__phong__co_so'
        )

    # =================================================
    # LẤY HỢP ĐỒNG HIỆN HÀNH
    # =================================================

    def _hop_dong_hien_hanh(self, obj):

        return next(
            (
                hop_dong
                for hop_dong in obj.hop_dong.all()
                if hop_dong.trang_thai == 'hieu_luc'
            ),
            None,
        )

    # =================================================
    # HIỂN THỊ HỌ TÊN
    # =================================================

    @admin.display(
        description='Họ tên',
        ordering='ho_ten',
    )
    def ho_ten_hien_thi(self, obj):
        return obj.ho_ten

    # =================================================
    # HIỂN THỊ CCCD
    # =================================================

    @admin.display(
        description='Số CCCD',
        ordering='so_cccd',
    )
    def so_cccd_hien_thi(self, obj):
        return obj.so_cccd

    # =================================================
    # HIỂN THỊ SỐ ĐIỆN THOẠI
    # =================================================

    @admin.display(
        description='Số điện thoại',
        ordering='so_dien_thoai',
    )
    def so_dien_thoai_hien_thi(self, obj):
        return obj.so_dien_thoai

    # =================================================
    # HIỂN THỊ PHÒNG
    # =================================================

    @admin.display(description='Phòng')
    def phong_hien_thi(self, obj):

        hop_dong = self._hop_dong_hien_hanh(obj)

        if hop_dong:
            return hop_dong.phong.ten_phong

        return 'Chưa thuê phòng'

    # =================================================
    # HIỂN THỊ ĐỊA CHỈ CƠ SỞ
    # =================================================

    @admin.display(description='Địa chỉ cơ sở')
    def dia_chi_co_so_hien_thi(self, obj):

        hop_dong = self._hop_dong_hien_hanh(obj)

        if not hop_dong:
            return 'Chưa thuê phòng'

        if not hop_dong.phong.co_so:
            return 'Chưa gán cơ sở'

        return (
            hop_dong.phong.co_so.dia_chi
            or 'Chưa cập nhật'
        )

    # =================================================
    # LƯU NGƯỜI THUÊ
    # =================================================

    @transaction.atomic
    def save_model(self, request, obj, form, change):

        obj.tai_khoan = form.cleaned_data['tai_khoan']

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        tai_khoan = obj.tai_khoan
        user = tai_khoan.user

        user.email = obj.email or ''
        user.first_name = obj.ho_ten

        user.save(
            update_fields=[
                'email',
                'first_name',
            ]
        )


# =====================================================
# BỘ LỌC HỢP ĐỒNG THEO CƠ SỞ
# =====================================================

class HopDongCoSoFilter(admin.SimpleListFilter):
    title = 'Cơ sở'
    parameter_name = 'co_so'

    def lookups(self, request, model_admin):
        return [
            (str(cs.pk), cs.ten_co_so)
            for cs in CoSo.objects.all().order_by('ten_co_so')
        ]

    def queryset(self, request, queryset):
        co_so_id = self.value()

        if co_so_id:
            return queryset.filter(
                phong__co_so_id=co_so_id
            )

        return queryset


# =====================================================
# QUẢN LÝ HỢP ĐỒNG THEO CƠ SỞ
# =====================================================

# HỢP ĐỒNG
@admin.register(HopDong)
class HopDongAdmin(admin.ModelAdmin):
    ten_chuc_nang = 'Hợp đồng'
    co_so_filter_field = 'phong__co_so_id'

    change_list_template = 'admin/quanly/change_list.html'

    # CÁC CỘT HIỂN THỊ
    list_display = (
        'phong_hien_thi',
        'nguoi_thue_hien_thi',
        'ngay_bat_dau_hien_thi',
        'ngay_ket_thuc_hien_thi',
        'tien_coc_hien_thi',
        'trang_thai_hien_thi',
        ngay_tao_hien_thi,
    )

    # BỘ LỌC
    list_filter = (
        HopDongCoSoFilter,
        'trang_thai',
    )

    # TÌM KIẾM
    search_fields = (
        'phong__ten_phong',
        'nguoi_thue__ho_ten',
        'nguoi_thue__so_cccd',
    )

    ordering = (
        '-ngay_bat_dau',
    )

    readonly_fields = ('xuat_pdf',)

    # =================================================
    # HIỂN THỊ DANH SÁCH CƠ SỞ TRƯỚC
    # =================================================


    # =================================================
    # TỐI ƯU TRUY VẤN DỮ LIỆU
    # =================================================

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'phong',
            'phong__co_so',
            'nguoi_thue',
        )

    # =================================================
    # HIỂN THỊ PHÒNG
    # =================================================

    @admin.display(
        description='Phòng',
        ordering='phong',
    )
    def phong_hien_thi(self, obj):
        return str(obj.phong)

    # =================================================
    # HIỂN THỊ NGƯỜI THUÊ
    # =================================================

    @admin.display(
        description='Người thuê',
        ordering='nguoi_thue',
    )
    def nguoi_thue_hien_thi(self, obj):
        return str(obj.nguoi_thue)

    # =================================================
    # HIỂN THỊ NGÀY BẮT ĐẦU
    # =================================================

    @admin.display(
        description='Ngày bắt đầu',
        ordering='ngay_bat_dau',
    )
    def ngay_bat_dau_hien_thi(self, obj):
        return obj.ngay_bat_dau.strftime('%d/%m/%Y')

    # =================================================
    # HIỂN THỊ NGÀY KẾT THÚC
    # =================================================

    @admin.display(
        description='Ngày kết thúc',
        ordering='ngay_ket_thuc',
    )
    def ngay_ket_thuc_hien_thi(self, obj):
        return (
            obj.ngay_ket_thuc.strftime('%d/%m/%Y')
            if obj.ngay_ket_thuc
            else '-'
        )

    # =================================================
    # XUẤT HỢP ĐỒNG PDF
    # =================================================

    @admin.display(description='Xuất hợp đồng PDF')
    def xuat_pdf(self, obj):

        if not obj or not obj.pk:
            return 'Lưu hợp đồng trước để xuất PDF.'

        from django.urls import reverse
        from django.utils.html import format_html

        url = reverse('hopdong_pdf', args=[obj.pk])

        return format_html(
            '<a href="{}" target="_blank" rel="noopener">'
            '📄 Xem / Xuất PDF</a>',
            url,
        )

    # =================================================
    # HIỂN THỊ TIỀN CỌC
    # =================================================

    @admin.display(description='Tiền cọc')
    def tien_coc_hien_thi(self, obj):
        return dinh_dang_tien(obj.tien_coc)

    # =================================================
    # HIỂN THỊ TRẠNG THÁI
    # =================================================

    @admin.display(
        description='Trạng thái',
        ordering='trang_thai',
    )
    def trang_thai_hien_thi(self, obj):
        return obj.get_trang_thai_display()

# =====================================================
# BỘ LỌC ĐIỆN NƯỚC THEO CƠ SỞ
# =====================================================

class DienNuocCoSoFilter(admin.SimpleListFilter):
    title = 'Cơ sở'
    parameter_name = 'co_so'

    def lookups(self, request, model_admin):
        return [
            (str(cs.pk), cs.ten_co_so)
            for cs in CoSo.objects.all().order_by('ten_co_so')
        ]

    def queryset(self, request, queryset):
        co_so_id = self.value()

        if co_so_id:
            return queryset.filter(
                phong__co_so_id=co_so_id
            )

        return queryset


# =====================================================
# QUẢN LÝ ĐIỆN NƯỚC THEO CƠ SỞ
# =====================================================

# ĐIỆN NƯỚC
@admin.register(DienNuoc)
class DienNuocAdmin(admin.ModelAdmin):
    ten_chuc_nang = 'Điện nước'
    co_so_filter_field = 'phong__co_so_id'

    change_list_template = 'admin/quanly/change_list.html'

    # CÁC CỘT HIỂN THỊ
    list_display = (
        'phong_hien_thi',
        'thang_hien_thi',
        'so_dien_su_dung',
        'tien_dien_hien_thi',
        'so_nuoc_su_dung',
        'tien_nuoc_hien_thi',
        ngay_tao_hien_thi,
    )

    # BỘ LỌC
    list_filter = (
        DienNuocCoSoFilter,
    )

    # TÌM KIẾM
    search_fields = (
        'phong__ten_phong',
    )

    ordering = (
        '-thang',
    )

    # =================================================
    # HIỂN THỊ DANH SÁCH CƠ SỞ TRƯỚC
    # =================================================


    # =================================================
    # LẤY DỮ LIỆU ĐIỆN NƯỚC
    # =================================================

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'phong',
            'phong__co_so',
        )

    # =================================================
    # HIỂN THỊ PHÒNG
    # =================================================

    @admin.display(description='Phòng', ordering='phong')
    def phong_hien_thi(self, obj):
        return str(obj.phong)

    # =================================================
    # HIỂN THỊ THÁNG
    # =================================================

    @admin.display(description='Tháng', ordering='thang')
    def thang_hien_thi(self, obj):
        return obj.thang.strftime('%d/%m/%Y')

    # =================================================
    # SỐ ĐIỆN SỬ DỤNG
    # =================================================

    @admin.display(description='Số điện sử dụng')
    def so_dien_su_dung(self, obj):
        so_dien = max(
            0,
            obj.chi_so_dien_moi - obj.chi_so_dien_cu
        )
        return f'{so_dien} kWh'

    # =================================================
    # TIỀN ĐIỆN
    # =================================================

    @admin.display(description='Tiền điện')
    def tien_dien_hien_thi(self, obj):
        return dinh_dang_tien(obj.tien_dien())

    # =================================================
    # SỐ NƯỚC SỬ DỤNG
    # =================================================

    @admin.display(description='Số nước sử dụng')
    def so_nuoc_su_dung(self, obj):
        so_nuoc = max(
            0,
            obj.chi_so_nuoc_moi - obj.chi_so_nuoc_cu
        )
        return f'{so_nuoc} m³'

    # =================================================
    # TIỀN NƯỚC
    # =================================================

    @admin.display(description='Tiền nước')
    def tien_nuoc_hien_thi(self, obj):
        return dinh_dang_tien(obj.tien_nuoc())


# ==========================================================
# QUẢN LÝ THANH TOÁN - KIỂM TRA VÀ DUYỆT HÓA ĐƠN
# ==========================================================

class ThanhToanAdminForm(forms.ModelForm):
    class Meta:
        model = ThanhToan
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()

        trang_thai = cleaned_data.get('trang_thai')
        so_tien_da_nhan = cleaned_data.get('so_tien_da_nhan')
        ly_do = cleaned_data.get('ly_do_bo_sung')

        tien_phong = cleaned_data.get('tien_phong')
        tien_dien = cleaned_data.get('tien_dien')
        tien_nuoc = cleaned_data.get('tien_nuoc')
        tien_khac = cleaned_data.get('tien_khac')

        if all(
            value is not None
            for value in (
                tien_phong,
                tien_dien,
                tien_nuoc,
                tien_khac,
            )
        ):
            tong_tien = (
                tien_phong
                + tien_dien
                + tien_nuoc
                + tien_khac
            )

            if (
                trang_thai == 'da_thanh_toan'
                and so_tien_da_nhan is not None
                and so_tien_da_nhan < tong_tien
            ):
                self.add_error(
                    'so_tien_da_nhan',
                    'Số tiền thực nhận chưa đủ để duyệt thanh toán.'
                )

        if (
            trang_thai == 'yeu_cau_bo_sung'
            and not (ly_do or '').strip()
        ):
            self.add_error(
                'ly_do_bo_sung',
                'Vui lòng nhập lý do yêu cầu bổ sung.'
            )

        return cleaned_data


# ==========================================================
# BỘ LỌC THANH TOÁN THEO CƠ SỞ
# ==========================================================

class CoSoThanhToanFilter(admin.SimpleListFilter):
    title = 'Cơ sở'
    parameter_name = 'co_so'

    def lookups(self, request, model_admin):
        return [
            (str(cs.pk), cs.ten_co_so)
            for cs in CoSo.objects.all().order_by('ten_co_so')
        ]

    def queryset(self, request, queryset):
        co_so_id = self.value()

        if co_so_id:
            return queryset.filter(
                phong__co_so_id=co_so_id
            )

        return queryset


# ==========================================================
# QUẢN LÝ THANH TOÁN
# ==========================================================

@admin.register(ThanhToan)
class ThanhToanAdmin(admin.ModelAdmin):

    form = ThanhToanAdminForm

    change_list_template = 'admin/quanly/change_list.html'

    list_display = (
        'phong_hien_thi',
        'thang_hien_thi',
        'tong_tien_hien_thi',
        'so_tien_da_nhan_hien_thi',
        'trang_thai_hien_thi',
        'xem_hoa_don',
        'ngay_thanh_toan_hien_thi',
        ngay_tao_hien_thi,
    )

    # Bộ lọc hiển thị trong danh sách
    list_filter = (
        CoSoThanhToanFilter,
        'trang_thai',
    )

    search_fields = (
        'phong__ten_phong',
        'phong__co_so__ten_co_so',
    )

    ordering = ('-thang',)

    readonly_fields = (
        'tong_tien_o_co_khung',
        'xem_hoa_don',
        'ngay_gui_hoa_don',
        'ngay_thanh_toan',
        'nguoi_duyet',
    )

    fields = (
        'phong',
        'thang',
        'tien_phong',
        'tien_dien',
        'tien_nuoc',
        'tien_khac',
        'tong_tien_o_co_khung',
        'trang_thai',
        'xem_hoa_don',
        'ngay_gui_hoa_don',
        'so_tien_da_nhan',
        'ly_do_bo_sung',
        'ngay_thanh_toan',
        'nguoi_duyet',
        'ghi_chu',
    )

    @admin.display(description='Tổng tiền')
    def tong_tien_o_co_khung(self, obj):
        if obj is None or obj.pk is None:
            return '—'
        so_tien = f'{obj.tong_tien or 0:,.0f}'
        return format_html(
            '<div style="box-sizing:border-box;width:100%;min-height:40px;'
            'border:1px solid #d1dbe7;border-radius:8px;'
            'background:#fff;padding:10px 12px;color:#16233b;'
            'font-size:13px;line-height:20px;">{}</div>',
            so_tien,
        )

    # ======================================================
    # HIỂN THỊ DANH SÁCH THANH TOÁN
    # ======================================================

    @admin.display(description='Phòng', ordering='phong')
    def phong_hien_thi(self, obj):
        return str(obj.phong)

    @admin.display(description='Tháng', ordering='thang')
    def thang_hien_thi(self, obj):
        return obj.thang.strftime('%d/%m/%Y')

    @admin.display(description='Tiền phòng')
    def tien_phong_hien_thi(self, obj):
        return dinh_dang_tien(obj.tien_phong)

    @admin.display(description='Tiền điện')
    def tien_dien_hien_thi(self, obj):
        return dinh_dang_tien(obj.tien_dien)

    @admin.display(description='Tiền nước')
    def tien_nuoc_hien_thi(self, obj):
        return dinh_dang_tien(obj.tien_nuoc)

    @admin.display(description='Tiền khác')
    def tien_khac_hien_thi(self, obj):
        return dinh_dang_tien(obj.tien_khac)

    @admin.display(description='Tổng tiền')
    def tong_tien_hien_thi(self, obj):
        return dinh_dang_tien(obj.tong_tien)

    @admin.display(description='Số tiền đã nhận')
    def so_tien_da_nhan_hien_thi(self, obj):
        return dinh_dang_tien(obj.so_tien_da_nhan)

    @admin.display(
        description='Trạng thái',
        ordering='trang_thai'
    )
    def trang_thai_hien_thi(self, obj):
        return obj.get_trang_thai_display()

    # ======================================================
    # XEM HÓA ĐƠN CHUYỂN KHOẢN
    # ======================================================

    @admin.display(description='Hóa đơn')
    def xem_hoa_don(self, obj):
        if not obj or not obj.pk or not obj.hoa_don or not obj.hoa_don.name:
            return 'Chưa có hóa đơn'

        try:
            if not obj.hoa_don.storage.exists(obj.hoa_don.name):
                return 'Chưa có hóa đơn'
            url = obj.hoa_don.url
        except (OSError, ValueError):
            return 'Chưa có hóa đơn'

        return format_html(
            '<a href="{}" target="_blank" rel="noopener">'
            '📄 Xem hóa đơn'
            '</a>',
            url
        )

    @admin.display(
        description='Ngày thanh toán',
        ordering='ngay_thanh_toan'
    )
    def ngay_thanh_toan_hien_thi(self, obj):
        if obj.ngay_thanh_toan:
            return obj.ngay_thanh_toan.strftime(
                '%d/%m/%Y %H:%M'
            )

        return '-'

    # ======================================================
    # LƯU VÀ XÁC NHẬN THANH TOÁN
    # ======================================================

    @transaction.atomic
    def save_model(self, request, obj, form, change):

        trang_thai_cu = None

        if change:
            trang_thai_cu = ThanhToan.objects.get(
                pk=obj.pk
            ).trang_thai

        # Admin xác nhận đã nhận đủ tiền
        if obj.trang_thai == 'da_thanh_toan':

            if trang_thai_cu != 'da_thanh_toan':
                obj.ngay_thanh_toan = timezone.now()

            obj.nguoi_duyet = request.user
            obj.ly_do_bo_sung = ''

        # Admin yêu cầu người thuê bổ sung tiền
        elif obj.trang_thai == 'yeu_cau_bo_sung':

            obj.ngay_thanh_toan = None
            obj.nguoi_duyet = None

        # Các trạng thái chưa thanh toán
        else:

            obj.ngay_thanh_toan = None
            obj.nguoi_duyet = None

        super().save_model(request, obj, form, change)

        # ==================================================
        # GỬI THÔNG BÁO CHO NGƯỜI THUÊ
        # ==================================================

        if (
            change
            and trang_thai_cu != obj.trang_thai
            and obj.trang_thai in (
                'da_thanh_toan',
                'yeu_cau_bo_sung',
            )
        ):

            hop_dong = HopDong.objects.filter(
                phong=obj.phong,
                trang_thai='hieu_luc',
                ngay_bat_dau__lte=obj.thang,
            ).filter(
                Q(ngay_ket_thuc__isnull=True)
                | Q(ngay_ket_thuc__gte=obj.thang)
            ).select_related(
                'nguoi_thue'
            ).first()

            if hop_dong:

                if obj.trang_thai == 'da_thanh_toan':

                    tieu_de = 'Thanh toán thành công'

                    noi_dung = (
                        f'Thanh toán phòng '
                        f'{obj.phong.ten_phong} '
                        f'tháng {obj.thang:%m/%Y} '
                        f'đã được chủ trọ xác nhận.'
                    )

                else:

                    so_tien_con_thieu = max(
                        0,
                        obj.tong_tien - obj.so_tien_da_nhan
                    )

                    tieu_de = 'Yêu cầu bổ sung thanh toán'

                    noi_dung = (
                        f'Thanh toán phòng '
                        f'{obj.phong.ten_phong} '
                        f'tháng {obj.thang:%m/%Y} '
                        f'chưa được duyệt. '
                        f'Số tiền còn thiếu: '
                        f'{dinh_dang_tien(so_tien_con_thieu)}. '
                        f'Lý do: '
                        f'{obj.ly_do_bo_sung or "Cần kiểm tra lại."}'
                    )

                ThongBao.objects.create(
                    nguoi_thue=hop_dong.nguoi_thue,
                    tieu_de=tieu_de,
                    noi_dung=noi_dung,
                    loai='thanh_toan',
                )






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


# =====================================================
# BỘ LỌC TÀI KHOẢN THEO CƠ SỞ
# =====================================================

class TaiKhoanCoSoFilter(admin.SimpleListFilter):
    title = 'Cơ sở'
    parameter_name = 'co_so'

    def lookups(self, request, model_admin):
        return [
            (str(cs.pk), cs.ten_co_so)
            for cs in CoSo.objects.all().order_by('ten_co_so')
        ]

    def queryset(self, request, queryset):
        co_so_id = self.value()

        if co_so_id:
            return queryset.filter(
                ho_so_nguoi_thue__hop_dong__phong__co_so_id=co_so_id,
                ho_so_nguoi_thue__hop_dong__trang_thai='hieu_luc',
            ).distinct()

        return queryset


# =====================================================
# QUẢN LÝ TÀI KHOẢN THEO CƠ SỞ
# =====================================================

# TÀI KHOẢN
@admin.register(TaiKhoan)
class TaiKhoanAdmin(admin.ModelAdmin):
    ten_chuc_nang = 'Tài khoản'
    co_so_filter_field = 'ho_so_nguoi_thue__hop_dong__phong__co_so_id'

    change_list_template = 'admin/quanly/change_list.html'
    form = TaiKhoanAdminForm

    # CÁC CỘT HIỂN THỊ
    list_display = (
        'ten_dang_nhap_hien_thi',
        'ho_ten_hien_thi',
        'email_hien_thi',
        'vai_tro_hien_thi',
        'so_dien_thoai_hien_thi',
        'trang_thai_hien_thi',
        'ngay_tao_tai_khoan_hien_thi',
    )

    actions = (
        'khoa_tai_khoan',
        'mo_tai_khoan',
    )

    list_filter = (
        TaiKhoanCoSoFilter,
        'vai_tro',
    )

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

    # =================================================
    # HIỂN THỊ DANH SÁCH CƠ SỞ
    # =================================================


    # =================================================
    # LẤY DANH SÁCH TÀI KHOẢN
    # =================================================

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user',
        )

    # =================================================
    # LƯU TÀI KHOẢN - GIỮ NGUYÊN CODE CŨ
    # =================================================

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

    # =================================================
    # HIỂN THỊ VAI TRÒ
    # =================================================

    @admin.display(description='Vai trò', ordering='vai_tro')
    def vai_tro_hien_thi(self, obj):
        return obj.get_vai_tro_display()

    # =================================================
    # HIỂN THỊ SỐ ĐIỆN THOẠI
    # =================================================

    @admin.display(description='Số điện thoại', ordering='so_dien_thoai')
    def so_dien_thoai_hien_thi(self, obj):
        return obj.so_dien_thoai

    # =================================================
    # HIỂN THỊ TRẠNG THÁI
    # =================================================

    @admin.display(description='Trạng thái', ordering='user__is_active')
    def trang_thai_hien_thi(self, obj):
        return 'Đang hoạt động' if obj.user.is_active else 'Đã khóa'

    # =================================================
    # KHÓA TÀI KHOẢN
    # =================================================

    @admin.action(description='Khóa tài khoản đã chọn')
    def khoa_tai_khoan(self, request, queryset):
        user_ids = queryset.values_list('user_id', flat=True)
        updated = User.objects.filter(
            pk__in=user_ids
        ).update(is_active=False)

        self.message_user(
            request,
            f'Đã khóa {updated} tài khoản.'
        )

    # =================================================
    # MỞ TÀI KHOẢN
    # =================================================

    @admin.action(description='Mở tài khoản đã chọn')
    def mo_tai_khoan(self, request, queryset):
        user_ids = queryset.values_list('user_id', flat=True)
        updated = User.objects.filter(
            pk__in=user_ids
        ).update(is_active=True)

        self.message_user(
            request,
            f'Đã mở {updated} tài khoản.'
        )

    # =================================================
    # HIỂN THỊ TÊN ĐĂNG NHẬP
    # =================================================

    @admin.display(description='Tài khoản')
    def ten_dang_nhap_hien_thi(self, obj):
        if obj.so_dien_thoai:
            return obj.so_dien_thoai
        return obj.user.username

    # =================================================
    # HIỂN THỊ NGÀY TẠO
    # =================================================

    @admin.display(description='Ngày tạo', ordering='user__date_joined')
    def ngay_tao_tai_khoan_hien_thi(self, obj):
        return obj.user.date_joined.strftime('%d/%m/%Y %H:%M')

    # =================================================
    # HIỂN THỊ HỌ TÊN
    # =================================================

    @admin.display(description='Họ tên')
    def ho_ten_hien_thi(self, obj):
        try:
            return obj.ho_so_nguoi_thue.ho_ten
        except Exception:
            return obj.user.get_full_name() or 'Chưa cập nhật'

    # =================================================
    # HIỂN THỊ EMAIL
    # =================================================

    @admin.display(description='Email')
    def email_hien_thi(self, obj):
        try:
            email = obj.ho_so_nguoi_thue.email
            if email:
                return email
        except Exception:
            pass

        return obj.user.email or 'Chưa cập nhật'


class ThongBaoAdminForm(forms.ModelForm):
    gui_tat_ca = forms.BooleanField(
        required=False,
        label='Gửi cho tất cả mọi người',
        help_text='Tích chọn để gửi thông báo cho tất cả người thuê có tài khoản.'
    )

    class Meta:
        model = ThongBao
        fields = ('nguoi_thue', 'tieu_de', 'noi_dung', 'loai')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['nguoi_thue'].required = False

        # Không cho đổi người nhận khi sửa thông báo
        if self.instance.pk:
            self.fields.pop('gui_tat_ca', None)
            self.fields['nguoi_thue'].required = True

    def clean(self):
        cleaned_data = super().clean()

        if self.instance.pk:
            return cleaned_data

        gui_tat_ca = cleaned_data.get('gui_tat_ca')
        nguoi_thue = cleaned_data.get('nguoi_thue')

        if not gui_tat_ca and not nguoi_thue:
            self.add_error(
                'nguoi_thue',
                'Vui lòng chọn người nhận hoặc tích gửi cho tất cả.'
            )

        if gui_tat_ca and not NguoiThue.objects.filter(
            tai_khoan__isnull=False,
            tai_khoan__vai_tro='nguoi_thue'
        ).exists():
            self.add_error(
                'gui_tat_ca',
                'Chưa có người thuê nào có tài khoản để nhận thông báo.'
            )

        return cleaned_data


# =====================================================
# BỘ LỌC THÔNG BÁO THEO CƠ SỞ
# =====================================================

class ThongBaoCoSoFilter(admin.SimpleListFilter):
    title = 'Cơ sở'
    parameter_name = 'co_so'

    def lookups(self, request, model_admin):
        return [
            (str(cs.pk), cs.ten_co_so)
            for cs in CoSo.objects.all().order_by('ten_co_so')
        ]

    def queryset(self, request, queryset):
        co_so_id = self.value()

        if co_so_id:
            return queryset.filter(
                nguoi_thue__hop_dong__phong__co_so_id=co_so_id,
                nguoi_thue__hop_dong__trang_thai='hieu_luc',
            ).distinct()

        return queryset


# =====================================================
# QUẢN LÝ THÔNG BÁO THEO CƠ SỞ
# =====================================================

# THÔNG BÁO
@admin.register(ThongBao)
class ThongBaoAdmin(admin.ModelAdmin):
    ten_chuc_nang = 'Thông báo'
    co_so_filter_field = 'nguoi_thue__hop_dong__phong__co_so_id'

    change_list_template = 'admin/quanly/change_list.html'
    form = ThongBaoAdminForm

    list_display = (
        'tieu_de',
        'nguoi_nhan_hien_thi',
        'loai',
        'trang_thai_doc',
        'ngay_tao_hien_thi',
    )

    list_display_links = ('tieu_de',)

    list_filter = (
        ThongBaoCoSoFilter,
        'loai',
        'da_doc',
        'ngay_tao',
    )

    search_fields = (
        'tieu_de',
        'noi_dung',
        'nguoi_thue__ho_ten',
        'nguoi_thue__so_dien_thoai',
    )

    list_select_related = ('nguoi_thue',)

    ordering = ('-ngay_tao',)

    readonly_fields = ('da_doc', 'ngay_tao')

    actions = ('danh_dau_chua_doc',)

    list_per_page = 25

    # =================================================
    # HIỂN THỊ DANH SÁCH CƠ SỞ TRƯỚC
    # =================================================


    # =================================================
    # CÁC TRƯỜNG TRONG FORM
    # =================================================

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                'gui_tat_ca',
                'nguoi_thue',
                'tieu_de',
                'noi_dung',
                'loai',
            )

        return (
            'nguoi_thue',
            'tieu_de',
            'noi_dung',
            'loai',
            'da_doc',
            'ngay_tao',
        )

    # =================================================
    # LƯU VÀ GỬI THÔNG BÁO
    # =================================================

    def save_model(self, request, obj, form, change):

        if not change and form.cleaned_data.get('gui_tat_ca'):

            nguoi_thue_list = list(
                NguoiThue.objects.filter(
                    tai_khoan__isnull=False,
                    tai_khoan__vai_tro='nguoi_thue'
                ).values_list('pk', flat=True)
            )

            if not nguoi_thue_list:
                return

            with transaction.atomic():
                ThongBao.objects.bulk_create([
                    ThongBao(
                        nguoi_thue_id=nguoi_thue_id,
                        tieu_de=obj.tieu_de,
                        noi_dung=obj.noi_dung,
                        loai=obj.loai,
                        da_doc=False,
                    )
                    for nguoi_thue_id in nguoi_thue_list
                ])

            obj.pk = None
            obj._state.adding = True
            self._gui_tat_ca_count = len(nguoi_thue_list)
            return

        super().save_model(request, obj, form, change)

    # =================================================
    # KHÔNG LƯU TRÙNG KHI GỬI TẤT CẢ
    # =================================================

    def save_related(self, request, form, formsets, change):
        if getattr(self, '_gui_tat_ca_count', None) is not None:
            return

        super().save_related(request, form, formsets, change)

    # =================================================
    # THÔNG BÁO SAU KHI GỬI
    # =================================================

    def response_add(self, request, obj, post_url_continue=None):
        count = getattr(self, '_gui_tat_ca_count', None)

        if count is not None:
            del self._gui_tat_ca_count

            self.message_user(
                request,
                f'Đã gửi thông báo thành công cho {count} người thuê.',
                messages.SUCCESS
            )

            return redirect('admin:quanly_thongbao_changelist')

        return super().response_add(
            request, obj, post_url_continue
        )

    # =================================================
    # HIỂN THỊ NGƯỜI NHẬN
    # =================================================

    @admin.display(
        description='Người nhận',
        ordering='nguoi_thue__ho_ten'
    )
    def nguoi_nhan_hien_thi(self, obj):
        return obj.nguoi_thue.ho_ten

    # =================================================
    # TRẠNG THÁI ĐÃ ĐỌC
    # =================================================

    @admin.display(
        description='Trạng thái',
        boolean=True,
        ordering='da_doc'
    )
    def trang_thai_doc(self, obj):
        return obj.da_doc

    # =================================================
    # NGÀY TẠO
    # =================================================

    @admin.display(
        description='Ngày tạo',
        ordering='ngay_tao'
    )
    def ngay_tao_hien_thi(self, obj):
        return obj.ngay_tao.strftime('%d/%m/%Y %H:%M')

    # =================================================
    # ĐÁNH DẤU CHƯA ĐỌC
    # =================================================

    @admin.action(
        description='Đánh dấu chưa đọc cho thông báo đã chọn'
    )
    def danh_dau_chua_doc(self, request, queryset):
        count = queryset.update(da_doc=False)

        self.message_user(
            request,
            f'Đã đánh dấu chưa đọc {count} thông báo.'
        )


admin.site.site_header = "QUẢN LÝ PHÒNG TRỌ"
admin.site.site_title = "Quản lý phòng trọ"
admin.site.index_title = "Trang quản trị Chủ trọ"