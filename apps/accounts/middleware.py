from .models import User


class MongoAuthMiddleware:
    """Attach MongoEngine User to request, replacing Django's AuthenticationMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get("_auth_user_id")
        if user_id:
            try:
                request.user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                request.user = _AnonymousUser()
        else:
            request.user = _AnonymousUser()
        return self.get_response(request)


class _AnonymousUser:
    is_authenticated = False
    is_anonymous = True
    is_active = False
    is_staff = False
    role = "analyst"
    pk = None

    def __str__(self):
        return "AnonymousUser"
