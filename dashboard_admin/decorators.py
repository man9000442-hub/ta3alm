"""
dashboard_admin/decorators.py
Decorators للتحقق من صلاحيات الإدارة
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def _get_admin_profile(user):
    """يُعيد admin_profile لو وجد، أو None."""
    try:
        return user.admin_profile if user.admin_profile.is_active_admin else None
    except Exception:
        return None


def admin_required(view_func):
    """
    يسمح فقط لـ: superuser أو user.role == 'admin' مع AdminProfile نشط.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('account_login')

        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        profile = _get_admin_profile(user)
        if profile:
            return view_func(request, *args, **kwargs)

        messages.error(request, "ليس لديك صلاحية للوصول لهذه الصفحة.")
        return redirect('home')

    return wrapper


def owner_required(view_func):
    """
    يسمح فقط لـ: superuser أو admin_role == 'owner'.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('account_login')

        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        profile = _get_admin_profile(user)
        if profile and profile.is_owner:
            return view_func(request, *args, **kwargs)

        messages.error(request, "هذه الصفحة للمالك فقط.")
        return redirect('admin_panel:dashboard')

    return wrapper


def finance_required(view_func):
    """
    يسمح لـ: superuser, owner, finance.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('account_login')

        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        profile = _get_admin_profile(user)
        if profile and profile.can_view_finance:
            return view_func(request, *args, **kwargs)

        messages.error(request, "ليس لديك صلاحية عرض التقارير المالية.")
        return redirect('admin_panel:dashboard')

    return wrapper


def moderator_required(view_func):
    """
    يسمح لـ: superuser, owner, moderator.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('account_login')

        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        profile = _get_admin_profile(user)
        if profile and profile.can_manage_users:
            return view_func(request, *args, **kwargs)

        messages.error(request, "ليس لديك صلاحية إدارة المستخدمين.")
        return redirect('admin_panel:dashboard')

    return wrapper
