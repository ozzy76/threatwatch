import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.conf import settings
from .forms import LoginForm, UserCreateForm
from .backends import MongoEngineBackend
from .decorators import login_required, admin_required
from .models import User
import datetime

logger = logging.getLogger(__name__)

MAX_FAILURES = 5
LOCKOUT_SECONDS = 900  # 15 minutes


def _ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[-1].strip() if xff else request.META.get("REMOTE_ADDR", "unknown")


def _lockout_key(ip):
    return f"login_failures:{ip}"


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    ip = _ip(request)
    failures = cache.get(_lockout_key(ip), 0)
    if failures >= MAX_FAILURES:
        logger.warning("Login locked out for IP: %s", ip)
        return render(request, "accounts/login.html", {
            "form": LoginForm(),
            "lockout": True,
        })

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            backend = MongoEngineBackend()
            user = backend.authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                cache.delete(_lockout_key(ip))
                request.session.cycle_key()
                request.session["_auth_user_id"] = str(user.pk)
                # Update last_login
                user.last_login = datetime.datetime.now(datetime.timezone.utc)
                user.save()
                next_url = request.GET.get("next", "")
                if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                    next_url = settings.LOGIN_REDIRECT_URL
                return redirect(next_url)
            else:
                new_count = failures + 1
                cache.set(_lockout_key(ip), new_count, LOCKOUT_SECONDS)
                logger.warning("Failed login attempt from IP %s (count: %d)", ip, new_count)
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    request.session.flush()
    logger.info("User logged out")
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required
@admin_required
def user_list(request):
    users = User.objects().order_by("username")
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
@admin_required
@require_http_methods(["GET", "POST"])
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User(
                username=d["username"],
                email=d["email"],
                first_name=d["first_name"],
                last_name=d["last_name"],
                role=d["role"],
                is_active=True,
                date_joined=datetime.datetime.now(datetime.timezone.utc),
            )
            user.set_password(d["password"])
            user.save()
            logger.info("Admin %s created user %s (role=%s)", request.user.username, user.username, user.role)
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect("accounts:user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_create.html", {"form": form})
