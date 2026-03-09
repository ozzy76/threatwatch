from django import forms


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
