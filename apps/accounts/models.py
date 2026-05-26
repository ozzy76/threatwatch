import datetime
from mongoengine import Document, fields
from django.contrib.auth.hashers import make_password, check_password as django_check_password

ROLE_ANALYST = "analyst"
ROLE_ADMIN   = "admin"
ROLE_CHOICES = (ROLE_ANALYST, ROLE_ADMIN)


class Organization(Document):
    """Represents a corporate/enterprise entity containing multiple ThirdParty clients."""
    name = fields.StringField(max_length=200, required=True, unique=True)
    third_parties = fields.ListField(fields.ReferenceField('ThirdParty'), default=list)
    created_at = fields.DateTimeField(default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = fields.DateTimeField(default=lambda: datetime.datetime.now(datetime.timezone.utc))

    meta = {
        "collection": "accounts_organization",
        "indexes": ["name"],
        "ordering": ["name"],
    }

    def __str__(self):
        return self.name


class User(Document):
    username = fields.StringField(max_length=150, unique=True, required=True)
    email = fields.EmailField(unique=True, required=True)
    password = fields.StringField(required=True)
    first_name = fields.StringField(max_length=150, default="")
    last_name = fields.StringField(max_length=150, default="")
    company_name = fields.StringField(max_length=200, default="")
    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=False)
    role = fields.StringField(choices=ROLE_CHOICES, default=ROLE_ANALYST, required=True)
    date_joined = fields.DateTimeField()
    last_login = fields.DateTimeField(null=True)
    allowed_third_party_ids = fields.ListField(fields.ObjectIdField(), default=list)
    organization = fields.ReferenceField(Organization, null=True)

    meta = {
        "collection": "accounts_user",
        "indexes": ["username", "email"],
        "strict": False,
    }

    def __init__(self, *args, **values):
        legacy_ids = values.pop("allowed_customer_ids", None)
        super().__init__(*args, **values)
        if legacy_ids is not None and not self.allowed_third_party_ids:
            self.allowed_third_party_ids = legacy_ids

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

    @property
    def effective_allowed_third_party_ids(self):
        """
        Dynamically returns the union of user-specific allowed third parties 
        and any third parties associated with their affiliated Organization.
        """
        allowed_set = set(self.allowed_third_party_ids or [])
        if self.organization and self.organization.third_parties:
            for tp in self.organization.third_parties:
                if tp:
                    allowed_set.add(tp.id)
        return list(allowed_set)
