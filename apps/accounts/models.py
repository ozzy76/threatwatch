from mongoengine import Document, fields
from django.contrib.auth.hashers import make_password, check_password as django_check_password

ROLE_ANALYST = "analyst"
ROLE_ADMIN   = "admin"
ROLE_CHOICES = (ROLE_ANALYST, ROLE_ADMIN)


class User(Document):
    username = fields.StringField(max_length=150, unique=True, required=True)
    email = fields.EmailField(unique=True, required=True)
    password = fields.StringField(required=True)
    first_name = fields.StringField(max_length=150, default="")
    last_name = fields.StringField(max_length=150, default="")
    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=False)
    role = fields.StringField(choices=ROLE_CHOICES, default=ROLE_ANALYST, required=True)
    date_joined = fields.DateTimeField()
    last_login = fields.DateTimeField(null=True)
    allowed_customer_ids = fields.ListField(fields.ObjectIdField(), default=list)

    meta = {
        "collection": "accounts_user",
        "indexes": ["username", "email"],
    }

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)

    @property
    def pk(self):
        return str(self.id)

    def __str__(self):
        return self.username

    # Minimal interface expected by Django session/message framework
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
