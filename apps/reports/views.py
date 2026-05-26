import datetime
import logging
from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from apps.accounts.decorators import login_required
from apps.accounts.models import ROLE_ADMIN
from apps.customers.views import _get_allowed_third_party
from .models import Report
from .generator import build_report_context, generate_pdf
from .storage import upload_pdf, generate_signed_url

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def generate_report(request, third_party_id):
    customer = _get_allowed_third_party(request.user, third_party_id)
    try:
        context = build_report_context(customer, request.user)
        pdf_bytes = generate_pdf(context)

        # Create a placeholder Report doc to get an ID for the filename
        report = Report(
            third_party=customer,
            generated_by=request.user,
            generated_at=datetime.datetime.now(datetime.timezone.utc),
            gcs_object_path="pending",
            gcs_bucket="pending",
            snapshot_data={
                "customer_name": customer.name,
                "actor_count": len(context["actors"]),
                "breach_count": len(context["breaches"]),
                "detection_count": len(context["detections"]),
            },
            file_size_bytes=len(pdf_bytes),
            is_available=False,
        )
        report.save()

        bucket_name, object_path = upload_pdf(pdf_bytes, str(customer.id), str(report.id))
        report.gcs_object_path = object_path
        report.gcs_bucket = bucket_name
        report.is_available = True
        report.save()

        logger.info("Report %s generated for third party %s by %s", report.id, customer.id, request.user.username)
        messages.success(request, "Threat profile report generated successfully.")
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)
        messages.error(request, "Report generation failed. Please try again.")

    return redirect("reports:report_history", third_party_id=str(customer.id))


@login_required
def report_history(request, third_party_id):
    customer = _get_allowed_third_party(request.user, third_party_id)
    reports = Report.objects(third_party=customer, is_available=True).order_by("-generated_at")
    return render(request, "reports/report_history.html", {
        "customer": customer,
        "reports": reports,
    })


@login_required
def download_report(request, report_id):
    try:
        report = Report.objects.get(id=report_id, is_available=True)
    except Report.DoesNotExist:
        raise Http404

    # Enforce access control
    if getattr(request.user, "role", None) != ROLE_ADMIN:
        allowed_ids = [str(i) for i in request.user.effective_allowed_third_party_ids]
        if str(report.third_party.id) not in allowed_ids:
            raise Http404

    try:
        url = generate_signed_url(report.gcs_bucket, report.gcs_object_path)
        return redirect(url)
    except Exception as exc:
        logger.error("Signed URL generation failed for report %s: %s", report_id, exc)
        messages.error(request, "Download is temporarily unavailable. Please try again.")
        return redirect("reports:report_history", third_party_id=str(report.third_party.id))
