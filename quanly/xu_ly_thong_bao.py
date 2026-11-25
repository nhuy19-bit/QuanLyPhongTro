
from datetime import timedelta

from django.utils import timezone

from .models import HopDong, ThongBaoAdmin


def thong_bao_admin(request):
    """
    Hiển thị cảnh báo hợp đồng sắp hết hạn
    trong vòng 7 ngày trên chuông thông báo Admin.
    """

    # Chỉ Admin và nhân viên được xem thông báo
    if not request.user.is_authenticated:
        return {}

    if not request.user.is_staff:
        return {}

    hom_nay = timezone.localdate()
    ngay_gioi_han = hom_nay + timedelta(days=7)

    # Tìm hợp đồng sắp hết hạn trong 7 ngày
    hop_dong_sap_het_han = HopDong.objects.filter(
        trang_thai='hieu_luc',
        ngay_ket_thuc__range=(
            hom_nay,
            ngay_gioi_han
        )
    ).select_related(
        'phong',
        'nguoi_thue'
    )

    # Tự tạo thông báo, không tạo trùng
    for hop_dong in hop_dong_sap_het_han:
        so_ngay_con_lai = (
            hop_dong.ngay_ket_thuc - hom_nay
        ).days

        ThongBaoAdmin.objects.get_or_create(
            hop_dong=hop_dong,
            ngay_het_han=hop_dong.ngay_ket_thuc,
            defaults={
                'tieu_de': (
                    f'Hợp đồng phòng '
                    f'{hop_dong.phong.ten_phong} sắp hết hạn'
                ),
                'noi_dung': (
                    f'Phòng {hop_dong.phong.ten_phong} - '
                    f'Người thuê: {hop_dong.nguoi_thue.ho_ten}. '
                    f'Hợp đồng còn {so_ngay_con_lai} ngày, '
                    f'hết hạn ngày '
                    f'{hop_dong.ngay_ket_thuc:%d/%m/%Y}.'
                ),
                'da_doc': False,
            }
        )

    # Chỉ lấy thông báo của hợp đồng còn hiệu lực
    # và đang nằm trong khoảng cảnh báo 7 ngày
    danh_sach = ThongBaoAdmin.objects.filter(
        hop_dong__trang_thai='hieu_luc',
        hop_dong__ngay_ket_thuc__range=(
            hom_nay,
            ngay_gioi_han
        ),
        ngay_het_han__range=(
            hom_nay,
            ngay_gioi_han
        )
    ).select_related(
        'hop_dong',
        'hop_dong__phong',
        'hop_dong__nguoi_thue'
    ).order_by(
        '-ngay_tao'
    )

    return {
        # Danh sách hiển thị trong chuông
        'canh_bao_admin_moi': danh_sach[:10],

        # Số lượng thông báo chưa đọc
        'so_canh_bao_admin_chua_doc': danh_sach.filter(
            da_doc=False
        ).count(),
    }
