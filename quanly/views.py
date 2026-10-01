from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .models import TaiKhoan

def home(request):
    return render(request, 'home.html')


def dang_nhap(request):
    if request.user.is_superuser:
        return redirect('admin:index')

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
            return redirect('dashboard')

        return render(
            request,
            'login.html',
            {'error': 'Tên đăng nhập hoặc mật khẩu không đúng.'}
        )

    return render(request, 'login.html')

def dang_ky(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

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

    if request.user.is_superuser:
        return redirect('admin:index')

    try:
        vai_tro = request.user.tai_khoan.vai_tro
    except Exception:
        return render(
            request,
            'dashboard.html',
            {'error': 'Tài khoản chưa được thiết lập vai trò.'}
        )

    if vai_tro == 'chu_tro':
        return render(request, 'dashboard_chu_tro.html')

    return render(request, 'dashboard_nguoi_thue.html')