import unicodedata
from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class CustomerForm(forms.Form):
    name               = forms.CharField(max_length=200)
    industry_sector    = forms.CharField(max_length=100, required=False, label="Industry Sector")
    industry_subsector = forms.CharField(max_length=100, required=False, label="Subsector")
    naics_code         = forms.IntegerField(required=False, label="NAICS Code")
    hq_country         = forms.CharField(max_length=100, required=False, label="HQ Country")
    employee_count     = forms.IntegerField(required=False, min_value=0, label="Employee Count")
    description        = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)
    contact_name       = forms.CharField(max_length=200, required=False, label="Contact Name")
    contact_email      = forms.EmailField(required=False, label="Contact Email")
    website_url        = forms.URLField(required=False, label="Website URL", max_length=500)
    contract_exp_date  = forms.DateField(
        required=False,
        label="Contract Expiry Date",
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    # ------------------------------------------------------------------
    # Per-field cleaning
    # ------------------------------------------------------------------

    def _normalize_text(self, value):
        """NFC-normalize and strip control characters from a string."""
        if not value:
            return value
        value = unicodedata.normalize("NFC", value)
        # Remove ASCII control characters (0x00–0x1F, 0x7F) except newline/tab
        value = "".join(
            ch for ch in value if unicodedata.category(ch) != "Cc" or ch in "\n\t"
        )
        return value.strip()

    def clean_name(self):
        value = self._normalize_text(self.cleaned_data.get("name", ""))
        if not slugify(value):
            raise ValidationError(
                "Name must contain at least one letter or digit so a URL-safe "
                "identifier can be generated."
            )
        return value

    def clean_industry_sector(self):
        return self._normalize_text(self.cleaned_data.get("industry_sector", ""))

    def clean_industry_subsector(self):
        return self._normalize_text(self.cleaned_data.get("industry_subsector", ""))

    def clean_naics_code(self):
        value = self.cleaned_data.get("naics_code")
        if value is None:
            return value
        # NAICS codes are 2–6 digit integers (range 11–999999)
        if not (11 <= value <= 999999):
            raise ValidationError("NAICS code must be between 11 and 999999.")
        return value

    def clean_hq_country(self):
        return self._normalize_text(self.cleaned_data.get("hq_country", ""))

    def clean_description(self):
        return self._normalize_text(self.cleaned_data.get("description", ""))

    def clean_contact_name(self):
        return self._normalize_text(self.cleaned_data.get("contact_name", ""))

    def clean_contact_email(self):
        """Return None for blank input so MongoEngine's EmailField skips validation."""
        value = self.cleaned_data.get("contact_email", "")
        if not value:
            return None
        return value.strip().lower()

    def clean_website_url(self):
        """Restrict website URLs to http:// and https:// schemes only."""
        value = self.cleaned_data.get("website_url", "")
        if not value:
            return value
        scheme = value.split("://", 1)[0].lower()
        if scheme not in ("http", "https"):
            raise ValidationError(
                "Only http:// and https:// URLs are accepted."
            )
        return value
