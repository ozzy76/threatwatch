from mongoengine import Document, fields


class Report(Document):
    customer = fields.ReferenceField("customers.Customer", required=True)
    generated_by = fields.ReferenceField("accounts.User", required=True)
    generated_at = fields.DateTimeField(required=True)
    gcs_object_path = fields.StringField(required=True)
    gcs_bucket = fields.StringField(required=True)
    snapshot_data = fields.DictField(default=dict)
    page_count = fields.IntField(null=True)
    file_size_bytes = fields.IntField(null=True)
    is_available = fields.BooleanField(default=True)

    meta = {
        "collection": "reports_report",
        "indexes": ["customer", "generated_by", "generated_at"],
        "ordering": ["-generated_at"],
    }

    def __str__(self):
        return f"Report for {self.customer} at {self.generated_at:%Y-%m-%d %H:%M}"
