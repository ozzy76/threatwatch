from mongoengine import Document, EmbeddedDocument, fields


class MitreTechniqueRef(EmbeddedDocument):
    """Lightweight reference to a MITRE ATT&CK technique."""
    technique_id = fields.StringField(max_length=20, required=True)  # e.g. "T1059.001"
    name = fields.StringField(max_length=200)
    tactic = fields.StringField(max_length=100)
    url = fields.StringField()


class ThreatActor(Document):
    name = fields.StringField(max_length=200, required=True)
    aliases = fields.ListField(fields.StringField(max_length=200), default=list)
    mitre_group_id = fields.StringField(max_length=20)  # e.g. "G0016"
    description = fields.StringField()
    motivation = fields.StringField(max_length=200)
    origin_country = fields.StringField(max_length=100)
    target_industries = fields.ListField(fields.StringField(max_length=100), default=list)
    target_countries = fields.ListField(fields.StringField(max_length=100), default=list)
    known_techniques = fields.EmbeddedDocumentListField(MitreTechniqueRef, default=list)
    first_seen = fields.DateTimeField(null=True)
    last_seen = fields.DateTimeField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()

    meta = {
        "collection": "threats_threatactor",
        "indexes": ["name", "mitre_group_id", "is_active"],
        "ordering": ["name"],
    }

    def __str__(self):
        return self.name


class Campaign(Document):
    name = fields.StringField(max_length=200, required=True)
    mitre_campaign_id = fields.StringField(max_length=20)  # e.g. "C0001"
    description = fields.StringField()
    start_date = fields.DateTimeField(null=True)
    end_date = fields.DateTimeField(null=True)
    techniques = fields.EmbeddedDocumentListField(MitreTechniqueRef, default=list)
    target_industries = fields.ListField(fields.StringField(max_length=100), default=list)
    target_countries = fields.ListField(fields.StringField(max_length=100), default=list)
    threat_actor = fields.ReferenceField(ThreatActor, null=True)
    sources = fields.ListField(fields.StringField(), default=list)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()

    meta = {
        "collection": "threats_campaign",
        "indexes": ["name", "threat_actor", "mitre_campaign_id"],
        "ordering": ["-start_date"],
    }

    def __str__(self):
        return self.name
