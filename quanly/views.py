from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .models import HopDong, DienNuoc, ThanhToan
from .models import TaiKhoan
from .models import Phong
from django.shortcuts import get_object_or_404

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

    danh_sach = Phong.objects.all()

    return render(
        request,
        'phong_list.html',
        {
            'danh_sach': danh_sach
        }
    )


def them_phong(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        ten_phong = request.POST.get('ten_phong')
        gia_phong = request.POST.get('gia_phong')
        dien_tich = request.POST.get('dien_tich')
        trang_thai = request.POST.get('trang_thai')
        mo_ta = request.POST.get('mo_ta')

        Phong.objects.create(
            ten_phong=ten_phong,
            gia_phong=gia_phong,
            dien_tich=dien_tich,
            trang_thai=trang_thai,
            mo_ta=mo_ta
        )

        return redirect('phong_list')

    return render(
        request,
        'phong_form.html'
    )


def sua_phong(request, id):
    phong = get_object_or_404(Phong, id=id)

    if request.method == 'POST':
        phong.ten_phong = request.POST.get('ten_phong')
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
            'phong': phong
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