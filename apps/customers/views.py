import logging
import re as _re
from datetime import datetime, timezone
from mongoengine import ValidationError as MongoValidationError
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponseNotAllowed
from django.utils.text import slugify
from apps.accounts.decorators import login_required, admin_required
from .forms import CustomerForm
from .models import Customer, Breach, IndustryInfo
from apps.threats.models import ThreatActor

# Maps free-form customer industry text to the canonical sector names stored on ThreatActor.
# Each tuple is (regex_pattern, canonical_sector_name).  Multiple patterns can map to the
# same sector; a customer may resolve to multiple sectors (e.g. "Aerospace & Defense" also
# maps to "Defense").
_CUSTOMER_SECTOR_MAP = [
    (r"financ|bank|insurance|invest|capital market", "Financial Services"),
    (r"health|hospital|medical|pharma|biotech|clinical", "Healthcare"),
    (r"government|federal|state|municipal|public sector|public admin", "Government"),
    (r"defense|military|defence", "Defense"),
    (r"aerospace", "Aerospace & Defense"),
    (r"energy|oil|gas|\bpower\b|utilit|nuclear|renewable", "Energy"),
    (r"tech|software|\bit\b|information tech|cyber|cloud|saas|semiconductor", "Technology"),
    (r"telecom|communication|wireless|carrier|\bisp\b", "Telecommunications"),
    (r"education|school|universit|college|academic|research institute", "Education"),
    (r"\bngo\b|nonprofit|non.profit|charity|foundation|think tank|civil society", "Think Tank / NGO"),
    (r"media|broadcast|entertainment|publish|news|journalism", "Media"),
    (r"transport|logistics|shipping|freight|aviation|rail|maritime", "Transportation"),
    (r"manufactur|industrial|production|fabricat|assembly", "Manufacturing"),
    (r"retail|e.commerce|consumer goods|grocery|supermarket", "Retail"),
    (r"critical infrastructure|infrastructure", "Critical Infrastructure"),
    (r"consult|professional services|legal|accounting|audit|human resources|\bhr\b|staffing|managed service", "Professional Services"),
]


def _normalize_customer_sector(sector: str) -> list[str]:
    """Map a free-form customer industry string to one or more canonical sector names."""
    text = (sector or "").lower()
    found = []
    for pattern, canonical in _CUSTOMER_SECTOR_MAP:
        if _re.search(pattern, text) and canonical not in found:
            found.append(canonical)
    return found

logger = logging.getLogger(__name__)


def _allowed_customers(user):
    """Return queryset of all active customers — all authenticated users may browse."""
    return Customer.objects(is_active=True)


def _get_allowed_customer(user, customer_id):
    try:
        return Customer.objects.get(id=customer_id, is_active=True)
    except Customer.DoesNotExist:
        raise Http404


@login_required
def customer_list(request):
    qs = _allowed_customers(request.user)
    breach_filter = request.GET.get("breach", "")
    if breach_filter == "yes":
        qs = qs.filter(has_known_breach=True)
    elif breach_filter == "no":
        qs = qs.filter(has_known_breach=False)
    customers = qs.order_by("name")
    return render(request, "customers/customer_list.html", {
        "customers": customers,
        "breach_filter": breach_filter,
    })


@login_required
def customer_detail(request, customer_id):
    customer = _get_allowed_customer(request.user, customer_id)
    recent_breaches = Breach.objects(customer=customer).order_by("-breach_date")[:5]

    # Likely threat actors (WEP-scored)
    # Normalise the free-form customer industry string to canonical sector names, then query
    # actors whose target_industries list contains ANY of those canonical names.
    likely_actors = []
    canonical_sectors = _normalize_customer_sector(
        customer.industry.sector if customer.industry else ""
    )
    if canonical_sectors:
        country = (customer.hq_country or "").lower()
        matching = ThreatActor.objects(
            target_industries__in=canonical_sectors,
            is_active=True,
        ).order_by("name")
        for actor in matching:
            country_match = bool(country) and any(
                country in t.lower() or t.lower() in country
                for t in actor.target_countries
            )
            wep = "Highly Likely" if country_match else "Likely"
            likely_actors.append({
                "actor": actor,
                "wep": wep,
                "country_match": country_match,
            })
        # Highly Likely first
        likely_actors.sort(key=lambda x: 0 if x["wep"] == "Highly Likely" else 1)

    return render(request, "customers/customer_detail.html", {
        "customer": customer,
        "recent_breaches": recent_breaches,
        "likely_actors": likely_actors,
    })


@login_required
def breach_list(request, customer_id):
    customer = _get_allowed_customer(request.user, customer_id)
    breaches = Breach.objects(customer=customer).order_by("-breach_date")
    return render(request, "customers/breach_list.html", {
        "customer": customer,
        "breaches": breaches,
    })


@login_required
@admin_required
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            now = datetime.now(timezone.utc)
            industry = IndustryInfo(
                sector=d["industry_sector"],
                subsector=d["industry_subsector"],
                naics_code=d["naics_code"],
            )
            contract_dt = None
            if d["contract_exp_date"]:
                contract_dt = datetime.combine(d["contract_exp_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
            customer = Customer(
                name=d["name"],
                short_name=slugify(d["name"])[:50],
                industry=industry,
                hq_country=d["hq_country"] or None,
                employee_count=d["employee_count"],
                description=d["description"] or None,
                contact_name=d["contact_name"] or None,
                contact_email=d["contact_email"],
                website_url=d["website_url"] or None,
                contract_exp_date=contract_dt,
                created_at=now,
                updated_at=now,
            )
            try:
                customer.save()
            except MongoValidationError as exc:
                logger.error("MongoEngine validation error on customer create: %s", exc)
                form.add_error(None, "Could not save customer: %s" % exc)
                return render(request, "customers/customer_form.html", {"form": form, "action": "Create"})
            return redirect("customers:customer_detail", customer_id=str(customer.id))
    else:
        form = CustomerForm()
    return render(request, "customers/customer_form.html", {"form": form, "action": "Create"})


@login_required
@admin_required
def customer_edit(request, customer_id):
    customer = _get_allowed_customer(request.user, customer_id)
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            industry = IndustryInfo(
                sector=d["industry_sector"],
                subsector=d["industry_subsector"],
                naics_code=d["naics_code"],
            )
            contract_dt = None
            if d["contract_exp_date"]:
                contract_dt = datetime.combine(d["contract_exp_date"], datetime.min.time()).replace(tzinfo=timezone.utc)
            customer.name = d["name"]
            customer.short_name = slugify(d["name"])[:50]
            customer.industry = industry
            customer.hq_country = d["hq_country"] or None
            customer.employee_count = d["employee_count"]
            customer.description = d["description"] or None
            customer.contact_name = d["contact_name"] or None
            customer.contact_email = d["contact_email"]
            customer.website_url = d["website_url"] or None
            customer.contract_exp_date = contract_dt
            customer.updated_at = datetime.now(timezone.utc)
            try:
                customer.save()
            except MongoValidationError as exc:
                logger.error("MongoEngine validation error on customer edit %s: %s", customer_id, exc)
                form.add_error(None, "Could not save customer: %s" % exc)
                return render(request, "customers/customer_form.html", {
                    "form": form, "action": "Edit", "customer": customer,
                })
            return redirect("customers:customer_detail", customer_id=str(customer.id))
    else:
        initial = {
            "name": customer.name,
            "industry_sector": customer.industry.sector if customer.industry else "",
            "industry_subsector": customer.industry.subsector if customer.industry else "",
            "naics_code": customer.industry.naics_code if customer.industry else None,
            "hq_country": customer.hq_country,
            "employee_count": customer.employee_count,
            "description": customer.description,
            "contact_name": customer.contact_name,
            "contact_email": customer.contact_email,
            "website_url": customer.website_url,
            "contract_exp_date": customer.contract_exp_date.date() if customer.contract_exp_date else None,
        }
        form = CustomerForm(initial=initial)
    return render(request, "customers/customer_form.html", {
        "form": form,
        "action": "Edit",
        "customer": customer,
    })


@login_required
@admin_required
def customer_delete(request, customer_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    customer = _get_allowed_customer(request.user, customer_id)
    customer.is_active = False
    customer.updated_at = datetime.now(timezone.utc)
    customer.save()
    return redirect("customers:customer_list")
