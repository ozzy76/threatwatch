import logging
import urllib.request
import urllib.parse
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.conf import settings
from .forms import LoginForm, UserCreateForm, UserProfileForm
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


def auto_populate_names_from_email(user):
    """
    Parses the local-part of the email address to guess first/last names.
    e.g., john.doe@threatwatch.io -> First Name: John, Last Name: Doe
    """
    if not user.email:
        return
    
    modified = False
    local_part = user.email.split('@')[0]
    
    # Check common email delimiters
    parts = []
    for delimiter in ['.', '-', '_']:
        if delimiter in local_part:
            parts = local_part.split(delimiter)
            break
            
    if parts and len(parts) >= 2:
        if not user.first_name:
            user.first_name = parts[0].capitalize()
            modified = True
        if not user.last_name:
            user.last_name = parts[1].capitalize()
            modified = True
    elif not user.first_name:
        user.first_name = local_part.capitalize()
        modified = True
        
    if modified:
        user.save()
        logger.info("Normal Login: Auto-populated missing names for user %s", user.username)


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
                # Auto-populate names if missing
                auto_populate_names_from_email(user)
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


@require_http_methods(["GET", "POST"])
def oidc_login(request, provider):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    provider = provider.lower()
    if provider not in settings.OIDC_PROVIDERS:
        messages.error(request, f"Unsupported authentication provider: {provider}")
        return redirect("accounts:login")

    config_data = settings.OIDC_PROVIDERS[provider]

    # Sandbox / Mock Developer Mode
    if settings.OIDC_SANDBOX_MODE:
        if request.method == "POST":
            email = request.POST.get("email", "").strip()
            first_name = request.POST.get("first_name", "").strip() or "SSO"
            last_name = request.POST.get("last_name", "").strip() or "User"
            if not email:
                messages.error(request, "Email address is required.")
                return render(request, "accounts/oidc_sandbox.html", {
                    "provider": provider,
                    "provider_name": config_data["name"]
                })
            # Redirect to callback with mock query parameters
            query = urllib.parse.urlencode({
                "mock_email": email,
                "mock_first": first_name,
                "mock_last": last_name,
                "provider": provider
            })
            return redirect(f"/accounts/oidc/callback/?{query}")

        return render(request, "accounts/oidc_sandbox.html", {
            "provider": provider,
            "provider_name": config_data["name"]
        })

    # Production flow
    import secrets
    state = secrets.token_hex(16)
    nonce = secrets.token_hex(16)
    request.session["oidc_state"] = state
    request.session["oidc_nonce"] = nonce
    request.session["oidc_provider"] = provider

    # Redirect URI
    redirect_uri = request.build_absolute_uri("/accounts/oidc/callback/")
    params = {
        "client_id": config_data["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": config_data["scope"],
        "state": state,
        "nonce": nonce
    }
    auth_url = f"{config_data['auth_url']}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


@require_http_methods(["GET"])
def oidc_callback(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    # Sandbox Mock Verification
    if settings.OIDC_SANDBOX_MODE:
        email = request.GET.get("mock_email", "").strip()
        first_name = request.GET.get("mock_first", "SSO").strip()
        last_name = request.GET.get("mock_last", "User").strip()
        provider = request.GET.get("provider", "sso").strip()
        
        if not email:
            messages.error(request, "Invalid sandbox authentication payload.")
            return redirect("accounts:login")
    else:
        # Production Verification
        state = request.GET.get("state")
        code = request.GET.get("code")
        session_state = request.session.pop("oidc_state", None)
        provider = request.session.pop("oidc_provider", None)

        if not state or not session_state or state != session_state:
            messages.error(request, "Invalid OIDC state. Authorization failed.")
            return redirect("accounts:login")

        if not code or not provider:
            messages.error(request, "Invalid OIDC callback code. Authorization failed.")
            return redirect("accounts:login")

        config_data = settings.OIDC_PROVIDERS[provider]
        redirect_uri = request.build_absolute_uri("/accounts/oidc/callback/")

        # Exchange code for tokens
        try:
            token_params = {
                "client_id": config_data["client_id"],
                "client_secret": config_data["client_secret"],
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            token_data = urllib.parse.urlencode(token_params).encode("utf-8")
            token_req = urllib.request.Request(config_data["token_url"], data=token_data)
            
            with urllib.request.urlopen(token_req) as response:
                tokens = json.loads(response.read().decode("utf-8"))
            
            access_token = tokens.get("access_token")
            if not access_token:
                messages.error(request, "Failed to retrieve access token.")
                return redirect("accounts:login")

            # Fetch user details
            userinfo_req = urllib.request.Request(config_data["userinfo_url"])
            userinfo_req.add_header("Authorization", f"Bearer {access_token}")
            
            with urllib.request.urlopen(userinfo_req) as response:
                claims = json.loads(response.read().decode("utf-8"))
            
            email = claims.get("email")
            first_name = claims.get("given_name", claims.get("first_name", "SSO"))
            last_name = claims.get("family_name", claims.get("last_name", "User"))
            
            if not email:
                messages.error(request, "OIDC provider did not return email address.")
                return redirect("accounts:login")
                
        except Exception as exc:
            logger.error("OIDC authentication exchange failed: %s", exc)
            messages.error(request, "Authentication exchange failed. Please contact support.")
            return redirect("accounts:login")

    # Complete Authentication & Auto-Provision User
    try:
        user = User.objects.get(email=email)
        # Sync profile fields with incoming IdP claims
        has_changed = False
        if user.first_name != first_name:
            user.first_name = first_name
            has_changed = True
        if user.last_name != last_name:
            user.last_name = last_name
            has_changed = True
        if has_changed:
            user.save()
            logger.info("OIDC: Synced profile details for user %s", user.username)
    except User.DoesNotExist:
        # Auto-provision user on first successful OIDC login
        from django.core.management.utils import get_random_secret_key
        username_clean = email.split("@")[0]
        # Ensure unique username
        base_username = username_clean
        idx = 1
        while User.objects(username=username_clean).count() > 0:
            username_clean = f"{base_username}_{idx}"
            idx += 1

        user = User(
            username=username_clean,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role="analyst",
            is_active=True,
            date_joined=datetime.datetime.now(datetime.timezone.utc),
        )
        user.set_password(get_random_secret_key())
        user.save()
        logger.info("OIDC Auto-provisioned user: %s (role=analyst)", user.username)
        messages.success(request, f"Welcome to ThreatWatch! Your account has been provisioned via Single Sign-On.")

    # Establish Session
    request.session.cycle_key()
    request.session["_auth_user_id"] = str(user.pk)
    user.last_login = datetime.datetime.now(datetime.timezone.utc)
    user.save()
    
    logger.info("User %s logged in via %s OIDC SSO", user.username, provider.upper())
    return redirect(settings.LOGIN_REDIRECT_URL)


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, user=user)
        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            company_name_str = form.cleaned_data["company_name"].strip()
            user.company_name = company_name_str
            if company_name_str:
                from .models import Organization
                try:
                    org = Organization.objects.get(name=company_name_str)
                except Organization.DoesNotExist:
                    org = Organization(name=company_name_str).save()
                user.organization = org
            else:
                user.organization = None
            user.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(initial={
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "company_name": user.company_name,
        })

    return render(request, "accounts/profile.html", {
        "form": form,
        "profile_user": user,
    })


