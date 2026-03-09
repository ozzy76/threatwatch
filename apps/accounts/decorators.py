from functools import wraps
from django.shortcuts import redirect, render
from django.conf import settings
from apps.accounts.models import ROLE_ADMIN


def login_required(view_func):
    """Decorator that redirects unauthenticated users to login."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Decorator that returns 403 for non-admin users."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if getattr(request.user, "role", None) != ROLE_ADMIN:
            return render(request, "403.html", status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
