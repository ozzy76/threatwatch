import logging
import re as _re
from datetime import datetime, timezone
from mongoengine import ValidationError as MongoValidationError
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponseNotAllowed
from django.utils.text import slugify
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from apps.accounts.decorators import login_required, admin_required
from apps.accounts.models import Organization, ROLE_ADMIN, ROLE_ANALYST
from .forms import ThirdPartyForm, ThirdPartyCSVUploadForm
from .models import ThirdParty, Breach, IndustryInfo
from apps.threats.models import ThreatActor

# Maps free-form third-party industry text to the canonical sector names stored on ThreatActor.
# Each tuple is (regex_pattern, canonical_sector_name).  Multiple patterns can map to the
# same sector; a third party may resolve to multiple sectors (e.g. "Aerospace & Defense" also
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


def _normalize_third_party_sector(sector: str) -> list[str]:
    """Map a free-form third-party industry string to one or more canonical sector names."""
    text = (sector or "").lower()
    found = []
    for pattern, canonical in _CUSTOMER_SECTOR_MAP:
        if _re.search(pattern, text) and canonical not in found:
            found.append(canonical)
    return found


logger = logging.getLogger(__name__)


from bson import ObjectId

def _allowed_third_parties(user):
    """
    Returns a queryset of active third parties the user is authorized to view.
    Platform admins can view all active third parties.
    Analysts can only view third parties in their effective allowed list (user + organization).
    """
    if not user or not user.is_authenticated:
        return ThirdParty.objects.none()

    if getattr(user, "role", None) == "admin":
        return ThirdParty.objects(is_active=True)

    allowed_ids = user.effective_allowed_third_party_ids
    return ThirdParty.objects(id__in=allowed_ids, is_active=True)


def _get_allowed_third_party(user, third_party_id):
    """
    Fetches a specific third-party organization, strictly enforcing tenant boundaries.
    Raises Http404 if the organization does not exist or the user is unauthorized.
    """
    if not user or not user.is_authenticated:
        raise Http404("Unauthorized")

    try:
        obj_id = ObjectId(third_party_id)
    except Exception:
        raise Http404("Invalid ID format")

    if getattr(user, "role", None) == "admin":
        try:
            return ThirdParty.objects.get(id=obj_id, is_active=True)
        except ThirdParty.DoesNotExist:
            raise Http404("Not Found")

    # Standard analyst check
    allowed_ids = user.effective_allowed_third_party_ids
    if obj_id not in allowed_ids:
        raise Http404("Access Denied")

    try:
        return ThirdParty.objects.get(id=obj_id, is_active=True)
    except ThirdParty.DoesNotExist:
        raise Http404("Not Found")


@login_required
def third_party_list(request):
    qs = _allowed_third_parties(request.user)
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
def third_party_detail(request, third_party_id):
    customer = _get_allowed_third_party(request.user, third_party_id)
    recent_breaches = Breach.objects(third_party=customer).order_by("-breach_date")[:5]

    # Likely threat actors (WEP-scored)
    # Normalise the free-form industry string to canonical sector names, then query
    # actors whose target_industries list contains ANY of those canonical names.
    likely_actors = []
    canonical_sectors = _normalize_third_party_sector(
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
def breach_list(request, third_party_id):
    customer = _get_allowed_third_party(request.user, third_party_id)
    breaches = Breach.objects(third_party=customer).order_by("-breach_date")
    return render(request, "customers/breach_list.html", {
        "customer": customer,
        "breaches": breaches,
    })


@login_required
def third_party_create(request):
    user = request.user
    
    # Enforce that standard analysts MUST belong to an organization to create third parties
    if getattr(user, "role", None) != ROLE_ADMIN and not getattr(user, "organization", None):
        messages.warning(
            request,
            "An organization association is required to manage third parties. Please update your profile with your Company Name. Instructions: Click on your profile name in the top right, enter a company name, and click save."
        )
        return redirect("accounts:profile")

    if request.method == "POST":
        form = ThirdPartyForm(request.POST)
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
            customer = ThirdParty(
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
                is_active=True
            )
            try:
                customer.save()
            except MongoValidationError as exc:
                logger.error("MongoEngine validation error on third party create: %s", exc)
                form.add_error(None, "Could not save third party: %s" % exc)
                return render(request, "customers/customer_form.html", {"form": form, "action": "Create"})
            
            # Tenant association logic
            if getattr(user, "role", None) == ROLE_ADMIN:
                target_org_id = request.POST.get("organization_id")
                if target_org_id:
                    try:
                        org = Organization.objects.get(id=ObjectId(target_org_id))
                        org.third_parties.append(customer)
                        org.save()
                    except (Organization.DoesNotExist, Exception):
                        logger.warning("Admin specified an invalid organization ID %s during creation", target_org_id)
            else:
                org = user.organization
                org.reload()
                org.third_parties.append(customer)
                org.save()
                
            return redirect("customers:customer_detail", third_party_id=str(customer.id))
    else:
        form = ThirdPartyForm()
    return render(request, "customers/customer_form.html", {
        "form": form, 
        "action": "Create",
        "organizations": Organization.objects.all() if getattr(user, "role", None) == ROLE_ADMIN else None
    })


@login_required
def third_party_edit(request, third_party_id):
    customer = _get_allowed_third_party(request.user, third_party_id)
    if request.method == "POST":
        form = ThirdPartyForm(request.POST)
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
                logger.error("MongoEngine validation error on third party edit %s: %s", third_party_id, exc)
                form.add_error(None, "Could not save third party: %s" % exc)
                return render(request, "customers/customer_form.html", {
                    "form": form, "action": "Edit", "customer": customer,
                })
            return redirect("customers:customer_detail", third_party_id=str(customer.id))
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
        form = ThirdPartyForm(initial=initial)
    return render(request, "customers/customer_form.html", {
        "form": form,
        "action": "Edit",
        "customer": customer,
    })


@login_required
def third_party_delete(request, third_party_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    customer = _get_allowed_third_party(request.user, third_party_id)
    customer.is_active = False
    customer.updated_at = datetime.now(timezone.utc)
    customer.save()
    return redirect("customers:customer_list")


import csv
import io

@login_required
@require_http_methods(["GET", "POST"])
def third_party_csv_upload(request):
    user = request.user
    if getattr(user, "role", None) != ROLE_ADMIN and not getattr(user, "organization", None):
        messages.warning(
            request,
            "An organization association is required to manage third parties. Please update your profile with your Company Name. Instructions: Click on your profile name in the top right, enter a company name, and click save."
        )
        return redirect("accounts:profile")

    if request.method == "POST":
        form = ThirdPartyCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["csv_file"]
            try:
                decoded_file = csv_file.read().decode("utf-8-sig").splitlines()
            except Exception:
                messages.error(request, "Failed to decode the CSV file. Please ensure it is saved in UTF-8 format.")
                return render(request, "customers/csv_upload.html", {"form": form})

            reader = csv.DictReader(decoded_file)
            required_cols = {"Name", "Website URL"}
            if not reader.fieldnames or not required_cols.issubset(set(reader.fieldnames)):
                messages.error(request, "Invalid CSV format. Missing mandatory columns: 'Name' and 'Website URL'.")
                return render(request, "customers/csv_upload.html", {"form": form})

            success_count = 0
            fail_count = 0
            errors = []
            now = datetime.now(timezone.utc)
            org = getattr(user, "organization", None)

            for idx, row in enumerate(reader, start=2):
                name = (row.get("Name") or "").strip()
                website_url = (row.get("Website URL") or "").strip()

                if not name:
                    errors.append(f"Row {idx}: 'Name' is empty.")
                    fail_count += 1
                    continue

                if website_url:
                    scheme = website_url.split("://", 1)[0].lower()
                    if scheme not in ("http", "https"):
                        errors.append(f"Row {idx}: Website URL must start with http:// or https://")
                        fail_count += 1
                        continue

                # Check for duplicates within user's visible ecosystem
                allowed_qs = _allowed_third_parties(user)
                if allowed_qs.filter(name__iexact=name).first():
                    errors.append(f"Row {idx}: Third Party with name '{name}' already exists in your workspace.")
                    fail_count += 1
                    continue

                try:
                    industry = IndustryInfo(sector="", subsector="", naics_code=None)
                    customer = ThirdParty(
                        name=name,
                        short_name=slugify(name)[:50],
                        website_url=website_url or None,
                        industry=industry,
                        is_active=True,
                        created_at=now,
                        updated_at=now
                    )
                    customer.save()

                    if getattr(user, "role", None) == ROLE_ADMIN:
                        target_org_id = request.POST.get("organization_id")
                        if target_org_id:
                            try:
                                target_org = Organization.objects.get(id=ObjectId(target_org_id))
                                target_org.third_parties.append(customer)
                                target_org.save()
                            except Exception:
                                pass
                    else:
                        if org:
                            org.reload()
                            org.third_parties.append(customer)
                            org.save()

                    success_count += 1
                except Exception as exc:
                    errors.append(f"Row {idx}: Database error: {str(exc)}")
                    fail_count += 1

            if success_count > 0:
                messages.success(request, f"Successfully uploaded and active-provisioned {success_count} third parties.")
            if fail_count > 0:
                messages.warning(request, f"Failed to upload {fail_count} rows due to validation or duplicate constraints.")

            return render(request, "customers/csv_upload.html", {
                "form": form,
                "errors": errors,
                "success_count": success_count,
                "fail_count": fail_count,
                "organizations": Organization.objects.all() if getattr(user, "role", None) == ROLE_ADMIN else None
            })
    else:
        form = ThirdPartyCSVUploadForm()

    return render(request, "customers/csv_upload.html", {
        "form": form,
        "organizations": Organization.objects.all() if getattr(user, "role", None) == ROLE_ADMIN else None
    })
