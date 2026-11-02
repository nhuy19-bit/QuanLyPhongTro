from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .models import HopDong, DienNuoc, ThanhToan
from .models import TaiKhoan
from .models import CoSo, Phong
from django.shortcuts import get_object_or_404

from io import BytesIO
from xml.sax.saxutils import escape
from pathlib import Path

from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def home(request):
    danh_sach_phong = Phong.objects.all().order_by('ten_phong')
    return render(
        request,
        'home.html',
        {
            'danh_sach_phong': danh_sach_phong,
            'tong_so_phong': danh_sach_phong.count(),
            'phong_trong': danh_sach_phong.filter(trang_thai='trong').count(),
            'phong_dang_thue': danh_sach_phong.filter(trang_thai='dang_thue').count(),
            'phong_bao_tri': danh_sach_phong.filter(trang_thai='bao_tri').count(),
        }
    )


def dang_nhap(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # Nếu là tài khoản người thuê
            if hasattr(user, 'tai_khoan') and user.tai_khoan.vai_tro == 'nguoi_thue':
                return redirect('dashboard')

            return render(
                request,
                'login.html',
                {
                    'error': 'Tài khoản này không phải tài khoản người thuê.'
                }
            )

        return render(
            request,
            'login.html',
            {'error': 'Tên đăng nhập hoặc mật khẩu không đúng.'}
        )

    return render(request, 'login.html')
def dang_ky(request):
    
    if request.method == 'POST':
        ho_ten = request.POST.get('ho_ten', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        so_dien_thoai = request.POST.get('so_dien_thoai', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        vai_tro = request.POST.get('vai_tro', '')

        # Kiểm tra dữ liệu bắt buộc
        if not ho_ten or not username or not password or not password2:
            return render(
                request,
                'register.html',
                {'error': 'Vui lòng nhập đầy đủ các thông tin bắt buộc.'}
            )

        # Kiểm tra mật khẩu
        if password != password2:
            return render(
                request,
                'register.html',
                {'error': 'Mật khẩu xác nhận không khớp.'}
            )

        # Kiểm tra vai trò
        if vai_tro not in ['chu_tro', 'nguoi_thue']:
            return render(
                request,
                'register.html',
                {'error': 'Vui lòng chọn vai trò hợp lệ.'}
            )

        # Kiểm tra username đã tồn tại
        if User.objects.filter(username=username).exists():
            return render(
                request,
                'register.html',
                {'error': 'Tên đăng nhập đã tồn tại.'}
            )

        # Tạo tài khoản User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=ho_ten
        )

        # Tạo thông tin vai trò
        TaiKhoan.objects.create(
            user=user,
            vai_tro=vai_tro,
            so_dien_thoai=so_dien_thoai
        )

        # Đăng nhập luôn sau khi đăng ký
        login(request, user)

        return redirect('dashboard')

    return render(request, 'register.html')

def dang_xuat(request):
    logout(request)
    return redirect('home')


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        tai_khoan = request.user.tai_khoan
    except TaiKhoan.DoesNotExist:
        return redirect('login')

    if tai_khoan.vai_tro != 'nguoi_thue':
        return redirect('admin:index')

    # Lấy hồ sơ người thuê đã liên kết với tài khoản
    from .models import NguoiThue

    try:
        nguoi_thue = tai_khoan.ho_so_nguoi_thue
    except NguoiThue.DoesNotExist:
        return render(
            request,
            'dashboard_nguoi_thue.html',
            {
                'tai_khoan': tai_khoan,
                'error': 'Tài khoản chưa được liên kết với hồ sơ người thuê.'
            }
        )

    # Lấy hợp đồng đang có hiệu lực của người thuê
    hop_dong = HopDong.objects.filter(
        nguoi_thue=nguoi_thue,
        trang_thai='hieu_luc'
    ).select_related(
        'phong',
        'nguoi_thue'
    ).order_by('-ngay_bat_dau').first()

    phong = hop_dong.phong if hop_dong else None

    # Lấy dữ liệu điện nước mới nhất của phòng
    dien_nuoc = None
    thanh_toan = None

    if phong:
        dien_nuoc = DienNuoc.objects.filter(
            phong=phong
        ).order_by('-thang').first()

        thanh_toan = ThanhToan.objects.filter(
            phong=phong
        ).order_by('-thang').first()

    context = {
        'tai_khoan': tai_khoan,
        'nguoi_thue': nguoi_thue,
        'hop_dong': hop_dong,
        'phong': phong,
        'dien_nuoc': dien_nuoc,
        'thanh_toan': thanh_toan,
    }

    return render(
        request,
        'dashboard_nguoi_thue.html',
        context
    )

def danh_sach_phong(request):
    if not request.user.is_authenticated:
        return redirect('login')

    danh_sach_co_so = CoSo.objects.prefetch_related('phong').all()

    return render(
        request,
        'phong_list.html',
        {
            'danh_sach_co_so': danh_sach_co_so,
            'phong_chua_co_so': Phong.objects.filter(co_so__isnull=True),
        }
    )


def them_phong(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        ten_phong = request.POST.get('ten_phong')
        gia_phong = request.POST.get('gia_phong')
        dien_tich = request.POST.get('dien_tich')
        co_so_id = request.POST.get('co_so')
        trang_thai = request.POST.get('trang_thai')
        mo_ta = request.POST.get('mo_ta')

        Phong.objects.create(
            ten_phong=ten_phong,
            co_so_id=co_so_id or None,
            gia_phong=gia_phong,
            dien_tich=dien_tich,
            trang_thai=trang_thai,
            mo_ta=mo_ta
        )

        return redirect('phong_list')

    return render(
        request,
        'phong_form.html',
        {
            'danh_sach_co_so': CoSo.objects.all(),
        }
    )


def sua_phong(request, id):
    phong = get_object_or_404(Phong, id=id)

    if request.method == 'POST':
        phong.ten_phong = request.POST.get('ten_phong')
        phong.co_so_id = request.POST.get('co_so') or None
        phong.gia_phong = request.POST.get('gia_phong')
        phong.dien_tich = request.POST.get('dien_tich')
        phong.trang_thai = request.POST.get('trang_thai')
        phong.mo_ta = request.POST.get('mo_ta')

        phong.save()

        return redirect('phong_list')

    return render(
        request,
        'phong_form.html',
        {
            'phong': phong,
            'danh_sach_co_so': CoSo.objects.all(),
        }
    )


def xoa_phong(request, id):
    phong = get_object_or_404(Phong, id=id)

    if request.method == 'POST':
        phong.delete()
        return redirect('phong_list')

    return render(
        request,
        'phong_confirm_delete.html',
        {
            'phong': phong
        }
    )

@staff_member_required
def admin_dashboard(request):
    from .models import (
        Phong,
        NguoiThue,
        HopDong,
        DienNuoc,
        ThanhToan,
        TaiKhoan,
    )
    from django.contrib import admin

    context = admin.site.each_context(request)

    context.update({
        'title': 'Tổng quan',

        'tong_phong': Phong.objects.count(),

        'tong_co_so': CoSo.objects.count(),

        'phong_trong': Phong.objects.filter(
            trang_thai='trong'
        ).count(),

        'phong_dang_thue': Phong.objects.filter(
            trang_thai='dang_thue'
        ).count(),

        'phong_bao_tri': Phong.objects.filter(
            trang_thai='bao_tri'
        ).count(),

        'tong_nguoi_thue': NguoiThue.objects.count(),

        'tong_hop_dong': HopDong.objects.count(),

        'tong_dien_nuoc': DienNuoc.objects.count(),

        'tong_thanh_toan': ThanhToan.objects.count(),

        'tong_tai_khoan': TaiKhoan.objects.count(),
    })

    return render(
        request,
        'admin/dashboard.html',
        context
    )

def phong_cua_toi(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        tai_khoan = request.user.tai_khoan
    except TaiKhoan.DoesNotExist:
        return redirect('login')

    if tai_khoan.vai_tro != 'nguoi_thue':
        return redirect('admin:index')

    from .models import NguoiThue

    try:
        nguoi_thue = tai_khoan.ho_so_nguoi_thue
    except NguoiThue.DoesNotExist:
        return render(
            request,
            'phong_cua_toi.html',
            {'error': 'Tài khoản chưa được liên kết với hồ sơ người thuê.'}
        )

    hop_dong = HopDong.objects.filter(
        nguoi_thue=nguoi_thue,
        trang_thai='hieu_luc'
    ).select_related('phong').order_by('-ngay_bat_dau').first()

    return render(
        request,
        'phong_cua_toi.html',
        {
            'nguoi_thue': nguoi_thue,
            'hop_dong': hop_dong,
            'phong': hop_dong.phong if hop_dong else None,
        }
    )

@staff_member_required
def hopdong_pdf(request, hopdong_id):
    """
    Tạo hợp đồng PDF từ dữ liệu hợp đồng đã lưu.
    Chỉ nhân viên/quản trị viên được phép xuất file.
    """
    hop_dong = get_object_or_404(
        HopDong.objects.select_related(
            'phong',
            'phong__co_so',
            'nguoi_thue',
        ),
        pk=hopdong_id,
    )

    # Dùng font Arial để hiển thị tiếng Việt trên Windows.
    font_regular = Path(r'C:\Windows\Fonts\arial.ttf')
    font_bold = Path(r'C:\Windows\Fonts\arialbd.ttf')

    if not font_regular.exists() or not font_bold.exists():
        return HttpResponse(
            'Không tìm thấy font Arial tại C:\\Windows\\Fonts. '
            'Hãy kiểm tra font Arial trên máy đang chạy Django.',
            status=500,
            content_type='text/plain; charset=utf-8',
        )

    if 'ArialPDF' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('ArialPDF', str(font_regular)))
    if 'ArialPDF-Bold' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('ArialPDF-Bold', str(font_bold)))

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.7 * cm,
        title=f'Hop dong thue phong {hop_dong.pk}',
        author='He thong Quan ly phong tro',
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ContractTitle',
        parent=styles['Title'],
        fontName='ArialPDF-Bold',
        fontSize=16,
        leading=21,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#17365D'),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name='ContractHeading',
        parent=styles['Heading2'],
        fontName='ArialPDF-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#17365D'),
        spaceBefore=9,
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name='ContractBody',
        parent=styles['BodyText'],
        fontName='ArialPDF',
        fontSize=9.5,
        leading=14,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='ContractSmall',
        parent=styles['BodyText'],
        fontName='ArialPDF',
        fontSize=9,
        leading=13,
    ))

    def safe(value, default='Chưa cập nhật'):
        if value is None or value == '':
            value = default
        return escape(str(value))

    def money(value):
        if value is None:
            return 'Chưa cập nhật'
        try:
            return f'{value:,.0f} VNĐ'.replace(',', '.')
        except (TypeError, ValueError):
            return f'{safe(value)} VNĐ'

    def date_text(value):
        return value.strftime('%d/%m/%Y') if value else 'Không xác định'

    tenant = hop_dong.nguoi_thue
    room = hop_dong.phong
    facility = room.co_so

    story = [
        Paragraph('HỢP ĐỒNG THUÊ PHÒNG TRỌ', styles['ContractTitle']),
        Paragraph(
            f'Số hợp đồng: HD-{hop_dong.pk:04d}',
            ParagraphStyle(
                name='ContractNumber',
                parent=styles['ContractBody'],
                alignment=TA_CENTER,
            ),
        ),
        Spacer(1, 0.25 * cm),
        Paragraph('ĐIỀU 1. THÔNG TIN CÁC BÊN', styles['ContractHeading']),
        Paragraph('<b>BÊN CHO THUÊ (BÊN A)</b>', styles['ContractBody']),
        Paragraph('Họ tên/đơn vị: ................................................................................', styles['ContractBody']),
        Paragraph('Số điện thoại: ....................................................................................', styles['ContractBody']),
        Paragraph('<b>BÊN THUÊ (BÊN B)</b>', styles['ContractBody']),
    ]

    tenant_rows = [
        ['Họ và tên', Paragraph(safe(getattr(tenant, 'ho_ten', None)), styles['ContractSmall'])],
        ['Số CCCD', Paragraph(safe(getattr(tenant, 'so_cccd', None)), styles['ContractSmall'])],
        ['Số điện thoại', Paragraph(safe(getattr(tenant, 'so_dien_thoai', None)), styles['ContractSmall'])],
        ['Email', Paragraph(safe(getattr(tenant, 'email', None)), styles['ContractSmall'])],
        ['Địa chỉ', Paragraph(safe(getattr(tenant, 'dia_chi', None)), styles['ContractSmall'])],
    ]
    tenant_table = Table(tenant_rows, colWidths=[3.5 * cm, 12 * cm])
    tenant_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'ArialPDF'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        tenant_table,
        Paragraph('ĐIỀU 2. THÔNG TIN PHÒNG THUÊ', styles['ContractHeading']),
    ])

    room_rows = [
        ['Cơ sở', Paragraph(safe(getattr(facility, 'ten_co_so', None) if facility else None), styles['ContractSmall'])],
        ['Địa chỉ cơ sở', Paragraph(safe(getattr(facility, 'dia_chi', None) if facility else None), styles['ContractSmall'])],
        ['Phòng', Paragraph(safe(getattr(room, 'ten_phong', None)), styles['ContractSmall'])],
        ['Diện tích', Paragraph(
            f'{safe(getattr(room, "dien_tich", None))} m²'
            if getattr(room, 'dien_tich', None) not in (None, '')
            else 'Chưa cập nhật',
            styles['ContractSmall'],
        )],
        ['Giá thuê', Paragraph(money(getattr(room, 'gia_phong', None)), styles['ContractSmall'])],
    ]
    room_table = Table(room_rows, colWidths=[3.5 * cm, 12 * cm])
    room_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'ArialPDF'),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    status = (
        hop_dong.get_trang_thai_display()
        if hasattr(hop_dong, 'get_trang_thai_display')
        else getattr(hop_dong, 'trang_thai', 'Chưa cập nhật')
    )

    story.extend([
        room_table,
        Paragraph('ĐIỀU 3. THỜI HẠN VÀ CHI PHÍ THUÊ', styles['ContractHeading']),
    ])

    contract_rows = [
        ['Ngày bắt đầu', date_text(hop_dong.ngay_bat_dau)],
        ['Ngày kết thúc', date_text(hop_dong.ngay_ket_thuc)],
        ['Tiền đặt cọc', money(hop_dong.tien_coc)],
        ['Trạng thái hợp đồng', safe(status)],
    ]
    contract_table = Table(
        [[label, Paragraph(safe(value), styles['ContractSmall'])] for label, value in contract_rows],
        colWidths=[3.5 * cm, 12 * cm],
    )
    contract_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'ArialPDF'),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        contract_table,
        Paragraph('ĐIỀU 4. THỎA THUẬN CHUNG', styles['ContractHeading']),
        Paragraph(
            '1. Bên B sử dụng phòng đúng mục đích thuê và giữ gìn tài sản, '
            'vệ sinh, an ninh trật tự tại cơ sở.<br/>'
            '2. Bên B thanh toán tiền thuê và các chi phí điện, nước, dịch vụ '
            'theo thỏa thuận giữa hai bên.<br/>'
            '3. Mọi thay đổi hoặc tranh chấp phát sinh được hai bên trao đổi, '
            'thống nhất và thực hiện theo quy định pháp luật.',
            styles['ContractBody'],
        ),
        Paragraph(
            f'<b>Ghi chú hợp đồng:</b> {safe(hop_dong.ghi_chu, "Không có")}',
            styles['ContractBody'],
        ),
        Spacer(1, 0.5 * cm),
        Paragraph(
            'Hai bên đọc lại nội dung, thống nhất và ký xác nhận dưới đây.',
            styles['ContractBody'],
        ),
        Spacer(1, 0.3 * cm),
    ])

    signature_table = Table([
        [
            Paragraph('<b>BÊN CHO THUÊ (BÊN A)</b><br/><br/><br/><br/>'
                      '(Ký, ghi rõ họ tên)', styles['ContractBody']),
            Paragraph('<b>BÊN THUÊ (BÊN B)</b><br/><br/><br/><br/>'
                      f'{safe(getattr(tenant, "ho_ten", None))}<br/>(Ký, ghi rõ họ tên)',
                      styles['ContractBody']),
        ]
    ], colWidths=[7.75 * cm, 7.75 * cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(signature_table)

    document.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'inline; filename="hop_dong_{hop_dong.pk}.pdf"'
    )
    return response

@login_required
def hop_dong_cua_toi(request):
    try:
        tai_khoan = request.user.tai_khoan
    except TaiKhoan.DoesNotExist:
        return redirect('login')

    if tai_khoan.vai_tro != 'nguoi_thue':
        return redirect('admin:index')

    from .models import NguoiThue

    try:
        nguoi_thue = tai_khoan.ho_so_nguoi_thue
    except NguoiThue.DoesNotExist:
        return render(
            request,
            'hop_dong_cua_toi.html',
            {
                'danh_sach_hop_dong': [],
                'error': 'Tài khoản chưa được liên kết với hồ sơ người thuê.',
            }
        )

    danh_sach_hop_dong = HopDong.objects.filter(
        nguoi_thue=nguoi_thue
    ).select_related(
        'phong',
        'phong__co_so',
        'nguoi_thue',
    ).order_by('-ngay_bat_dau')
    print("USER ĐĂNG NHẬP:", request.user.username)
    print("HỢP ĐỒNG TÌM ĐƯỢC:", danh_sach_hop_dong.count())
    return render(
        request,
        'hop_dong_cua_toi.html',
        {
            'tai_khoan': tai_khoan,
            'nguoi_thue': nguoi_thue,
            'danh_sach_hop_dong': danh_sach_hop_dong,
        }
    )

def dien_nuoc_cua_toi(request):
    tai_khoan = getattr(request.user, "tai_khoan", None)

    # Kiểm tra tài khoản người thuê
    if not tai_khoan or tai_khoan.vai_tro != "nguoi_thue":
        return render(request, "dien_nuoc_cua_toi.html", {
            "danh_sach_dien_nuoc": [],
            "error": "Bạn không có quyền xem thông tin này.",
        })

    # Lấy hồ sơ người thuê đã liên kết với tài khoản
    nguoi_thue = getattr(tai_khoan, "ho_so_nguoi_thue", None)

    if not nguoi_thue:
        return render(request, "dien_nuoc_cua_toi.html", {
            "danh_sach_dien_nuoc": [],
            "error": "Tài khoản chưa được liên kết với hồ sơ người thuê.",
        })

    # Lấy các phòng có hợp đồng còn hiệu lực của người thuê
    phong_ids = HopDong.objects.filter(
        nguoi_thue=nguoi_thue,
        trang_thai="hieu_luc",
    ).values_list("phong_id", flat=True)

    # Lấy lịch sử điện nước của các phòng đó
    danh_sach_dien_nuoc = DienNuoc.objects.filter(
        phong_id__in=phong_ids
    ).select_related(
        "phong", "phong__co_so"
    ).order_by("-thang")

    return render(request, "dien_nuoc_cua_toi.html", {
        "danh_sach_dien_nuoc": danh_sach_dien_nuoc,
        "error": None,
    })

def thanh_toan_cua_toi(request):
    tai_khoan = getattr(request.user, "tai_khoan", None)

    if not tai_khoan or tai_khoan.vai_tro != "nguoi_thue":
        return redirect("home")

    nguoi_thue = getattr(tai_khoan, "ho_so_nguoi_thue", None)

    if not nguoi_thue:
        return render(request, "thanh_toan_cua_toi.html", {
            "danh_sach_thanh_toan": [],
            "error": "Tài khoản chưa được liên kết với hồ sơ người thuê.",
        })

    phong_ids = HopDong.objects.filter(
        nguoi_thue=nguoi_thue,
        trang_thai="hieu_luc",
    ).values_list("phong_id", flat=True)

    danh_sach_thanh_toan = ThanhToan.objects.filter(
        phong_id__in=phong_ids
    ).select_related(
        "phong"
    ).order_by("-thang")

    return render(request, "thanh_toan_cua_toi.html", {
        "danh_sach_thanh_toan": danh_sach_thanh_toan,
        "error": None,
    })

