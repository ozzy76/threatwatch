from mongoengine import Document, fields


class Detection(Document):
    title = fields.StringField(max_length=300, required=True)
    description = fields.StringField()
    technique_ids = fields.ListField(fields.StringField(max_length=20), default=list)
    platform = fields.StringField(max_length=100)
    data_source = fields.StringField(max_length=200)
    detection_logic = fields.StringField()
    severity = fields.StringField(
        choices=["critical", "high", "medium", "low"],
        default="medium",
    )
    priority = fields.IntField(min_value=1, max_value=100, default=50)
    tags = fields.ListField(fields.StringField(max_length=100), default=list)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()

    meta = {
        "collection": "detections_detection",
        "indexes": ["technique_ids", "severity", "priority"],
        "ordering": ["-priority"],
    }

    def __str__(self):
        return self.title
