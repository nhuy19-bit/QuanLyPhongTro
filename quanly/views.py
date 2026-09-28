from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


def home(request):
    return render(request, 'home.html')


def dang_nhap(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

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