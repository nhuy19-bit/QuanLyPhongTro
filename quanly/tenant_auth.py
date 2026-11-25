"""Độc lập đăng nhập người thuê với Django Admin bằng cookie ký HMAC.

Không dùng cookie này để cấp quyền cho đường dẫn admin.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import signing
from django.utils.crypto import constant_time_compare

TENANT_COOKIE_NAME = 'quanly_tenant_auth'
TENANT_COOKIE_SALT = 'quanly.tenant.auth.v1'
TENANT_MAX_AGE = 60 * 60 * 24 * 7
TENANT_PATHS = (
    '/dashboard/', '/phong-cua-toi/', '/hop-dong-cua-toi/',
    '/dien-nuoc-cua-toi/', '/thanh-toan-cua-toi/',
    '/thanh-toan/', '/thong-bao-cua-toi/', '/thong-bao/',
    '/thong-tin-ca-nhan/', '/dang-xuat/', '/dang-nhap/',
)


def set_tenant_login_cookie(response, user, request):
    token = signing.dumps(
        {'uid': user.pk, 'hash': user.get_session_auth_hash()},
        salt=TENANT_COOKIE_SALT,
    )
    response.set_cookie(
        TENANT_COOKIE_NAME, token, max_age=TENANT_MAX_AGE,
        httponly=True, secure=request.is_secure(), samesite='Lax', path='/',
    )
    return response


class TenantAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info.startswith(TENANT_PATHS):
            request.user = self.get_tenant_user(request)
        return self.get_response(request)

    @staticmethod
    def get_tenant_user(request):
        token = request.COOKIES.get(TENANT_COOKIE_NAME)
        if not token:
            return AnonymousUser()
        try:
            data = signing.loads(
                token, salt=TENANT_COOKIE_SALT, max_age=TENANT_MAX_AGE,
            )
            user = get_user_model().objects.get(pk=data['uid'], is_active=True)
            if not constant_time_compare(data['hash'], user.get_session_auth_hash()):
                return AnonymousUser()
            tai_khoan = getattr(user, 'tai_khoan', None)
            if not tai_khoan or tai_khoan.vai_tro != 'nguoi_thue':
                return AnonymousUser()
            return user
        except (signing.BadSignature, signing.SignatureExpired, KeyError,
                ValueError, TypeError, get_user_model().DoesNotExist):
            return AnonymousUser()
