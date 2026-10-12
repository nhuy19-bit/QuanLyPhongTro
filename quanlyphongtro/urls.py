"""
URL configuration for quanlyphongtro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from quanly import views

from quanly.views import (
    home,
    dang_nhap,
    dang_xuat,
    dashboard,
    admin_dashboard,
)


urlpatterns = [
    re_path(r'^admin/$', admin_dashboard, name='admin_dashboard'),
    path('admin/', admin.site.urls),

    path(
        'phong/',
        views.danh_sach_phong,
        name='phong_list'
    ),

    path(
        'phong/them/',
        views.them_phong,
        name='them_phong'
    ),

    path(
        'phong/sua/<int:id>/',
        views.sua_phong,
        name='sua_phong'
    ),

    path(
        'phong/xoa/<int:id>/',
        views.xoa_phong,
        name='xoa_phong'
    ),

    path('', home, name='home'),

    path('dang-nhap/', dang_nhap, name='login'),

    path('dang-xuat/', dang_xuat, name='logout'),

    path('dashboard/', dashboard, name='dashboard'),
]