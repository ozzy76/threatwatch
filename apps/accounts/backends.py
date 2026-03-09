import logging
from .models import User

logger = logging.getLogger(__name__)


class MongoEngineBackend:
    """Custom auth backend using MongoEngine User document."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.warning("Login attempt for unknown user: %s", username)
            return None

        if not user.is_active:
            logger.warning("Login attempt for inactive user: %s", username)
            return None

        if user.check_password(password):
            logger.info("Successful login: %s", username)
            return user

        logger.warning("Failed password check for user: %s", username)
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
