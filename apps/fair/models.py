from mongoengine import Document, fields


class FairScenario(Document):
    """
    Represents a scoped Quantified Risk Scenario matching the FAIR taxonomy.
    """
    THREAT_EFFECTS = (
        ("disclosure", "Confidentiality / Disclosure"),
        ("modification", "Integrity / Modification"),
        ("destruction", "Destruction"),
        ("interruption", "Availability / Interruption"),
    )

    third_party = fields.ReferenceField("customers.ThirdParty", null=True, required=False)
    name = fields.StringField(max_length=200, required=True)
    description = fields.StringField()
    asset = fields.StringField(max_length=200, required=True)
    threat_agent = fields.ReferenceField("threats.ThreatActor", null=True)
    threat_agent_text = fields.StringField(max_length=200, default="")
    threat_effect = fields.StringField(choices=THREAT_EFFECTS, required=True)
    
    # Authority factors (trends in insurance premiums and regulatory penalties)
    insurance_premium = fields.FloatField(default=0.0)
    regulatory_penalty_multiplier = fields.FloatField(default=1.0)
    
    created_by = fields.ReferenceField("accounts.User", required=True)
    created_at = fields.DateTimeField(required=True)
    updated_at = fields.DateTimeField(required=True)
    is_active = fields.BooleanField(default=True)

    meta = {
        "collection": "fair_scenario",
        "indexes": ["third_party", "is_active"],
        "ordering": ["-updated_at"],
    }

    def __str__(self):
        return f"{self.name} ({self.asset} - {self.threat_effect})"


class FairAnalysisRun(Document):
    """
    Saves an execution run of the Monte Carlo simulation engine with calibrated inputs and rationale.
    """
    scenario = fields.ReferenceField(FairScenario, required=True)
    run_by = fields.ReferenceField("accounts.User", required=True)
    created_at = fields.DateTimeField(required=True)
    
    # Guided data collection notes/evidence
    rationale = fields.DictField(default=dict)

    # Calibrated Ranges (Min, Mode, Max)
    tef_min = fields.FloatField(required=True)
    tef_mode = fields.FloatField(required=True)
    tef_max = fields.FloatField(required=True)

    vuln_min = fields.FloatField(required=True)
    vuln_mode = fields.FloatField(required=True)
    vuln_max = fields.FloatField(required=True)

    primary_loss_min = fields.FloatField(required=True)
    primary_loss_mode = fields.FloatField(required=True)
    primary_loss_max = fields.FloatField(required=True)

    secondary_loss_freq_min = fields.FloatField(required=True)
    secondary_loss_freq_mode = fields.FloatField(required=True)
    secondary_loss_freq_max = fields.FloatField(required=True)

    secondary_loss_mag_min = fields.FloatField(required=True)
    secondary_loss_mag_mode = fields.FloatField(required=True)
    secondary_loss_mag_max = fields.FloatField(required=True)

    # Simulation outcome metrics
    min_ale = fields.FloatField(default=0.0)
    max_ale = fields.FloatField(default=0.0)
    avg_ale = fields.FloatField(default=0.0)
    median_ale = fields.FloatField(default=0.0)
    var_95 = fields.FloatField(default=0.0)
    
    # Store exceedance curves as percentage odds
    loss_exceedance_curve = fields.DictField(default=dict)
    
    # Safeguard planning results
    safeguard_recommendations = fields.ListField(fields.DictField(), default=list)
    is_active = fields.BooleanField(default=True)

    meta = {
        "collection": "fair_analysis_run",
        "indexes": ["scenario", "is_active", "created_at"],
        "ordering": ["-created_at"],
    }

    def __str__(self):
        return f"Run of {self.scenario.name} at {self.created_at:%Y-%m-%d %H:%M}"
