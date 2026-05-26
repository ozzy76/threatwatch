from django import forms
from apps.threats.models import ThreatActor
from .models import FairScenario


class FairScenarioForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "e.g., Ransomware attack on critical customer database"}),
        label="Scenario Name"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Describe the scope and assumptions of this scenario..."}),
        required=False,
        label="Scenario Description"
    )
    asset = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "e.g., Corporate ERP, Payment Gateway, or HR Portal"}),
        label="Asset at Risk"
    )
    third_party_id = forms.ChoiceField(
        required=False,
        label="Linked Third Party / Vendor (Optional)"
    )
    threat_agent_id = forms.ChoiceField(
        required=False,
        label="Threat Community / Actor (MITRE ATT&CK)"
    )
    threat_agent_text = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g., Generic Cybercriminals (Fallback if not listed above)"}),
        label="Threat Agent (Freeform text)"
    )
    threat_effect = forms.ChoiceField(
        choices=FairScenario.THREAT_EFFECTS,
        label="Threat Effect (Impact Type)"
    )
    
    # Authority items
    insurance_premium = forms.FloatField(
        required=False,
        initial=0.0,
        min_value=0.0,
        label="Current Annual Insurance Policy Premium ($)",
        widget=forms.NumberInput(attrs={"step": "100"})
    )
    regulatory_penalty_multiplier = forms.FloatField(
        required=False,
        initial=1.0,
        min_value=0.0,
        label="Regulatory Fine Risk Factor (Multiplier)",
        widget=forms.NumberInput(attrs={"step": "0.1"}),
        help_text="Adjust based on target data severity (e.g. HIPAA, GDPR)."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load threat actors dynamically
        actors = [("", "--- Select Threat Actor ---")]
        try:
            db_actors = ThreatActor.objects(is_active=True).order_by("name")
            for actor in db_actors:
                actors.append((str(actor.id), actor.name))
        except Exception:
            pass
        self.fields["threat_agent_id"].choices = actors

        # Load third parties (formerly customers) dynamically
        from apps.customers.models import ThirdParty
        third_parties = [("", "--- None (Internal Enterprise Risk) ---")]
        try:
            db_customers = ThirdParty.objects(is_active=True).order_by("name")
            for cust in db_customers:
                third_parties.append((str(cust.id), cust.name))
        except Exception:
            pass
        self.fields["third_party_id"].choices = third_parties

        # Add Bootstrap form-control class
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-control bg-dark border-secondary text-white")


class FairCalibrateForm(forms.Form):
    # Threat Event Frequency (TEF) - Events per year
    tef_min = forms.FloatField(min_value=0.0, label="Min TEF (per year)")
    tef_mode = forms.FloatField(min_value=0.0, label="Most Likely TEF (per year)")
    tef_max = forms.FloatField(min_value=0.0, label="Max TEF (per year)")
    tef_rationale = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Rationale: E.g., based on 3 external active threat campaigns and historical phishing attempts..."}),
        label="TEF Evidence & Rationale",
        required=True
    )

    # Vulnerability (Vuln) - Probability 0 to 1
    vuln_min = forms.FloatField(min_value=0.0, max_value=1.0, label="Min Vulnerability (0.0 to 1.0)")
    vuln_mode = forms.FloatField(min_value=0.0, max_value=1.0, label="Most Likely Vulnerability (0.0 to 1.0)")
    vuln_max = forms.FloatField(min_value=0.0, max_value=1.0, label="Max Vulnerability (0.0 to 1.0)")
    vuln_rationale = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Rationale: E.g., based on missing MFA on legacy APIs and active patch lag of 45 days..."}),
        label="Vulnerability Evidence & Rationale",
        required=True
    )

    # Primary Loss Magnitude (PLM) - Dollars
    primary_loss_min = forms.FloatField(min_value=0.0, label="Min Primary Loss ($)")
    primary_loss_mode = forms.FloatField(min_value=0.0, label="Most Likely Primary Loss ($)")
    primary_loss_max = forms.FloatField(min_value=0.0, label="Max Primary Loss ($)")
    primary_loss_rationale = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Rationale: E.g., immediate forensic response hours ($15k) and employee recovery downtime cost ($30k)..."}),
        label="Primary Loss Evidence & Rationale",
        required=True
    )

    # Secondary Loss Event Frequency (SLEF) - Probability 0 to 1
    secondary_loss_freq_min = forms.FloatField(min_value=0.0, max_value=1.0, label="Min Secondary Freq (0.0 to 1.0)")
    secondary_loss_freq_mode = forms.FloatField(min_value=0.0, max_value=1.0, label="Most Likely Secondary Freq (0.0 to 1.0)")
    secondary_loss_freq_max = forms.FloatField(min_value=0.0, max_value=1.0, label="Max Secondary Freq (0.0 to 1.0)")
    secondary_loss_freq_rationale = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Rationale: E.g., likelihood of regulatory probe if customer PII is breached..."}),
        label="Secondary Loss Freq Evidence & Rationale",
        required=True
    )

    # Secondary Loss Magnitude (SLM) - Dollars
    secondary_loss_mag_min = forms.FloatField(min_value=0.0, label="Min Secondary Loss ($)")
    secondary_loss_mag_mode = forms.FloatField(min_value=0.0, label="Most Likely Secondary Loss ($)")
    secondary_loss_mag_max = forms.FloatField(min_value=0.0, label="Max Secondary Loss ($)")
    secondary_loss_mag_rationale = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Rationale: E.g., class-action lawsuit defense and regulatory fines based on similar peer breaches..."}),
        label="Secondary Loss Magnitude Evidence & Rationale",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control bg-dark border-secondary text-white")
            if "rationale" in name:
                field.widget.attrs["class"] += " font-sans"

    def clean(self):
        cleaned_data = super().clean()
        
        # Validation helper for ranges
        def check_range(field_name, min_val, mode_val, max_val):
            if min_val is not None and mode_val is not None and max_val is not None:
                if not (min_val <= mode_val <= max_val):
                    self.add_error(f"{field_name}_mode", f"Most Likely must lie between Min and Max for {field_name.upper()}.")

        check_range("tef", cleaned_data.get("tef_min"), cleaned_data.get("tef_mode"), cleaned_data.get("tef_max"))
        check_range("vuln", cleaned_data.get("vuln_min"), cleaned_data.get("vuln_mode"), cleaned_data.get("vuln_max"))
        check_range("primary_loss", cleaned_data.get("primary_loss_min"), cleaned_data.get("primary_loss_mode"), cleaned_data.get("primary_loss_max"))
        check_range("secondary_loss_freq", cleaned_data.get("secondary_loss_freq_min"), cleaned_data.get("secondary_loss_freq_mode"), cleaned_data.get("secondary_loss_freq_max"))
        check_range("secondary_loss_mag", cleaned_data.get("secondary_loss_mag_min"), cleaned_data.get("secondary_loss_mag_mode"), cleaned_data.get("secondary_loss_mag_max"))

        return cleaned_data
