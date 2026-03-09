import logging
from datetime import datetime, timezone
from bson import ObjectId
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponseNotAllowed
from django.utils.text import slugify
from apps.accounts.decorators import login_required, admin_required
from apps.accounts.models import ROLE_ADMIN
from .forms import CustomerForm
from .models import Customer, Breach, IndustryInfo

logger = logging.getLogger(__name__)


def _allowed_customers(user):
    """Return queryset filtered to user's role/allowed_customer_ids."""
    if getattr(user, "role", None) == ROLE_ADMIN:
        return Customer.objects(is_active=True)
    ids = [ObjectId(i) for i in user.allowed_customer_ids]
    return Customer.objects(id__in=ids, is_active=True)


def _get_allowed_customer(user, customer_id):
    if getattr(user, "role", None) == ROLE_ADMIN:
        try:
            return Customer.objects.get(id=customer_id, is_active=True)
        except Customer.DoesNotExist:
            raise Http404
    allowed_ids = [str(i) for i in user.allowed_customer_ids]
    if customer_id not in allowed_ids:
        raise Http404
    try:
        return Customer.objects.get(id=customer_id, is_active=True)
    except Customer.DoesNotExist:
        raise Http404


@login_required
def customer_list(request):
    customers = _allowed_customers(request.user).order_by("name")
    return render(request, "customers/customer_list.html", {"customers": customers})


@login_required
def customer_detail(request, customer_id):
    customer = _get_allowed_customer(request.user, customer_id)
    recent_breaches = Breach.objects(customer=customer).order_by("-breach_date")[:5]
    return render(request, "customers/customer_detail.html", {
        "customer": customer,
        "recent_breaches": recent_breaches,
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
                hq_country=d["hq_country"],
                employee_count=d["employee_count"],
                description=d["description"],
                contact_name=d["contact_name"],
                contact_email=d["contact_email"],
                website_url=d["website_url"],
                contract_exp_date=contract_dt,
                created_at=now,
                updated_at=now,
            )
            customer.save()
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
            customer.hq_country = d["hq_country"]
            customer.employee_count = d["employee_count"]
            customer.description = d["description"]
            customer.contact_name = d["contact_name"]
            customer.contact_email = d["contact_email"]
            customer.website_url = d["website_url"]
            customer.contract_exp_date = contract_dt
            customer.updated_at = datetime.now(timezone.utc)
            customer.save()
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
