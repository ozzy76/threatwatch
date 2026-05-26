from mongoengine import Document, EmbeddedDocument, fields


class IndustryInfo(EmbeddedDocument):
    sector = fields.StringField(max_length=100)
    subsector = fields.StringField(max_length=100, default="")
    naics_code = fields.IntField(null=True)


class ThirdParty(Document):
    name = fields.StringField(max_length=200, required=True)
    short_name = fields.StringField(max_length=50, required=True)
    industry = fields.EmbeddedDocumentField(IndustryInfo)
    hq_country = fields.StringField(max_length=100)
    employee_count = fields.IntField(min_value=0, null=True)
    description = fields.StringField()
    contact_name = fields.StringField(max_length=200)
    contact_email = fields.EmailField()
    website_url = fields.StringField(max_length=500)
    contract_exp_date = fields.DateTimeField(null=True)
    has_known_breach = fields.BooleanField(default=False)
    breach_source_refs = fields.ListField(fields.StringField(), default=list)
    associated_threat_actor_ids = fields.ListField(fields.ObjectIdField(), default=list)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()

    meta = {
        "collection": "customers_customer",
        "indexes": ["name", "short_name", "is_active"],
        "ordering": ["name"],
    }

    def __str__(self):
        return self.name


class Breach(Document):
    third_party = fields.ReferenceField(ThirdParty, required=True)
    breach_date = fields.DateTimeField(required=True)
    discovered_date = fields.DateTimeField(null=True)
    description = fields.StringField()
    data_types_compromised = fields.ListField(fields.StringField(), default=list)
    attributed_actor = fields.ObjectIdField(null=True)
    severity = fields.StringField(
        choices=["critical", "high", "medium", "low"],
        default="medium",
    )
    source_references = fields.ListField(fields.StringField(), default=list)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()

    meta = {
        "collection": "customers_breach",
        "indexes": ["third_party", "breach_date", "severity"],
        "ordering": ["-breach_date"],
    }

    def __str__(self):
        return f"Breach @ {self.third_party} on {self.breach_date:%Y-%m-%d}"
